from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import db, User
from datetime import datetime
import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Handle 1-Click auto-login support for iframes & recruiter demo (Prioritized over current session)
    auto_type = request.args.get('auto', '').lower()
    if auto_type in ['demo', 'guest', 'viewer', 'test']:
        if current_user.is_authenticated:
            logout_user()
            session.clear()
        user = User.query.filter_by(username='demo').first()
        if not user:
            user = User(username='demo', email='demo@smartcrowd.ai', role='viewer')
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=False)
        return redirect(url_for('main.dashboard'))
    elif auto_type in ['admin', '1', 'true']:
        if current_user.is_authenticated:
            logout_user()
            session.clear()
        user = User.query.filter_by(username='admin').first()
        if user:
            login_user(user, remember=False)
            return redirect(url_for('main.dashboard'))
    
    # 2. If already logged in and not asking for auto-login, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # 3. Handle standard form login
    if request.method == 'POST':
        login_input = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
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
            flash('Tài khoản không tồn tại. Vui lòng kiểm tra lại tên đăng nhập hoặc email.', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            print(f"[LOGIN] FAILED: Account '{user.username}' is deactivated")
            flash('Tài khoản đã bị tạm khóa. Vui lòng liên hệ quản trị viên.', 'error')
            return render_template('auth/login.html')
        
        # Check password
        try:
            password_ok = user.check_password(password)
            print(f"[LOGIN] Password check result: {password_ok}")
        except Exception as e:
            print(f"[LOGIN] ERROR checking password: {e}")
            traceback.print_exc()
            password_ok = False
        
        if password_ok:
            if current_user.is_authenticated:
                logout_user()
                session.clear()
            login_user(user, remember=False)
            user.last_login = datetime.now()  # Lưu giờ Việt Nam (GMT+7)
            db.session.commit()
            print(f"[LOGIN] SUCCESS: {user.username} ({user.role})")
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            print(f"[LOGIN] FAILED: Wrong password for '{user.username}'")
            flash('Mật khẩu không chính xác. Vui lòng thử lại.', 'error')
    
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
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại trong hệ thống', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'error')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        user.role = 'viewer'
        
        db.session.add(user)
        db.session.commit()
        
        flash('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Bạn đã đăng xuất khỏi hệ thống thành công.', 'info')
    
    response = redirect(url_for('auth.login'))
    
    # Delete all authentication cookies with SameSite=None and Secure=True for iframe compatibility
    cookie_names = [
        current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token'),
        current_app.config.get('SESSION_COOKIE_NAME', 'session'),
        'session',
        'remember_token'
    ]
    for c_name in set(cookie_names):
        response.delete_cookie(c_name, path='/', samesite='None', secure=True)
        response.delete_cookie(c_name, path='/')
        
    return response
