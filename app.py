import os
import sqlite3
from functools import wraps
from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash, g)
from werkzeug.security import generate_password_hash, check_password_hash

# Point Flask to the existing pages/ folder for templates
app = Flask(
    __name__,
    template_folder='pages',
    static_folder='static'
)
app.secret_key = 'change-this-to-a-random-secret-in-production'

DATABASE = os.path.join('database', 'lab_kit.db')
SCHEMA   = os.path.join('database', 'schema.sql')


# ── Database helpers ───────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row        # access columns by name
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Create the database from schema.sql if it does not exist yet."""
    if not os.path.exists(DATABASE):
        print("Initializing database from schema.sql...")
        conn = sqlite3.connect(DATABASE)
        with open(SCHEMA, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("Database ready.")


# ── Auth decorators ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in allowed_roles:
                flash('You do not have permission for that action.')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db   = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f'Welcome back, {user["first_name"]}!')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username   = request.form['username']
        password   = request.form['password']
        email      = request.form['email']
        first_name = request.form['first_name']
        last_name  = request.form['last_name']
        role       = request.form.get('role', 'Student')

        db     = get_db()
        exists = db.execute(
            'SELECT user_id FROM users WHERE username = ?', (username,)
        ).fetchone()

        if exists:
            flash('Username already taken.')
        else:
            db.execute(
                '''INSERT INTO users
                   (username, password_hash, email, first_name, last_name, role)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (username, generate_password_hash(password),
                 email, first_name, last_name, role)
            )
            db.commit()
            flash('Account created! Please log in.')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    db   = get_db()

    if role == 'Student':
        checkouts = db.execute(
            '''SELECT c.*, k.kit_name FROM checkouts c
               JOIN lab_kits k ON c.kit_id = k.kit_id
               WHERE c.student_id = ?''', (session['user_id'],)
        ).fetchall()
        return render_template('dashboard.html', checkouts=checkouts, role=role)

    if role in ('LabManager', 'Admin'):
        kits    = db.execute('SELECT * FROM lab_kits').fetchall()
        pending = db.execute(
            "SELECT c.*, k.kit_name, u.first_name, u.last_name "
            "FROM checkouts c "
            "JOIN lab_kits k ON c.kit_id = k.kit_id "
            "JOIN users u ON c.student_id = u.user_id "
            "WHERE c.status = 'Pending'"
        ).fetchall()
        return render_template('dashboard.html', kits=kits,
                               pending=pending, role=role)

    return render_template('dashboard.html', role=role)


@app.route('/kits')
@login_required
def list_kits():
    db   = get_db()
    kits = db.execute('SELECT * FROM lab_kits').fetchall()
    return render_template('kits.html', kits=kits)


@app.route('/kits/<int:kit_id>')
@login_required
def kit_detail(kit_id):
    db         = get_db()
    kit        = db.execute(
        'SELECT * FROM lab_kits WHERE kit_id = ?', (kit_id,)
    ).fetchone()
    components = db.execute(
        'SELECT * FROM kit_components WHERE kit_id = ?', (kit_id,)
    ).fetchall()
    return render_template('kit_detail.html', kit=kit, components=components)


@app.route('/checkout/<int:kit_id>', methods=['POST'])
@login_required
@role_required('Student')
def request_checkout(kit_id):
    db  = get_db()
    kit = db.execute(
        'SELECT * FROM lab_kits WHERE kit_id = ?', (kit_id,)
    ).fetchone()

    if not kit or kit['status'] != 'Available':
        flash('This kit is not currently available.')
        return redirect(url_for('list_kits'))

    db.execute(
        '''INSERT INTO checkouts (kit_id, student_id, checkout_date, status)
           VALUES (?, ?, date('now'), 'Pending')''',
        (kit_id, session['user_id'])
    )
    db.execute(
        "UPDATE lab_kits SET status = 'Checked Out' WHERE kit_id = ?", (kit_id,)
    )
    db.commit()
    flash('Checkout requested! Awaiting Lab Manager approval.')
    return redirect(url_for('dashboard'))


@app.route('/return/<int:checkout_id>', methods=['POST'])
@login_required
def return_kit(checkout_id):
    db       = get_db()
    checkout = db.execute(
        'SELECT * FROM checkouts WHERE checkout_id = ?', (checkout_id,)
    ).fetchone()

    if not checkout:
        flash('Checkout record not found.')
        return redirect(url_for('dashboard'))

    db.execute(
        "UPDATE checkouts SET return_date = date('now'), status = 'Returned' "
        "WHERE checkout_id = ?", (checkout_id,)
    )
    db.execute(
        "UPDATE lab_kits SET status = 'Available' WHERE kit_id = ?",
        (checkout['kit_id'],)
    )
    db.commit()
    flash('Kit returned successfully.')
    return redirect(url_for('dashboard'))


@app.route('/damage-report', methods=['GET', 'POST'])
@login_required
def damage_report():
    db = get_db()
    if request.method == 'POST':
        component_id = request.form['component_id']
        description  = request.form['description']
        db.execute(
            '''INSERT INTO damage_reports
               (component_id, reported_by, description, reported_at, status)
               VALUES (?, ?, ?, datetime('now'), 'Open')''',
            (component_id, session['user_id'], description)
        )
        db.commit()
        flash('Damage report submitted.')
        return redirect(url_for('dashboard'))

    components = db.execute('SELECT * FROM kit_components').fetchall()
    return render_template('damage_report.html', components=components)


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
