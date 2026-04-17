-- Lab Kit Organization System — Seed Data
-- Run AFTER schema.sql
-- Passwords are hashed with werkzeug (pbkdf2:sha256)
-- Plain-text equivalents shown in comments for dev use only


PRAGMA foreign_keys = ON;

-- USERS
-- password for all seed accounts: "password123"

INSERT OR IGNORE INTO users
    (username, password_hash, email, first_name, last_name, role, student_id, major, employee_id, department)
VALUES
    -- Admin
    ('admin',
     'pbkdf2:sha256:600000$abc123$hashedvalue1',
     'admin@fau.edu', 'System', 'Admin', 'admin',
     NULL, NULL, 'EMP-000', NULL),

    -- Instructors
    ('prof.smith',
     'pbkdf2:sha256:600000$abc123$hashedvalue2',
     'smith@fau.edu', 'Robert', 'Smith', 'instructor',
     NULL, NULL, 'EMP-101', 'Electrical Engineering'),

    ('prof.jones',
     'pbkdf2:sha256:600000$abc123$hashedvalue3',
     'jones@fau.edu', 'Laura', 'Jones', 'instructor',
     NULL, NULL, 'EMP-102', 'Computer Science'),

    -- Lab Managers
    ('labmanager',
     'pbkdf2:sha256:600000$abc123$hashedvalue4',
     'labmgr@fau.edu', 'Carlos', 'Rivera', 'lab_manager',
     NULL, NULL, 'EMP-201', NULL),

    -- Students
    ('n.gopeesingh',
     'pbkdf2:sha256:600000$abc123$hashedvalue5',
     'ngopeesingh2014@fau.edu', 'Nicholas', 'Gopeesingh', 'student',
     'S001', 'Computer Science', NULL, NULL),

    ('j.dormelus',
     'pbkdf2:sha256:600000$abc123$hashedvalue6',
     'jdormelus@fau.edu', 'Jeremy', 'Dormelus', 'student',
     'S002', 'Computer Science', NULL, NULL),

    ('j.pena',
     'pbkdf2:sha256:600000$abc123$hashedvalue7',
     'jpena@fau.edu', 'Juan', 'Pena', 'student',
     'S003', 'Computer Science', NULL, NULL),

    ('k.campbell',
     'pbkdf2:sha256:600000$abc123$hashedvalue8',
     'kyle.c@fau.edu', 'Kyle', 'Campbell', 'student',
     'S004', 'Computer Science', NULL, NULL);


-- COURSES
-- instructor_id 2 = prof.smith, 3 = prof.jones

INSERT OR IGNORE INTO courses (course_name, course_code, instructor_id, semester)
VALUES
    ('Introduction to Circuits',      'EEL3111', 2, 'Spring 2026'),
    ('Digital Logic Design',          'EEL3701', 2, 'Spring 2026'),
    ('Embedded Systems',              'CDA4630', 3, 'Spring 2026'),
    ('Prin. Software Engineering',          'CEN4010', 3, 'Spring 2026');


-- LAB KITS
-- course_id: 1=EEL3111, 2=EEL3701, 3=CDA4630, 4=CEN4010

INSERT OR IGNORE INTO lab_kits (kit_name, description, course_id, status)
VALUES
    ('Circuits Kit A',      'Resistors, capacitors, breadboard, DMM leads',   1, 'available'),
    ('Circuits Kit B',      'Resistors, capacitors, breadboard, DMM leads',   1, 'checked_out'),
    ('Circuits Kit C',      'Resistors, capacitors, breadboard, DMM leads',   1, 'available'),
    ('Digital Logic Kit A', 'Logic gates, flip-flops, 7-segment display',     2, 'available'),
    ('Digital Logic Kit B', 'Logic gates, flip-flops, 7-segment display',     2, 'damaged'),
    ('Embedded Kit A',      'Arduino Uno, sensors, jumper wires, LCD',        3, 'available'),
    ('Embedded Kit B',      'Arduino Uno, sensors, jumper wires, LCD',        3, 'pending'),
    ('Software Kit A',      'Raspberry Pi, SD card, HDMI adapter',            4, 'available');

