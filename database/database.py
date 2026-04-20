"""
database.py — Flask-SQLite integration for Lab Kit Organization System

Usage in your Flask app:
    from database import get_db, close_db, init_db
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
"""

import sqlite3
import os
from flask import g

# Path to the SQLite database file (sits next to this file)
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, 'labkit.db')
SCHEMA    = os.path.join(BASE_DIR, 'schema.sql')
SEED      = os.path.join(BASE_DIR, 'seed.sql')



#  Connection helpers                                                  


def get_db():
    """
    Return the database connection for the current request context.
    Opens a new connection if one doesn't exist yet.
    Rows are returned as sqlite3.Row objects (accessible by column name).
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()



#  Initialization                                                      


def init_db(seed=False):
    """
    Create all tables from schema.sql.
    Optionally load sample data from seed.sql.

    Call once at startup:
        with app.app_context():
            init_db(seed=True)   # first run
            init_db()            # subsequent runs (safe, uses IF NOT EXISTS)
    """
    db = get_db()

    with open(SCHEMA, 'r') as f:
        db.executescript(f.read())

    if seed:
        with open(SEED, 'r') as f:
            db.executescript(f.read())

    db.commit()
    print(f"[DB] Initialized at {DB_PATH}")


def init_app(app):
    """Register database functions with a Flask app instance."""
    app.teardown_appcontext(close_db)


#  Query helpers                                                       

def query_db(sql, args=(), one=False):
    """
    Run a SELECT query and return results.

    Args:
        sql  : SQL string with ? placeholders
        args : tuple of values to bind
        one  : if True, return a single row (or None); otherwise return a list

    Examples:
        user = query_db("SELECT * FROM users WHERE user_id = ?", (user_id,), one=True)
        kits = query_db("SELECT * FROM lab_kits WHERE status = ?", ('available',))
    """
    cur = get_db().execute(sql, args)
    rv  = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(sql, args=()):
    """
    Run an INSERT, UPDATE, or DELETE and commit.

    Returns the lastrowid (useful for INSERT).

    Examples:
        new_id = execute_db(
            "INSERT INTO users (username, password_hash, email, ...) VALUES (?,?,?,...)",
            (username, hashed_pw, email, ...)
        )
    """
    db  = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


#  Convenience functions — Users                                       

def get_user_by_id(user_id):
    return query_db("SELECT * FROM users WHERE user_id = ?", (user_id,), one=True)


def get_user_by_username(username):
    return query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)


def create_user(username, password_hash, email, first_name, last_name, role,
                student_id=None, major=None, employee_id=None, department=None):
    return execute_db(
        """INSERT INTO users
           (username, password_hash, email, first_name, last_name, role,
            student_id, major, employee_id, department)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (username, password_hash, email, first_name, last_name, role,
         student_id, major, employee_id, department)
    )


#  Convenience functions — Lab Kits                                    

def get_all_kits():
    return query_db("SELECT * FROM lab_kits ORDER BY kit_id")


def get_available_kits():
    return query_db("SELECT * FROM lab_kits WHERE status = 'available' ORDER BY kit_id")


def get_kit_by_id(kit_id):
    return query_db("SELECT * FROM lab_kits WHERE kit_id = ?", (kit_id,), one=True)


def get_kit_components(kit_id):
    return query_db(
        "SELECT * FROM kit_components WHERE kit_id = ? ORDER BY component_id",
        (kit_id,)
    )


def update_kit_status(kit_id, status):
    execute_db("UPDATE lab_kits SET status = ? WHERE kit_id = ?", (status, kit_id))


#  Convenience functions — Checkouts                                   

def get_checkout_by_id(checkout_id):
    return query_db("SELECT * FROM checkouts WHERE checkout_id = ?", (checkout_id,), one=True)


def get_active_checkouts():
    return query_db(
        """SELECT c.*, u.first_name, u.last_name, k.kit_name
           FROM checkouts c
           JOIN users    u ON c.student_id = u.user_id
           JOIN lab_kits k ON c.kit_id     = k.kit_id
           WHERE c.status IN ('pending', 'active', 'overdue')
           ORDER BY c.due_date"""
    )


def get_student_checkouts(student_id):
    return query_db(
        """SELECT c.*, k.kit_name
           FROM checkouts c
           JOIN lab_kits k ON c.kit_id = k.kit_id
           WHERE c.student_id = ?
           ORDER BY c.checkout_date DESC""",
        (student_id,)
    )


def create_checkout(kit_id, student_id, due_date):
    checkout_id = execute_db(
        """INSERT INTO checkouts (kit_id, student_id, due_date, status)
           VALUES (?, ?, ?, 'pending')""",
        (kit_id, student_id, due_date)
    )
    update_kit_status(kit_id, 'pending')
    return checkout_id


def approve_checkout(checkout_id, processed_by):
    checkout = get_checkout_by_id(checkout_id)
    if not checkout:
        raise ValueError(f"Checkout {checkout_id} not found")
    execute_db(
        "UPDATE checkouts SET status = 'active', processed_by = ? WHERE checkout_id = ?",
        (processed_by, checkout_id)
    )
    update_kit_status(checkout['kit_id'], 'checked_out')


def complete_return(checkout_id, processed_by):
    from datetime import datetime
    checkout = get_checkout_by_id(checkout_id)
    if not checkout:
        raise ValueError(f"Checkout {checkout_id} not found")
    execute_db(
        """UPDATE checkouts
           SET status = 'returned', return_date = ?, processed_by = ?
           WHERE checkout_id = ?""",
        (datetime.now().isoformat(), processed_by, checkout_id)
    )
    update_kit_status(checkout['kit_id'], 'available')


#  Convenience functions — Damage Reports                             

def create_damage_report(component_id, reported_by, description):
    report_id = execute_db(
        """INSERT INTO damage_reports (component_id, reported_by, description)
           VALUES (?, ?, ?)""",
        (component_id, reported_by, description)
    )
    # Mark the component as damaged
    execute_db(
        "UPDATE kit_components SET condition = 'damaged' WHERE component_id = ?",
        (component_id,)
    )
    return report_id


def get_open_damage_reports():
    return query_db(
        """SELECT dr.*, kc.component_name, k.kit_name,
                  u.first_name || ' ' || u.last_name AS reported_by_name
           FROM damage_reports dr
           JOIN kit_components kc ON dr.component_id = kc.component_id
           JOIN lab_kits       k  ON kc.kit_id        = k.kit_id
           JOIN users          u  ON dr.reported_by   = u.user_id
           WHERE dr.status = 'open'
           ORDER BY dr.reported_at DESC"""
    )


#  Convenience functions — Inventory                                   

def get_inventory():
    return query_db("SELECT * FROM inventory WHERE inventory_id = 1", one=True)


#  Convenience functions — Courses & Assignments                       

def get_courses_by_instructor(instructor_id):
    return query_db(
        "SELECT * FROM courses WHERE instructor_id = ? ORDER BY course_code",
        (instructor_id,)
    )


def get_assignments_by_course(course_id):
    return query_db(
        """SELECT la.*, k.kit_name
           FROM lab_assignments la
           LEFT JOIN lab_kits k ON la.required_kit_id = k.kit_id
           WHERE la.course_id = ?
           ORDER BY la.due_date""",
        (course_id,)
    )
