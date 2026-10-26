#!/usr/bin/env python3
"""
Database initialization script for VisionAI Object Detection System
"""

from app import create_app, db
from app.models.user import User
from app.models.detection import Detection

def init_database():
    """Initialize the database with tables and default admin user"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(email='admin@visionai.com').first()
        
        if not admin_user:
            # Create default admin user
            print("Creating default admin user...")
            admin_user = User(
                username='admin',
                email='admin@visionai.com',
                role='admin'
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("Admin user created successfully!")
            print("Email: admin@visionai.com")
            print("Password: admin123")
            print("Please change the password after first login!")
        else:
            print("Admin user already exists.")
        
        # Create a test user
        test_user = User.query.filter_by(email='user@visionai.com').first()
        
        if not test_user:
            print("Creating test user...")
            test_user = User(
                username='testuser',
                email='user@visionai.com',
                role='user'
            )
            test_user.set_password('user123')
            
            db.session.add(test_user)
            db.session.commit()
            
            print("Test user created successfully!")
            print("Email: user@visionai.com")
            print("Password: user123")
        else:
            print("Test user already exists.")
        
        print("\nDatabase initialization completed!")
        print("You can now run the application with: python run.py")

if __name__ == '__main__':
    init_database()
