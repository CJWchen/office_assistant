"""
应用配置
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {
        'excel': ['.xlsx', '.xls', '.csv'],
        'text': ['.txt', '.md', '.pdf', '.doc', '.docx'],
        'audio': ['.mp3', '.wav', '.m4a', '.ogg']
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'office_assistant_dev.db')

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'office_assistant.db')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}