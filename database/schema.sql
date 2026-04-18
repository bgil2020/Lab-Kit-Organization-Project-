-- Lab Kit Organization System
-- schema.sql  —  run once to create all tables
-- Compatible with app.py Flask backend

PRAGMA foreign_keys = ON;

-- ── Users ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'Student'
                          CHECK(role IN ('Student','Instructor','LabManager','Admin')),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Lab Kits ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lab_kits (
    kit_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    kit_name    TEXT    NOT NULL,
    description TEXT,
    course_id   INTEGER,                    -- loosely linked, no hard FK for now
    status      TEXT    NOT NULL DEFAULT 'Available'
                        CHECK(status IN ('Available','Checked Out','Maintenance')),
    qr_code     TEXT                        -- reserved for QR code feature
);

-- ── Kit Components ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kit_components (
    component_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    kit_id         INTEGER NOT NULL,
    component_name TEXT    NOT NULL,
    quantity       INTEGER NOT NULL DEFAULT 1,
    description    TEXT,
    condition      TEXT    NOT NULL DEFAULT 'Good'
                           CHECK(condition IN ('Good','Fair','Damaged')),
    FOREIGN KEY (kit_id) REFERENCES lab_kits(kit_id)
);

-- ── Checkouts ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS checkouts (
    checkout_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    kit_id        INTEGER NOT NULL,
    student_id    INTEGER NOT NULL,
    checkout_date DATE    NOT NULL,
    due_date      DATE,
    return_date   DATE,
    status        TEXT    NOT NULL DEFAULT 'Pending'
                          CHECK(status IN ('Pending','Active','Returned','Overdue')),
    processed_by  INTEGER,                  -- Lab Manager user_id
    FOREIGN KEY (kit_id)    REFERENCES lab_kits(kit_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- ── Damage Reports ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS damage_reports (
    report_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    reported_by  INTEGER NOT NULL,
    description  TEXT    NOT NULL,
    reported_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    status       TEXT    NOT NULL DEFAULT 'Open'
                         CHECK(status IN ('Open','Resolved','Escalated')),
    FOREIGN KEY (component_id) REFERENCES kit_components(component_id),
    FOREIGN KEY (reported_by)  REFERENCES users(user_id)
);
