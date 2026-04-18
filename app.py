from flask import Flask, render_template
from database import get_db, close_db

app = Flask(__name__, template_folder='database', static_folder='database', static_url_path='')

app.teardown_appcontext(close_db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/kits')
def kits():
    return render_template('student_kit.html')

@app.route('/request')
def request_form():
    return render_template('request_form.html')

if __name__ == '__main__':
    app.run(debug=True)
