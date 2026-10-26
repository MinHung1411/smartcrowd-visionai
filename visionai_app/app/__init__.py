from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config.config import Config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Set up login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.views.auth import auth_bp
    from app.views.main import main_bp
    from app.views.detection import detection_bp
    from app.views.color_detection import color_detection_bp
    from app.views.face_detection import face_detection_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(detection_bp, url_prefix='/detection')
    app.register_blueprint(color_detection_bp)
    app.register_blueprint(face_detection_bp)
    
    # Create database tables on Databricks Catalog
    # Note: For Databricks, tables should be pre-created via setup_databricks.py
    # db.create_all() may not work perfectly with Databricks dialect
    with app.app_context():
        try:
            db.create_all()
            print("[DB] Tables created/verified on Databricks Catalog")
        except Exception as e:
            print(f"[DB] Warning: db.create_all() skipped — {e}")
            print("[DB] Run 'python setup_databricks.py' to create tables manually")
    
    return app
