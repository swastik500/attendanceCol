from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key

db = SQLAlchemy(app)


# -------------------- Database Models --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Admin, Teacher, Student


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(50), nullable=False)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # Present / Absent


# -------------------- Create Database & Add Admin User --------------------
with app.app_context():
    db.create_all()

    # Add admin users if they do not exist
    admin_emails = ["swip@gmail.com", "swip@2004"]
    for admin_email in admin_emails:
        existing_admin = User.query.filter_by(username=admin_email).first()
        if not existing_admin:
            hashed_password = generate_password_hash("adminpassword")  # Set a default password
            new_admin = User(username=admin_email, password=hashed_password, role="Admin")
            db.session.add(new_admin)
    db.session.commit()


# -------------------- Routes --------------------

# Home Page
@app.route('/')
def home():
    return render_template('index.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(username=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == "Admin":
                return redirect(url_for('admin_dashboard'))
            elif user.role == "Teacher":
                return redirect(url_for('teacher_dashboard'))
            elif user.role == "Student":
                return redirect(url_for('student_dashboard'))

        flash('Invalid credentials, try again!', 'danger')

    return render_template('login.html')


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))


# -------------------- Admin Routes --------------------

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    users = User.query.all()
    courses = Course.query.all()
    classes = Class.query.all()
    subjects = Subject.query.all()
    return render_template('admin_dashboard.html', users=users, courses=courses, classes=classes, subjects=subjects)


# Register Users (Admin Functionality)
@app.route('/admin/register', methods=['POST'])
def register_user():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    username = request.form['username']
    password = generate_password_hash(request.form['password'])
    role = request.form['role']

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('User registered successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# Add Courses (Admin)
@app.route('/admin/add_course', methods=['POST'])
def add_course():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    name = request.form['name']
    new_course = Course(name=name)
    db.session.add(new_course)
    db.session.commit()
    flash('Course added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# Add Classes (Admin)
@app.route('/admin/add_class', methods=['POST'])
def add_class():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    name = request.form['name']
    year = request.form['year']
    new_class = Class(name=name, year=year)
    db.session.add(new_class)
    db.session.commit()
    flash('Class added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# -------------------- Teacher Routes --------------------

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'Teacher':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    teacher_id = session['user_id']
    subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
    return render_template('teacher_dashboard.html', subjects=subjects)


# Mark Attendance (Teacher)
@app.route('/teacher/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session or session['role'] != 'Teacher':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    subject_id = request.form['subject_id']
    status = request.form['status']
    new_attendance = Attendance(student_id=student_id, subject_id=subject_id, date=request.form['date'], status=status)

    db.session.add(new_attendance)
    db.session.commit()
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))


# -------------------- Student Routes --------------------

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'Student':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    student_id = session['user_id']
    attendance_records = Attendance.query.filter_by(student_id=student_id).all()
    return render_template('student_dashboard.html', attendance_records=attendance_records)


# -------------------- Run Flask App --------------------
if __name__ == '__main__':
    app.run(debug=True)
