from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from config import Config
from models import db, User, Class, Subject, Attendance, Course
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Create tables if not exist
with app.app_context():
    db.create_all()

    # Admin Credentials
    admin_email = "swip@gmail.com"
    admin_password = "swip@2004"

    # Check if admin already exists
    existing_admin = User.query.filter_by(username=admin_email).first()

    if not existing_admin:
        hashed_password = generate_password_hash(admin_password)  # Hash the password
        admin_user = User(username=admin_email, password=hashed_password, role="admin")

        # Add admin to database
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user added successfully!")
    else:
        print("⚠️ Admin user already exists!")


# ---- ROUTES ---- #

@app.route('/')
def home():
    return render_template('index.html')


# ---- AUTHENTICATION ---- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session.permanent = True  # Keep session active

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# ---- ADMIN DASHBOARD ---- #
@app.route('/admin')
def admin_dashboard():
    if 'user_id' in session and session['role'] == 'admin':
        users = User.query.all()
        classes = Class.query.all()
        subjects = Subject.query.all()
        courses = Course.query.all()
        return render_template('admin_dashboard.html', users=users, classes=classes, subjects=subjects, courses=courses)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if username and password and role:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("User already exists!", "warning")
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password, role=role)
                db.session.add(new_user)
                db.session.commit()
                flash("User registered successfully!", "success")
        else:
            flash("All fields are required!", "danger")

    users = User.query.all()
    return render_template('register.html', users=users)


@app.route('/delete_user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
    else:
        flash("User not found!", "danger")

    return redirect(url_for('admin_dashboard'))

#----- courses-----#
@app.route('/manage_courses', methods=['GET', 'POST'])
def manage_courses():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        course_name = request.form.get('course_name')
        description = request.form.get('description')

        if course_name:
            existing_course = Course.query.filter_by(name=course_name).first()
            if existing_course:
                flash("Course already exists!", "warning")
            else:
                new_course = Course(name=course_name, description=description)
                db.session.add(new_course)
                db.session.commit()
                flash("Course added successfully!", "success")
        else:
            flash("Course name is required!", "danger")

    courses = Course.query.all()
    return render_template('manage_courses.html', courses=courses)
#---- manage users-----#
@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if username and password and role:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("User already exists!", "warning")
            else:
                new_user = User(username=username, password=generate_password_hash(password), role=role)
                db.session.add(new_user)
                db.session.commit()
                flash("User added successfully!", "success")
        else:
            flash("All fields are required!", "danger")

    users = User.query.all()
    return render_template('manage_users.html', users=users)

# ---- CLASS MANAGEMENT ---- #
@app.route('/add_class', methods=['POST'])
def add_class():
    if 'user_id' in session and session['role'] == 'admin':
        name = request.form['name']
        year = request.form['year']

        new_class = Class(name=name, year=year)
        db.session.add(new_class)
        db.session.commit()
        flash("Class added successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    return "Unauthorized Access"


@app.route('/delete_class/<int:class_id>')
def delete_class(class_id):
    if 'user_id' in session and session['role'] == 'admin':
        class_entry = Class.query.get(class_id)
        if class_entry:
            db.session.delete(class_entry)
            db.session.commit()
            flash("Class deleted!", "success")
        return redirect(url_for('admin_dashboard'))
    return "Unauthorized Access"


# ---- SUBJECT MANAGEMENT ---- #
@app.route('/add_subject', methods=['POST'])
def add_subject():
    if 'user_id' in session and session['role'] == 'admin':
        name = request.form['name']
        class_id = int(request.form['class_id'])
        teacher_id = int(request.form['teacher_id'])

        new_subject = Subject(name=name, class_id=class_id, teacher_id=teacher_id)
        db.session.add(new_subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    return "Unauthorized Access"


@app.route('/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    if 'user_id' in session and session['role'] == 'admin':
        subject = Subject.query.get(subject_id)
        if subject:
            db.session.delete(subject)
            db.session.commit()
            flash("Subject deleted!", "success")
        return redirect(url_for('admin_dashboard'))
    return "Unauthorized Access"


# ---- TEACHER DASHBOARD ---- #
@app.route('/teacher')
def teacher_dashboard():
    if 'user_id' in session and session['role'] == 'teacher':
        subjects = Subject.query.filter_by(teacher_id=session['user_id']).all()
        students = User.query.filter_by(role='student').all()
        return render_template('teacher_dashboard.html', subjects=subjects, students=students)
    return redirect(url_for('login'))


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' in session and session['role'] == 'teacher':
        student_id = int(request.form['student_id'])
        subject_id = int(request.form['subject_id'])
        status = request.form['status']

        if not status in ['Present', 'Absent']:
            flash("Invalid attendance status", "danger")
            return redirect(url_for('teacher_dashboard'))

        attendance = Attendance(student_id=student_id, subject_id=subject_id, date=date.today(), status=status)
        db.session.add(attendance)
        db.session.commit()
        flash("Attendance marked!", "success")
        return redirect(url_for('teacher_dashboard'))
    return "Unauthorized Access"


# ---- STUDENT DASHBOARD ---- #
@app.route('/student')
def student_dashboard():
    if 'user_id' in session and session['role'] == 'student':
        student_id = session['user_id']
        attendance_records = Attendance.query.filter_by(student_id=student_id).all()

        total_classes = len(attendance_records)
        present_count = sum(1 for record in attendance_records if record.status == 'Present')
        attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0

        return render_template('student_dashboard.html', attendance=attendance_records, percentage=attendance_percentage)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
