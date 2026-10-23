from flask import Flask, request, redirect, url_for
import mysql.connector
from pymongo import MongoClient
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key-for-session")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:3000")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:6000")

def get_mysql_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "rootpassword"),
        database=os.getenv("DB_NAME", "analytics_db")
    )

def get_mongo_collection():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongodb:27017/"))
    return client["analytics_results"]["stats"]

def require_auth():
    token = request.cookies.get('token')
    if not token:
        return False
    try:
        verify_resp = requests.post(f"{AUTH_SERVICE_URL}/verify", json={"token": token})
        if verify_resp.status_code == 200 and verify_resp.json().get("valid"):
            return True
    except Exception:
        pass
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            resp = requests.post(f"{AUTH_SERVICE_URL}/login", json={"username": username, "password": password})
            if resp.status_code == 200:
                token = resp.json().get("token")
                out = redirect(url_for('home'))
                out.set_cookie('token', token)
                return out
            else:
                error = "Invalid username or password."
        except Exception as e:
            error = f"Authentication service unreachable: {e}"

    return f'''
        <h2>Login</h2>
        <p style="color:red;">{error if error else ""}</p>
        <form method="POST">
            Username: <input type="text" name="username" required><br><br>
            Password: <input type="password" name="password" required><br><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/logout')
def logout():
    resp = redirect(url_for('login'))
    resp.delete_cookie('token')
    return resp

@app.route('/home', methods=['GET', 'POST'])
def home():
    if not require_auth():
        return redirect(url_for('login'))

    error_msg = ""
    if request.method == 'POST':
        try:
            # 1. Clean and validate course name
            raw_course = request.form.get('course', '')
            course = raw_course.strip().upper()
            if not course:
                raise ValueError("Course name cannot be empty.")

            # 2. Strict grade validation (0-100 float)
            raw_grade = request.form.get('grade', '')
            try:
                grade = float(raw_grade)
            except ValueError:
                raise ValueError("Grade must be a valid number (no strings allowed).")

            if not (0 <= grade <= 100):
                raise ValueError("Grade must be between 0 and 100.")
            
            # 3. Save raw grade to MySQL
            db = get_mysql_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO course_grades (course, grade) VALUES (%s, %s)", (course, grade))
            db.commit()
            cursor.close()
            db.close()
            
            # 4. TRIGGER ANALYTICS SERVICE: Notify analytics microservice to aggregate and write to MongoDB
            try:
                requests.post(f"{ANALYTICS_SERVICE_URL}/trigger-analytics", timeout=5)
            except Exception as trig_err:
                print(f"Warning: Failed to reach analytics service trigger: {trig_err}")
                
            # 5. Redirect to view summary table
            return redirect(url_for('view_summary'))

        except ValueError as ve:
            error_msg = str(ve)
        except Exception as ex:
            error_msg = f"An unexpected error occurred: {ex}"

    return f'''
        <h2>Enter Course Grade (Home)</h2>
        <a href="/view">View Summary</a> | <a href="/logout">Logout</a>
        <p style="color:red;">{error_msg}</p>
        <hr>
        <form method="POST">
            Course Name: <input type="text" name="course" required><br><br>
            Grade (0-100): <input type="number" step="any" name="grade" required><br><br>
            <input type="submit" value="Submit & Sync Analytics">
        </form>
    '''

@app.route('/view', methods=['GET'])
def view_summary():
    if not require_auth():
        return redirect(url_for('login'))

    try:
        mongo_col = get_mongo_collection()
        stats = list(mongo_col.find({}, {"_id": 0}))
    except Exception:
        stats = []

    table_rows = ""
    for s in stats:
        table_rows += f"<tr><td>{s.get('course')}</td><td>{s.get('min_val')}</td><td>{s.get('max_val')}</td><td>{s.get('avg_val', 0):.2f}</td><td>{s.get('count_val')}</td></tr>"

    return f'''
        <h2>Course Analytics Summary View</h2>
        <a href="/home">Enter More Grades</a> | <a href="/logout">Logout</a>
        <hr>
        <table border="1" cellpadding="5">
            <tr><th>Course</th><th>Min Grade</th><th>Max Grade</th><th>Average Grade</th><th>Count</th></tr>
            {table_rows if table_rows else "<tr><td colspan='5'>No analytics data available yet.</td></tr>"}
        </table>
    '''

@app.route('/')
def index():
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)