-- ------------------------------------------------------------
-- KIT COMPONENTS
-- ------------------------------------------------------------
INSERT OR IGNORE INTO kit_components (kit_id, component_name, quantity, description, condition)
VALUES
    -- Circuits Kit A (kit_id=1)
    (1, 'Breadboard',         1,  '830-point solderless breadboard',     'good'),
    (1, 'Resistor Pack',      1,  'Assorted 1/4W resistors',             'good'),
    (1, 'Capacitor Pack',     1,  'Assorted ceramic & electrolytic caps', 'good'),
    (1, 'DMM Test Leads',     1,  'Red/black banana plug leads',         'good'),
    (1, 'Jumper Wires',       30, 'Male-to-male jumper wires',           'good'),

    -- Circuits Kit B (kit_id=2)
    (2, 'Breadboard',         1,  '830-point solderless breadboard',     'good'),
    (2, 'Resistor Pack',      1,  'Assorted 1/4W resistors',             'fair'),
    (2, 'Capacitor Pack',     1,  'Assorted ceramic & electrolytic caps', 'good'),
    (2, 'DMM Test Leads',     1,  'Red/black banana plug leads',         'good'),
    (2, 'Jumper Wires',       28, 'Male-to-male jumper wires',           'good'),

    -- Digital Logic Kit A (kit_id=4)
    (4, '74LS00 NAND Gate',   2,  'Quad 2-input NAND gate IC',           'good'),
    (4, '74LS74 Flip-Flop',   2,  'Dual D-type positive-edge flip-flop', 'good'),
    (4, '7-Segment Display',  1,  'Common cathode 7-segment display',    'good'),
    (4, 'Breadboard',         1,  '830-point solderless breadboard',     'good'),

    -- Digital Logic Kit B (kit_id=5)
    (5, '74LS00 NAND Gate',   2,  'Quad 2-input NAND gate IC',           'damaged'),
    (5, '74LS74 Flip-Flop',   1,  'Dual D-type positive-edge flip-flop', 'good'),
    (5, 'Breadboard',         1,  '830-point solderless breadboard',     'damaged'),

    -- Embedded Kit A (kit_id=6)
    (6, 'Arduino Uno',        1,  'ATmega328P microcontroller board',    'good'),
    (6, 'USB Cable',          1,  'USB-A to USB-B cable',                'good'),
    (6, 'Temperature Sensor', 1,  'DHT11 digital temp/humidity sensor',  'good'),
    (6, 'LCD Screen',         1,  '16x2 character LCD with I2C adapter', 'good'),
    (6, 'Jumper Wires',       20, 'Male-to-male jumper wires',           'good'),

    -- Embedded Kit B (kit_id=7)
    (7, 'Arduino Uno',        1,  'ATmega328P microcontroller board',    'good'),
    (7, 'USB Cable',          1,  'USB-A to USB-B cable',                'good'),
    (7, 'Temperature Sensor', 1,  'DHT11 digital temp/humidity sensor',  'good'),
    (7, 'Jumper Wires',       20, 'Male-to-male jumper wires',           'good'),

    -- Software Kit A (kit_id=8)
    (8, 'Raspberry Pi 4',     1,  '4GB RAM model',                       'good'),
    (8, 'MicroSD Card',       1,  '32GB class 10',                       'good'),
    (8, 'HDMI Adapter',       1,  'Micro-HDMI to HDMI adapter',          'good'),
    (8, 'USB Power Supply',   1,  '5V 3A USB-C power supply',            'good');

-- ------------------------------------------------------------
-- CHECKOUTS
-- student_id 5=nicholas, 6=jeremy, 7=juan
-- processed_by 4=labmanager
-- kit 2 = Circuits Kit B (checked_out), kit 7 = Embedded B (pending)
-- ------------------------------------------------------------
INSERT OR IGNORE INTO checkouts
    (kit_id, student_id, checkout_date, due_date, return_date, status, processed_by)
VALUES
    (2, 5, '2026-04-01 09:00:00', '2026-04-15 23:59:59', NULL,                  'active',   4),
    (7, 6, '2026-04-10 14:00:00', '2026-04-24 23:59:59', NULL,                  'pending',  NULL),
    (4, 7, '2026-03-15 10:00:00', '2026-03-29 23:59:59', '2026-03-28 16:00:00', 'returned', 4);

-- ------------------------------------------------------------
-- LAB ASSIGNMENTS
-- ------------------------------------------------------------
INSERT OR IGNORE INTO lab_assignments (course_id, title, description, required_kit_id, due_date)
VALUES
    (1, 'Lab 1: Ohm''s Law',
     'Verify Ohm''s Law using resistors and a DMM. Measure voltage, current, and resistance.',
     1, '2026-04-20 23:59:59'),

    (1, 'Lab 2: RC Circuits',
     'Build and analyze RC circuits. Observe charge/discharge behavior on an oscilloscope.',
     1, '2026-05-01 23:59:59'),

    (2, 'Lab 1: Logic Gates',
     'Implement basic Boolean functions using 74LS-series ICs on a breadboard.',
     4, '2026-04-18 23:59:59'),

    (3, 'Lab 1: Arduino Intro',
     'Set up Arduino IDE, blink an LED, and read a sensor value over serial.',
     6, '2026-04-22 23:59:59');


-- DAMAGE REPORTS
-- component 15 = Digital Logic Kit B NAND gate (damaged)
-- component 17 = Digital Logic Kit B breadboard (damaged)
-- reported_by 5=nicholas

INSERT OR IGNORE INTO damage_reports (component_id, reported_by, description, status)
VALUES
    (15, 5, 'NAND gate IC appears burnt, one pin is bent and broken off.', 'open'),
    (17, 5, 'Breadboard has cracked tie strips — rows 15-20 have no continuity.', 'escalated');
