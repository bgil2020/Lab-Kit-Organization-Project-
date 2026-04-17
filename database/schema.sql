-- Lab Kit Organization System — Database Schema
-- CEN 4010 

PRAGMA foreign_keys = ON;

-- USERS
-- Flattened from the class hierarchy (Student, Instructor,
-- LabManager, Admin all stored in one table with a role column)
-- Role-specific fields are nullable

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK(role IN ('student', 'instructor', 'lab_manager', 'admin')),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Student-specific
    student_id    TEXT    UNIQUE,
    major         TEXT,

    -- Instructor / LabManager-specific
    employee_id   TEXT    UNIQUE,
    department    TEXT
);


-- COURSES

CREATE TABLE IF NOT EXISTS courses (
    course_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name   TEXT    NOT NULL,
    course_code   TEXT    NOT NULL UNIQUE,
    instructor_id INTEGER NOT NULL,
    semester      TEXT    NOT NULL,

    FOREIGN KEY (instructor_id) REFERENCES users(user_id) ON DELETE RESTRICT
);


-- LAB KITS

CREATE TABLE IF NOT EXISTS lab_kits (
    kit_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    kit_name    TEXT    NOT NULL,
    description TEXT,
    course_id   INTEGER,
    status      TEXT    NOT NULL DEFAULT 'available'
                CHECK(status IN ('available', 'checked_out', 'pending', 'damaged')),

    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL
);


-- KIT COMPONENTS

CREATE TABLE IF NOT EXISTS kit_components (
    component_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    kit_id         INTEGER NOT NULL,
    component_name TEXT    NOT NULL,
    quantity       INTEGER NOT NULL DEFAULT 1 CHECK(quantity >= 0),
    description    TEXT,
    condition      TEXT    NOT NULL DEFAULT 'good'
                   CHECK(condition IN ('good', 'fair', 'damaged')),

    FOREIGN KEY (kit_id) REFERENCES lab_kits(kit_id) ON DELETE CASCADE
);


-- CHECKOUTS

CREATE TABLE IF NOT EXISTS checkouts (
    checkout_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    kit_id        INTEGER NOT NULL,
    student_id    INTEGER NOT NULL,
    checkout_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date      DATETIME NOT NULL,
    return_date   DATETIME,
    status        TEXT    NOT NULL DEFAULT 'pending'
                  CHECK(status IN ('pending', 'active', 'returned', 'overdue')),
    processed_by  INTEGER,

    FOREIGN KEY (kit_id)       REFERENCES lab_kits(kit_id) ON DELETE RESTRICT,
    FOREIGN KEY (student_id)   REFERENCES users(user_id)   ON DELETE RESTRICT,
    FOREIGN KEY (processed_by) REFERENCES users(user_id)   ON DELETE SET NULL
);


-- LAB ASSIGNMENTS

CREATE TABLE IF NOT EXISTS lab_assignments (
    assignment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id       INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT,
    required_kit_id INTEGER,
    due_date        DATETIME,

    FOREIGN KEY (course_id)       REFERENCES courses(course_id)   ON DELETE CASCADE,
    FOREIGN KEY (required_kit_id) REFERENCES lab_kits(kit_id)     ON DELETE SET NULL
);


-- INVENTORY (single-row summary table, updated via triggers)

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    total_kits     INTEGER NOT NULL DEFAULT 0,
    available_kits INTEGER NOT NULL DEFAULT 0,
    last_updated   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Seed the single inventory row on first run
INSERT OR IGNORE INTO inventory (inventory_id, total_kits, available_kits)
VALUES (1, 0, 0);


-- DAMAGE REPORTS

CREATE TABLE IF NOT EXISTS damage_reports (
    report_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    reported_by  INTEGER NOT NULL,
    description  TEXT    NOT NULL,
    reported_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    status       TEXT    NOT NULL DEFAULT 'open'
                 CHECK(status IN ('open', 'resolved', 'escalated')),

    FOREIGN KEY (component_id) REFERENCES kit_components(component_id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by)  REFERENCES users(user_id)               ON DELETE RESTRICT
);


-- TRIGGERS — keep inventory counts in sync automatically


-- When a new kit is added, increment total and available
CREATE TRIGGER IF NOT EXISTS trg_kit_insert
AFTER INSERT ON lab_kits
BEGIN
    UPDATE inventory SET
        total_kits     = total_kits + 1,
        available_kits = available_kits + CASE WHEN NEW.status = 'available' THEN 1 ELSE 0 END,
        last_updated   = CURRENT_TIMESTAMP
    WHERE inventory_id = 1;
END;

-- When a kit is deleted, decrement total
-- (available handled separately by status)
CREATE TRIGGER IF NOT EXISTS trg_kit_delete
AFTER DELETE ON lab_kits
BEGIN
    UPDATE inventory SET
        total_kits     = total_kits - 1,
        available_kits = CASE
            WHEN OLD.status = 'available' THEN available_kits - 1
            ELSE available_kits
        END,
        last_updated   = CURRENT_TIMESTAMP
    WHERE inventory_id = 1;
END;

-- When a kit's status changes, update available_kits count
CREATE TRIGGER IF NOT EXISTS trg_kit_status_change
AFTER UPDATE OF status ON lab_kits
WHEN OLD.status != NEW.status
BEGIN
    UPDATE inventory SET
        available_kits = available_kits
            + CASE WHEN NEW.status = 'available' THEN 1 ELSE 0 END
            - CASE WHEN OLD.status = 'available' THEN 1 ELSE 0 END,
        last_updated   = CURRENT_TIMESTAMP
    WHERE inventory_id = 1;
END;
