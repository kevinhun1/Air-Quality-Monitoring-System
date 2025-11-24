# create_admin.py
from app.database.connection import SessionLocal
from app.models import user, sensor_reading, alert
from app.auth.utils import hash_password
from app.models.user import User

def create_admin():
    db = SessionLocal()

    name = "Admin"
    email = "admin@example.com"
    password = "StrongAdminPass123"

    hashed = hash_password(password)

    admin = User(
        name=name,
        email=email,
        password_hash=hashed,
        role="admin"
    )

    db.add(admin)
    db.commit()
    db.close()

    print("Admin created successfully.")

if __name__ == "__main__":
    create_admin()
