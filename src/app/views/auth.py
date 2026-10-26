from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import db, User
from datetime import datetime
import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        login_input = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        print(f"\n[LOGIN] Attempt: '{login_input}'")
        
        # Support login by email OR username
        user = User.query.filter_by(email=login_input).first()
        if not user:
            user = User.query.filter_by(username=login_input).first()
            if user:
                print(f"[LOGIN] Found by username: {user.username} ({user.email})")
        else:
            print(f"[LOGIN] Found by email: {user.email}")
        
        if not user:
            print(f"[LOGIN] FAILED: No user found for '{login_input}'")
            flash('Account not found. Please check your email or username.', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            print(f"[LOGIN] FAILED: Account '{user.username}' is deactivated")
            flash('Account is deactivated. Please contact admin.', 'error')
            return render_template('auth/login.html')
        
        # Check password
        try:
            password_ok = user.check_password(password)
            print(f"[LOGIN] Password check result: {password_ok}")
            print(f"[LOGIN] Hash in DB: {user.password_hash[:50]}...")
        except Exception as e:
            print(f"[LOGIN] ERROR checking password: {e}")
            traceback.print_exc()
            password_ok = False
        
        if password_ok:
            login_user(user, remember=remember)
            user.last_login = datetime.now()  # Lưu giờ Việt Nam (GMT+7)
            db.session.commit()
            print(f"[LOGIN] SUCCESS: {user.username} ({user.role})")
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            print(f"[LOGIN] FAILED: Wrong password for '{user.username}'")
            flash('Invalid password. Please try again.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        # Default role is 'user', not 'admin'
        # Only existing admins can grant admin rights to other users
        user.role = 'user'  # Explicitly set to non-admin
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
