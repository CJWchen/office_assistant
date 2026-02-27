"""
智能办公文档处理助手 - Flask应用工厂
"""

import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 扩展实例
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=None):
    """应用工厂函数"""
    app = Flask(
        __name__,
        template_folder=os.path.join('..', 'templates'),
        static_folder=os.path.join('..', 'static')
    )
    
    # 配置
    if config_class:
        app.config.from_object(config_class)
    else:
        # 默认配置
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(app.instance_path, 'office_assistant.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '..', 'static', 'uploads')
        app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
        app.config['ALLOWED_EXTENSIONS'] = {
            'excel': ['.xlsx', '.xls', '.csv'],
            'text': ['.txt', '.md', '.pdf', '.doc', '.docx'],
            'audio': ['.mp3', '.wav', '.m4a'],
            'ppt': ['.pptx', '.ppt']
        }
        
        # PPT生成相关配置
        app.config['UNSPLASH_ACCESS_KEY'] = os.environ.get('UNSPLASH_ACCESS_KEY') or ''
        app.config['DEEPSEEK_API_KEY'] = os.environ.get('DEEPSEEK_API_KEY') or ''
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # 配置登录视图
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面'
    login_manager.login_message_category = 'info'
    
    # 注册蓝图
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .upload import bp as upload_bp
    app.register_blueprint(upload_bp, url_prefix='/api')
    
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # 导入模型（确保SQLAlchemy知道它们）
    from . import models
    
    # 创建数据库表（开发环境）
    with app.app_context():
        db.create_all()
    
    return app
