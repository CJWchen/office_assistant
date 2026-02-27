"""
数据库模型定义
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    uploads = db.relationship('Upload', backref='user', lazy=True, cascade='all, delete-orphan')
    ppt_templates = db.relationship('PPTTemplate', backref='user', lazy=True, cascade='all, delete-orphan')
    ppt_projects = db.relationship('PPTProject', backref='user', lazy=True, cascade='all, delete-orphan')
    meeting_minutes = db.relationship('MeetingMinutes', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Upload(db.Model):
    """文件上传记录"""
    __tablename__ = 'uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # 字节
    file_type = db.Column(db.String(50), nullable=False)  # excel/text/audio
    upload_path = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Upload {self.original_filename}>'

class PPTTemplate(db.Model):
    """PPT模板模型"""
    __tablename__ = 'ppt_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # 商务、教育、创意等
    thumbnail_path = db.Column(db.String(500))  # 缩略图路径
    template_path = db.Column(db.String(500), nullable=False)  # 模板文件路径
    style_type = db.Column(db.String(20), nullable=False)  # 信息图风、插画科普风等
    color_scheme = db.Column(db.String(500))  # JSON格式的主题色系统
    tags = db.Column(db.String(500))  # 逗号分隔的标签
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)  # 是否公开
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PPTTemplate {self.name}>'

class PPTProject(db.Model):
    """PPT项目模型"""
    __tablename__ = 'ppt_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('ppt_templates.id'))
    content_data = db.Column(db.Text)  # JSON格式的内容数据
    generated_pptx_path = db.Column(db.String(500))  # 生成的PPTX文件路径
    generated_html_path = db.Column(db.String(500))  # 生成的HTML文件路径
    share_token = db.Column(db.String(100), unique=True)  # 分享令牌
    share_expires = db.Column(db.DateTime)  # 分享过期时间
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, generating, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PPTProject {self.title}>'

class MeetingMinutes(db.Model):
    """会议纪要模型"""
    __tablename__ = 'meeting_minutes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    original_file_id = db.Column(db.Integer, db.ForeignKey('uploads.id'))
    original_text = db.Column(db.Text)  # 原始文本内容
    summary = db.Column(db.Text)  # 结构化摘要文本
    structured_data = db.Column(db.Text)  # JSON格式的结构化数据（问题、讨论、决议等）
    todo_items = db.Column(db.Text)  # JSON格式的待办事项列表
    timeline_data = db.Column(db.Text)  # JSON格式的时间线数据
    language = db.Column(db.String(10), default='zh')  # 语言：zh, en等
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    original_file = db.relationship('Upload', foreign_keys=[original_file_id])
    
    def __repr__(self):
        return f'<MeetingMinutes {self.title}>'

class TodoItem(db.Model):
    """待办事项模型（独立存储，便于跟踪）"""
    __tablename__ = 'todo_items'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_minutes_id = db.Column(db.Integer, db.ForeignKey('meeting_minutes.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    assignee = db.Column(db.String(100))  # 责任人
    priority = db.Column(db.Integer, default=1)  # 优先级：1-低，2-中，3-高
    due_date = db.Column(db.DateTime)  # 截止日期
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    meeting_minutes = db.relationship('MeetingMinutes', foreign_keys=[meeting_minutes_id])
    
    def __repr__(self):
        return f'<TodoItem {self.description[:50]}>'