"""
用户认证相关路由
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from .models import User, db
from . import login_manager

bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载器"""
    return User.query.get(int(user_id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # API登录
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            if request.is_json:
                return jsonify({'success': True, 'message': '登录成功'})
            flash('登录成功！', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # API注册
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
        
        # 验证
        errors = []
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            errors.append('用户名已被使用')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            errors.append('邮箱已被使用')
        
        # 密码确认
        if password != confirm_password:
            errors.append('两次输入的密码不一致')
        
        # 密码强度检查（简单示例）
        if len(password) < 6:
            errors.append('密码长度至少6位')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            for error in errors:
                flash(error, 'error')
        else:
            # 创建用户
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': '注册成功'})
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('main.index'))

@bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """注册API接口"""
    return register()

@bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """登录API接口"""
    return login()