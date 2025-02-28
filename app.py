from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import csv
import io
from config import Config
from models import db, User, Class, Subject, Attendance, Course, LectureSchedule
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_, or_

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
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized Access!', 'error')
        return redirect(url_for('login'))
    
    users = User.query.all()
    classes = Class.query.all()
    courses = Course.query.all()
    return render_template('admin_dashboard.html', users=users, classes=classes, courses=courses)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not all([username, password, role]):
            flash('All fields are required!', 'error')
            return redirect(url_for('admin_dashboard'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('admin_dashboard'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        
        try:
            db.session.commit()
            flash('User registered successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error registering user!', 'error')
        
        return redirect(url_for('admin_dashboard'))

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
@app.route('/manage_classes', methods=['GET', 'POST'])
def manage_classes():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('class_name')
        year = request.form.get('year')

        if name and year:
            existing_class = Class.query.filter_by(name=name, year=year).first()
            if existing_class:
                flash("Class already exists!", "warning")
            else:
                new_class = Class(name=name, year=year)
                db.session.add(new_class)
                db.session.commit()
                flash("Class added successfully!", "success")
        else:
            flash("All fields are required!", "danger")

    classes = Class.query.all()
    return render_template('manage_classes.html', classes=classes)

@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    if 'user_id' in session and session['role'] == 'admin':
        courses = Course.query.all()
        if request.method == 'POST':
            class_name = request.form['class_name']
            course_id = request.form['course_id']
            year = request.form['year']
            
            if not class_name or not course_id or not year:
                flash("All fields (class name, year, and course) are required!", "danger")
                return render_template('add_class.html', courses=courses)
            
            existing_class = Class.query.filter_by(name=class_name).first()
            if existing_class:
                flash("Class with this name already exists!", "danger")
                return render_template('add_class.html', courses=courses)
            
            new_class = Class(name=class_name, year=year, course_id=course_id)
            db.session.add(new_class)
            db.session.commit()
            flash("Class added successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        
        classes = Class.query.all()
        return render_template('add_class.html', courses=courses, classes=classes)
    return "Unauthorized Access"

@app.route('/manage_course_assignments', methods=['GET'])
def manage_course_assignments():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    students = User.query.filter_by(role='student').all()
    courses = Course.query.all()
    return render_template('manage_course_assignments.html', students=students, courses=courses)

@app.route('/assign_course', methods=['POST'])
def assign_course():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')

    if not student_id or not course_id:
        flash("Both student and course must be selected!", "danger")
        return redirect(url_for('manage_course_assignments'))

    student = User.query.get(student_id)
    course = Course.query.get(course_id)

    if not student or not course:
        flash("Invalid student or course selected!", "danger")
        return redirect(url_for('manage_course_assignments'))

    if course in student.enrolled_courses:
        flash("Student is already enrolled in this course!", "warning")
    else:
        student.enrolled_courses.append(course)
        db.session.commit()
        flash("Course assigned successfully!", "success")

    return redirect(url_for('manage_course_assignments'))

@app.route('/unassign_course/<int:student_id>/<int:course_id>')
def unassign_course(student_id, course_id):
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    student = User.query.get(student_id)
    course = Course.query.get(course_id)

    if student and course and course in student.enrolled_courses:
        student.enrolled_courses.remove(course)
        db.session.commit()
        flash("Course unassigned successfully!", "success")
    else:
        flash("Invalid student or course!", "danger")

    return redirect(url_for('manage_course_assignments'))

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
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    subject = Subject.query.get(subject_id)
    if subject:
        db.session.delete(subject)
        db.session.commit()
        flash("Subject deleted successfully!", "success")
    else:
        flash("Subject not found!", "danger")

    return redirect(url_for('manage_subjects'))

@app.route('/manage_subjects', methods=['GET', 'POST'])
def manage_subjects():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        class_id = request.form.get('class_id')
        teacher_id = request.form.get('teacher_id')

        if subject_name and class_id and teacher_id:
            new_subject = Subject(name=subject_name, class_id=class_id, teacher_id=teacher_id)
            db.session.add(new_subject)
            db.session.commit()
            flash("Subject added successfully!", "success")
        else:
            flash("All fields are required!", "danger")

    subjects = Subject.query.all()
    classes = Class.query.all()
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('manage_subjects.html', subjects=subjects, classes=classes, teachers=teachers)
@app.route('/manage_schedules', methods=['GET', 'POST'])
def manage_schedules():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        class_id = request.form.get('class_id')
        day_of_week = request.form.get('day_of_week')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        if subject_id and class_id and day_of_week and start_time and end_time:
            # Convert time strings to Time objects
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()

            # Check for time conflicts
            existing_schedule = LectureSchedule.query.filter_by(
                class_id=class_id,
                day_of_week=day_of_week
            ).filter(
                or_(
                    and_(LectureSchedule.start_time <= start_time, LectureSchedule.end_time > start_time),
                    and_(LectureSchedule.start_time < end_time, LectureSchedule.end_time >= end_time)
                )
            ).first()

            if existing_schedule:
                flash("Time slot conflicts with an existing schedule!", "warning")
            else:
                new_schedule = LectureSchedule(
                    subject_id=subject_id,
                    class_id=class_id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time
                )
                db.session.add(new_schedule)
                db.session.commit()
                flash("Schedule added successfully!", "success")
        else:
            flash("All fields are required!", "danger")

    subjects = Subject.query.all()
    classes = Class.query.all()
    schedules = LectureSchedule.query.all()
    return render_template('manage_schedules.html', subjects=subjects, classes=classes, schedules=schedules)

@app.route('/delete_schedule/<int:schedule_id>')
def delete_schedule(schedule_id):
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('login'))

    schedule = LectureSchedule.query.get(schedule_id)
    if schedule:
        db.session.delete(schedule)
        db.session.commit()
        flash("Schedule deleted successfully!", "success")
    else:
        flash("Schedule not found!", "danger")

    return redirect(url_for('manage_schedules'))


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
        subject_id = int(request.form['subject_id'])
        student_ids = request.form.getlist('student_ids[]')
        for student_id in student_ids:
            status = request.form.get(f'status_{student_id}')
            if status in ['Present', 'Absent']:
                attendance = Attendance(
                    student_id=int(student_id),
                    subject_id=subject_id,
                    date=date.today(),
                    status=status
                )
                db.session.add(attendance)
        db.session.commit()
        flash("Attendance marked successfully!", "success")
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


@app.route('/download_attendance_csv')
def download_attendance_csv():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Unauthorized Access!', 'error')
        return redirect(url_for('login'))

    # Create a string buffer to write CSV data
    si = io.StringIO()
    cw = csv.writer(si)

    # Write headers
    cw.writerow(['Subject', 'Student', 'Date', 'Status'])

    # Get attendance records for subjects taught by this teacher
    subjects = Subject.query.filter_by(teacher_id=session['user_id']).all()
    subject_ids = [subject.id for subject in subjects]
    attendance_records = Attendance.query.filter(Attendance.subject_id.in_(subject_ids)).all()

    # Write attendance data
    for record in attendance_records:
        cw.writerow([
            record.subject.name,
            record.student.username,
            record.date.strftime('%Y-%m-%d'),
            record.status
        ])

    output = si.getvalue()
    si.close()

    # Create the response with CSV data
    response = app.make_response(output)
    response.headers['Content-Disposition'] = 'attachment; filename=attendance_records.csv'
    response.headers['Content-type'] = 'text/csv'

    return response

if __name__ == '__main__':
    app.run(debug=True)
