from app import app, db
from models import User  # Ensure you import User from models
from werkzeug.security import generate_password_hash, check_password_hash


# Create database tables
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
