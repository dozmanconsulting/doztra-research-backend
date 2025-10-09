from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings

# Create database connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Query for the user
user = db.query(User).filter(User.email == 'dozie.aji@gmail.com').first()

# Print user information
print(f'User exists: {user is not None}')
if user:
    print(f'User ID: {user.id}')
    print(f'Is active: {user.is_active}')
    print(f'Is verified: {user.is_verified}')
    print(f'Role: {user.role}')
else:
    print('User not found. Let\'s check all users in the database:')
    users = db.query(User).all()
    for u in users:
        print(f'- {u.email} (ID: {u.id}, Role: {u.role})')
