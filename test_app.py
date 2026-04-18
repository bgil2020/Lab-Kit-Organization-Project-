"""
test_app.py  —  Automated Unit Tests for Lab Kit Organization System
====================================================================
Automated test cases selected from the project RTM:

  TC-SR3  SR-3  Student confirms kit completion (checkout request)
  TC-AR4  AR-4  Admin monitors inventory — return updates kit count
  TC-FR1  FR-1  System has data on each kit (database seeded correctly)

Framework: Python unittest + Flask built-in test client
No browser required — runs entirely in-memory against a temp database.

How to run:
  1. Activate virtual environment:   venv\\Scripts\\activate
  2. Install pytest if needed:       pip install pytest
  3. Run:                            pytest test_app.py -v

Expected output:
  3 passed in X.XXs

CI/CD Note:
  Commit this file to the repo. It will be part of the CI/CD pipeline
  during final project code submission at the end of the semester.
"""

import os
import sys
import pytest
import sqlite3
import tempfile
from werkzeug.security import generate_password_hash

# Import Flask app from project root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import app as flask_app


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    Spins up a clean temp SQLite database for each test.
    Seeds one student user and two lab kits.
    Tears down after each test automatically.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    flask_app.app.config["TESTING"]    = True
    flask_app.app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.DATABASE = db_path

    # Initialize schema
    conn = sqlite3.connect(db_path)
    schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # Seed test user (Student)
    conn.execute(
        """INSERT INTO users (username, password_hash, email, first_name, last_name, role)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("testuser", generate_password_hash("testpass123"),
         "test@fau.edu", "Test", "Student", "Student")
    )

    # Seed two lab kits
    conn.execute(
        "INSERT INTO lab_kits (kit_name, description, status) VALUES (?, ?, ?)",
        ("EEL3111 Circuit Kit", "Basic circuits kit", "Available")
    )
    conn.execute(
        "INSERT INTO lab_kits (kit_name, description, status) VALUES (?, ?, ?)",
        ("CDA3101 Logic Kit", "Digital logic kit", "Available")
    )

    # Seed components so parts list is populated
    conn.execute(
        """INSERT INTO kit_components (kit_id, component_name, quantity, condition)
           VALUES (1, 'Resistor Pack', 10, 'Good')"""
    )
    conn.execute(
        """INSERT INTO kit_components (kit_id, component_name, quantity, condition)
           VALUES (1, 'Breadboard', 2, 'Good')"""
    )
    conn.commit()
    conn.close()

    with flask_app.app.test_client() as client:
        yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


# ── Helper ─────────────────────────────────────────────────────────────────────

def login(client, username="testuser", password="testpass123"):
    """Log in via the Flask test client."""
    return client.post("/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)


# ── TC-SR3 | SR-3 — Student Confirms Kit Completion ───────────────────────────

def test_TC_SR3_student_confirms_kit_checkout(client):
    """
    TC-SR3 | Requirement SR-3
    Requirement:  Students confirm kit completion
    Feature:      Confirmation button (checkout request form)
    Input:        Logged-in student submits checkout for an available kit
    Expected:     Checkout record created in DB with status Pending,
                  kit status updated to Checked Out
    Postcondition: Lab manager/admin can see request in dashboard
    """
    login(client)

    db_path = flask_app.DATABASE
    conn = sqlite3.connect(db_path)
    kit = conn.execute(
        "SELECT kit_id FROM lab_kits WHERE kit_name = 'EEL3111 Circuit Kit'"
    ).fetchone()
    conn.close()

    assert kit is not None, "TC-SR3 FAIL: Test kit not found in database"
    kit_id = kit[0]

    # Student submits checkout (confirms kit)
    response = client.post(f"/checkout/{kit_id}", follow_redirects=True)
    assert response.status_code == 200, \
        f"TC-SR3 FAIL: Expected HTTP 200, got {response.status_code}"

    # Verify checkout record was created
    conn = sqlite3.connect(db_path)
    checkout = conn.execute(
        "SELECT status FROM checkouts WHERE kit_id = ?", (kit_id,)
    ).fetchone()
    kit_row = conn.execute(
        "SELECT status FROM lab_kits WHERE kit_id = ?", (kit_id,)
    ).fetchone()
    conn.close()

    assert checkout is not None, \
        "TC-SR3 FAIL: No checkout record created in database"
    assert kit_row[0] == "Checked Out", \
        f"TC-SR3 FAIL: Kit status expected 'Checked Out', got '{kit_row[0]}'"

    print("\n  TC-SR3 PASS: Student checkout confirmed, kit status = 'Checked Out'")


# ── TC-AR4 | AR-4 — Admin Monitors Inventory After Return ─────────────────────

def test_TC_AR4_inventory_updates_on_return(client):
    """
    TC-AR4 | Requirement AR-4
    Requirement:  Admin can monitor inventory
    Feature:      Tracking inventory
    Input:        Active checkout is returned by student
    Expected:     Kit status returns to Available (inventory count recovers)
    Postcondition: Admin dashboard stat card reflects updated available count
    """
    login(client)

    db_path = flask_app.DATABASE
    conn = sqlite3.connect(db_path)
    kit = conn.execute(
        "SELECT kit_id FROM lab_kits WHERE kit_name = 'CDA3101 Logic Kit'"
    ).fetchone()
    user = conn.execute(
        "SELECT user_id FROM users WHERE username = 'testuser'"
    ).fetchone()
    kit_id, user_id = kit[0], user[0]

    # Simulate an active checkout already in the system
    conn.execute(
        """INSERT INTO checkouts (kit_id, student_id, checkout_date, status)
           VALUES (?, ?, date('now'), 'Active')""",
        (kit_id, user_id)
    )
    conn.execute(
        "UPDATE lab_kits SET status = 'Checked Out' WHERE kit_id = ?", (kit_id,)
    )
    conn.commit()

    checkout = conn.execute(
        "SELECT checkout_id FROM checkouts WHERE kit_id = ? AND student_id = ?",
        (kit_id, user_id)
    ).fetchone()
    conn.close()
    checkout_id = checkout[0]

    # Student returns the kit
    response = client.post(f"/return/{checkout_id}", follow_redirects=True)
    assert response.status_code == 200, \
        f"TC-AR4 FAIL: Expected HTTP 200, got {response.status_code}"

    # Verify inventory is updated (kit back to Available)
    conn = sqlite3.connect(db_path)
    kit_status = conn.execute(
        "SELECT status FROM lab_kits WHERE kit_id = ?", (kit_id,)
    ).fetchone()
    checkout_status = conn.execute(
        "SELECT status FROM checkouts WHERE checkout_id = ?", (checkout_id,)
    ).fetchone()
    conn.close()

    assert kit_status[0] == "Available", \
        f"TC-AR4 FAIL: Kit status expected 'Available', got '{kit_status[0]}'"
    assert checkout_status[0] == "Returned", \
        f"TC-AR4 FAIL: Checkout status expected 'Returned', got '{checkout_status[0]}'"

    print("\n  TC-AR4 PASS: Kit returned, inventory updated — status = 'Available'")


# ── TC-FR1 | FR-1 — System Has Data on Each Kit ───────────────────────────────

def test_TC_FR1_database_contains_kit_data(client):
    """
    TC-FR1 | Requirement FR-1
    Requirement:  System has data on each kit
    Feature:      SQLite Database
    Input:        Application started with seeded database
    Expected:     /kits route returns HTTP 200 with kit names visible,
                  kit_components table has records linked to kits
    Postcondition: Parts list is queryable and displayable by Flask
    """
    login(client)

    # Kits page should load and contain seeded kit names
    response = client.get("/kits", follow_redirects=True)
    assert response.status_code == 200, \
        f"TC-FR1 FAIL: Expected HTTP 200 on /kits, got {response.status_code}"

    assert b"EEL3111 Circuit Kit" in response.data, \
        "TC-FR1 FAIL: Seeded kit name not found in /kits response"
    assert b"CDA3101 Logic Kit" in response.data, \
        "TC-FR1 FAIL: Second seeded kit not found in /kits response"

    # Verify components are also stored and linked
    db_path = flask_app.DATABASE
    conn = sqlite3.connect(db_path)
    components = conn.execute(
        "SELECT * FROM kit_components WHERE kit_id = 1"
    ).fetchall()
    conn.close()

    assert len(components) >= 2, \
        f"TC-FR1 FAIL: Expected at least 2 components for kit 1, found {len(components)}"

    print(f"\n  TC-FR1 PASS: Database contains kit data — {len(components)} components found for kit 1")
