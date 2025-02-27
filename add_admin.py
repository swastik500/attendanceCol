from app import app, db, User
from werkzeug.security import generate_password_hash

# Ensure database tables are created
with app.app_context():
    db.create_all()

    # Check if the admin user already exists
    admin_email = "swip@gmail.com"
    admin_password = "swip@2004"

    existing_admin = User.query.filter_by(username=admin_email).first()

    if not existing_admin:
        hashed_password = generate_password_hash(admin_password)
        admin_user = User(username=admin_email, password=hashed_password, role="Admin")

        # Add to database
        db.session.add(admin_user)
        db.session.commit()

        print("Admin user added successfully!")
    else:
        print("Admin user already exists!")
