from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db  # Importing models correctly

# Initialize Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key

db.init_app(app)  # Initialize SQLAlchemy with the app

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
    return render_template('admin_dashboard.html', users=users)


# Register Users (Admin Functionality)
@app.route('/admin/register', methods=['POST'])
def register_user_admin():
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


# Register Users (API Route)
@app.route('/api/register', methods=['POST'])
def register_user_api():
    data = request.json
    existing_user = User.query.filter_by(username=data['username']).first()

    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = generate_password_hash(data['password'])  # Hash the password
    new_user = User(username=data['username'], password=hashed_password, role=data['role'])
    db.session.add(new_user)

    try:
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/add_class', methods=['POST'])
def add_class():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    # Example logic: You may need to store class details in a table
    class_name = request.form.get('class_name')

    if not class_name:
        flash('Class name is required!', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Add logic to store the class in the database if you have a Class model
    flash(f'Class "{class_name}" added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# -------------------- Run Flask App --------------------
if __name__ == '__main__':
    app.run(debug=True)
