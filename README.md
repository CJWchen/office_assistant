智能办公文档处理助手

基于 DeepSeek API 的 AI 办公自动化工具，提供 Excel 智能处理、PPT 自动生成、会议纪要摘要等功能。

功能特性

Excel 智能处理：数据清洗、趋势分析、可视化图表生成
PPT 自动生成：内容结构化、模板匹配、一键导出
会议纪要助手：语音转文字、关键信息提取、待办事项生成
用户系统：注册登录、文件管理、历史记录
响应式界面：Tailwind CSS 现代化设计，移动端友好

技术栈

后端：Python Flask + SQLAlchemy + Flask-Login
前端：HTML5 + Tailwind CSS + jQuery + FilePond
数据库：SQLite（开发）/ PostgreSQL（生产）
AI 集成：DeepSeek API
部署：Docker + Heroku + GitHub Pages

项目结构

plaintext
src/office_assistant/
├── app/                    # Flask 应用
│   ├── __init__.py        # 应用工厂
│   ├── models.py          # 数据库模型
│   ├── auth.py            # 用户认证
│   ├── upload.py          # 文件上传
│   └── main.py            # 主页面路由
├── static/                # 静态资源
│   └── uploads/           # 上传文件存储
├── templates/             # HTML 模板
│   ├── base.html          # 基础模板
│   ├── main/              # 主要页面
│   └── auth/              # 认证页面
├── instance/              # 实例文件夹
│   └── office_assistant.db # SQLite 数据库
├── config.py              # 配置文件
├── run.py                 # 启动脚本
└── requirements.txt       # Python 依赖


快速开始

1. 环境配置

bash
# 克隆项目
git clone <repository-url>
cd src/office_assistant

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt


2. 启动应用

bash
python run.py


应用将在 http://localhost:5000 启动。

3. 初始设置

访问 http://localhost:5000
点击"注册"创建新账户
登录后进入仪表板
上传文件开始使用 AI 办公工具

API 接口

状态检查

plaintext
GET /api/status


用户认证

plaintext
POST /api/auth/register
POST /api/auth/login


文件上传

plaintext
POST /api/upload


获取上传记录

plaintext
GET /api/uploads


开发计划

Day 1：项目基础搭建与用户系统 ✅

Flask 应用框架搭建
用户注册登录功能
文件上传基础功能

Day 2：Excel 智能处理模块

Excel 数据读取与清洗
AI 数据分析与趋势预测
图表可视化生成

Day 3：PPT 自动生成模块

PPT 模板管理
内容自动填充
导出功能实现

Day 4：会议纪要助手模块

音频文件处理
语音转文字集成
关键信息提取

Day 5：功能集成与部署优化

模块集成测试
Docker 容器化
生产环境部署

部署指南

Heroku 部署

bash
heroku create
git push heroku main


Docker 部署

bash
docker build -t office-assistant .
docker run -p 5000:5000 office-assistant


GitHub Pages 静态演示

bash
# 构建静态版本
python build_static.py
# 推送到 gh-pages 分支


许可证

MIT License

联系

如有问题或建议，请通过项目仓库提交 Issue。