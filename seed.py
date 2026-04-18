"""
seed.py  —  Populate the database with sample data for testing.
Run ONCE after the database has been created:

    python seed.py

Re-running is safe: it skips records that already exist.
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = os.path.join('database', 'lab_kit.db')
SCHEMA   = os.path.join('database', 'schema.sql')


def get_conn():
    if not os.path.exists(DATABASE):
        print("Database not found — creating from schema.sql...")
        conn = sqlite3.connect(DATABASE)
        with open(SCHEMA) as f:
            conn.executescript(f.read())
        conn.commit()
    else:
        conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def seed_users(conn):
    sample_users = [
        ('admin',    'admin123',    'admin@fau.edu',       'Alice',  'Admin',   'Admin'),
        ('manager1', 'manager123',  'manager@fau.edu',     'Bob',    'Manager', 'LabManager'),
        ('student1', 'student123',  'student1@fau.edu',    'Carlos', 'Rivera',  'Student'),
        ('student2', 'student123',  'student2@fau.edu',    'Dana',   'Kim',     'Student'),
        ('prof1',    'prof123',     'professor@fau.edu',   'Dr. Eve','Chen',    'Instructor'),
    ]
    for username, password, email, first, last, role in sample_users:
        exists = conn.execute(
            'SELECT user_id FROM users WHERE username = ?', (username,)
        ).fetchone()
        if not exists:
            conn.execute(
                '''INSERT INTO users (username, password_hash, email, first_name, last_name, role)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (username, generate_password_hash(password), email, first, last, role)
            )
            print(f"  + user: {username} ({role})")
        else:
            print(f"  ~ skip: {username} already exists")
    conn.commit()


def seed_kits(conn):
    sample_kits = [
        ('EEL3111 Circuit Kit',   'Basic circuits kit — resistors, capacitors, breadboard', 1),
        ('CDA3101 Logic Kit',     'Digital logic gates and IC chips',                       1),
        ('EEL4744 Embedded Kit',  'Microcontroller board with sensors and jumpers',         2),
        ('PHY2048 Lab Kit',       'Physics measurement tools — calipers, weights, spring',  3),
        ('COP3502 Robotics Kit',  'Servo motors, sensors, and Arduino Uno',                 1),
    ]
    for name, desc, course_id in sample_kits:
        exists = conn.execute(
            'SELECT kit_id FROM lab_kits WHERE kit_name = ?', (name,)
        ).fetchone()
        if not exists:
            conn.execute(
                'INSERT INTO lab_kits (kit_name, description, course_id, status) VALUES (?, ?, ?, ?)',
                (name, desc, course_id, 'Available')
            )
            print(f"  + kit: {name}")
        else:
            print(f"  ~ skip: {name} already exists")
    conn.commit()


def seed_components(conn):
    kits = conn.execute('SELECT kit_id, kit_name FROM lab_kits').fetchall()
    components_map = {
        'EEL3111 Circuit Kit':  [('Resistor Pack (100pc)', 1), ('Capacitor Pack', 1),
                                  ('Breadboard', 2), ('Jumper Wires', 1), ('Multimeter', 1)],
        'CDA3101 Logic Kit':    [('74LS00 NAND Gate', 4), ('74LS04 NOT Gate', 4),
                                  ('74LS86 XOR Gate', 2), ('7-Segment Display', 2)],
        'EEL4744 Embedded Kit': [('Arduino Uno', 1), ('USB Cable', 1),
                                  ('Temperature Sensor', 2), ('LED Pack', 1), ('Servo Motor', 2)],
        'PHY2048 Lab Kit':      [('Digital Calipers', 1), ('Spring Scale', 1),
                                  ('Mass Set (200g)', 1), ('Meter Stick', 1)],
        'COP3502 Robotics Kit': [('Servo Motor SG90', 4), ('Ultrasonic Sensor', 2),
                                  ('Arduino Uno', 1), ('Chassis Frame', 1), ('Battery Pack', 1)],
    }
    for kit in kits:
        comps = components_map.get(kit['kit_name'], [])
        for comp_name, qty in comps:
            exists = conn.execute(
                'SELECT component_id FROM kit_components WHERE kit_id = ? AND component_name = ?',
                (kit['kit_id'], comp_name)
            ).fetchone()
            if not exists:
                conn.execute(
                    '''INSERT INTO kit_components (kit_id, component_name, quantity, condition)
                       VALUES (?, ?, ?, 'Good')''',
                    (kit['kit_id'], comp_name, qty)
                )
                print(f"  + component: {comp_name} → {kit['kit_name']}")
    conn.commit()


def main():
    print("\n── Seeding database ──────────────────────────────────────")
    conn = get_conn()

    print("\n[Users]")
    seed_users(conn)

    print("\n[Lab Kits]")
    seed_kits(conn)

    print("\n[Components]")
    seed_components(conn)

    conn.close()
    print("\n✓ Done. Test credentials:")
    print("  admin     / admin123    (Admin)")
    print("  manager1  / manager123  (Lab Manager)")
    print("  student1  / student123  (Student)")
    print("  prof1     / prof123     (Instructor)\n")


if __name__ == '__main__':
    main()
