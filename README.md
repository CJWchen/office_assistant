# 智能办公文档处理助手（Office Assistant）

基于 `DeepSeek API` 的 AI 办公自动化工具，提供 Excel 智能处理、PPT 自动生成、会议纪要摘要等能力。

## 功能特性

- Excel 智能处理：数据清洗、趋势分析、可视化图表生成
- PPT 自动生成：内容结构化、模板匹配、一键导出
- 会议纪要助手：语音转文字、关键信息提取、待办事项生成
- 用户系统：注册登录、文件管理、历史记录
- 响应式界面：现代化 Web 设计，移动端友好

## 技术栈

- 后端：Python + Flask + SQLAlchemy + Flask-Login
- 前端：HTML5 + Tailwind CSS + jQuery + FilePond
- 数据库：SQLite（开发）/ PostgreSQL（生产）
- AI 集成：DeepSeek API
- 部署：Docker / Heroku

## 项目结构

```text
office_assistant/
├── app/                        # Flask 应用
│   ├── __init__.py             # 应用工厂
│   ├── models.py               # 数据库模型
│   ├── auth.py                 # 用户认证
│   ├── upload.py               # 文件上传与预览
│   ├── main.py                 # 主页面与业务路由
│   ├── ppt_manager.py          # PPT 处理逻辑
│   ├── meeting_minutes.py      # 会议纪要处理
│   ├── data_cleaner.py         # 数据清洗模块
│   └── ai_analyzer.py          # AI 分析模块
├── static/                     # 静态资源
├── templates/                  # HTML 模板
│   ├── base.html
│   ├── auth/
│   └── main/
├── tests/                      # 测试代码
├── config.py                   # 配置文件
├── run.py                      # 启动脚本
└── requirements.txt            # Python 依赖
```

## 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd office_assistant

# 创建虚拟环境（可选但推荐）
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python run.py
```

默认访问地址：`http://127.0.0.1:5000`

### 3. 初始使用

1. 打开 `http://127.0.0.1:5000`
2. 点击“注册”创建账户
3. 登录后进入仪表板
4. 上传文件开始使用 AI 办公工具

## API 示例

### 状态检查

```http
GET /api/status
```

### 用户认证

```http
POST /api/auth/register
POST /api/auth/login
```

### 文件上传与记录

```http
POST /api/upload
GET /api/uploads
```

## 开发计划（原始里程碑）

- Day 1：项目基础搭建与用户系统
- Day 2：Excel 智能处理模块
- Day 3：PPT 自动生成模块
- Day 4：会议纪要助手模块
- Day 5：功能集成与部署优化

## 部署示例

### Heroku

```bash
heroku create
git push heroku main
```

### Docker

```bash
docker build -t office-assistant .
docker run -p 5000:5000 office-assistant
```

## 许可证

MIT License

## 联系

如有问题或建议，请通过仓库 `Issues` 提交反馈。
