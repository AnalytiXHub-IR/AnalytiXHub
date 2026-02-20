"""
Authentication Module for OPENCHAIN IR
Handles User Login, Logout, and Session Management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from modules.core.db_models import User, SessionLocal

auth_bp = Blueprint('auth', __name__)

# User class for Flask-Login (wraps DB model)
class AuthUser(UserMixin):
    def __init__(self, user_model):
        self.id = user_model.id
        self.username = user_model.username
        self.role = user_model.role
        self.user_model = user_model

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = SessionLocal()
        user = db.query(User).filter_by(username=username).first()
        db.close()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(AuthUser(user))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# ==================== USER MANAGEMENT (ADMIN ONLY) ====================

@auth_bp.route('/users')
@login_required
def list_users():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
        
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return render_template('users.html', users=users, active_page='settings')

@auth_bp.route('/users/create', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
        
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'officer')
    
    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('auth.list_users'))
        
    db = SessionLocal()
    if db.query(User).filter((User.username == username) | (User.email == email)).first():
        flash('User already exists.', 'error')
        db.close()
        return redirect(url_for('auth.list_users'))
        
    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.close()
    
    flash(f"User '{username}' created successfully.", "success")
    return redirect(url_for('auth.list_users'))

@auth_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
        
    if user_id == current_user.id:
        flash("Cannot delete your own account.", "error")
        return redirect(url_for('auth.list_users'))
        
    db = SessionLocal()
    user = db.query(User).get(user_id)
    if user:
        db.delete(user)
        db.commit()
        flash(f"User '{user.username}' deleted.", "success")
    else:
        flash("User not found.", "error")
    db.close()
    
    return redirect(url_for('auth.list_users'))

def init_auth(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        db = SessionLocal()
        user = db.query(User).get(int(user_id))
        db.close()
        if user:
            return AuthUser(user)
        return None
