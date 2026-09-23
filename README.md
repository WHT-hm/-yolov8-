# 农作物病虫害检测系统（pipeline-widget）

基于 Vue 3 + Element Plus + FastAPI 的农作物病虫害检测演示系统，包含用户注册登录、个人中心、模型接口设置与多主题切换等功能。

## 技术栈

- **前端**：Vue 3（`<script setup>`）+ Vite + Element Plus + Vue Router + Axios + ECharts
- **后端**：FastAPI + SQLAlchemy（SQLite）+ JWT 鉴权

## 目录结构

```
pipeline-widget/
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── routers/        # 各功能路由（auth / settings / detections / dashboard / meta）
│   │   ├── models.py       # 数据库模型（用户、用户设置）
│   │   ├── database.py     # SQLite 连接配置
│   │   └── data/            # 运行时生成的数据库文件（已加入 .gitignore）
│   └── static/uploads/     # 检测图片上传目录（已加入 .gitignore）
└── frontend/            # Vue 3 前端
    └── src/
        ├── views/           # 页面：首页 / 检测 / 历史 / 知识库 / 登录 / 个人中心 / 设置
        ├── store/           # 登录状态与主题状态
        ├── styles/          # 全局样式与多主题配色
        └── router/          # 路由与登录守卫
```

## 环境要求

- Node.js 18+
- Python 3.10+

## 快速开始（推荐：一条命令同时启动前后端）

首次使用需要先安装依赖：

```bash
npm run install:all
```

这条命令会依次安装根目录、`frontend/`、`backend/` 的依赖（后端依赖通过 `pip install -r backend/requirements.txt` 安装）。

安装完成后，在项目根目录运行：

```bash
npm run dev
```

会同时启动：
- 后端：`http://127.0.0.1:8000`
- 前端：`http://localhost:5173`

终端会用不同颜色区分 `[backend]` 和 `[frontend]` 的日志，按 `Ctrl + C` 可以同时停止两者。

## 手动分别启动（可选）

如果想在两个独立终端窗口分别查看日志，也可以手动启动：

```bash
# 终端 1：后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# 终端 2：前端
cd frontend
npm install
npm run dev
```

## 功能说明

- **注册 / 登录**：真实账号体系，密码使用 bcrypt 哈希存储，登录状态通过 JWT 维护（`Authorization: Bearer <token>`）。
- **个人中心**：查看与修改用户名 / 邮箱，修改密码。
- **设置**：
  - 模型接口设置：配置你自己的 AI 模型接口地址、API Key、模型名称，并可通过"测试连接"验证接口是否可达。
  - 外观设置：在森林绿 / 海洋蓝 / 皇家紫 / 日落橙四套配色主题间切换，实时生效并保存。
- **多主题**：基于 CSS 变量 + `data-theme` 属性实现，切换主题会同步更新侧边栏、强调色、Element Plus 组件配色。

## 数据存储说明

用户账号与设置保存在 SQLite 文件 `backend/app/data/app.db` 中，该文件不会被提交到 Git（详见 `.gitignore`）。首次启动后端时会自动创建数据库和数据表。

## 注意事项

- `backend/app/auth.py` 中的 JWT 密钥（`SECRET_KEY`）是写死的开发用密钥，仅适用于本地学习环境，**不要**在生产环境中直接使用。
- 检测功能目前返回的是模拟结果（尚未接入真实的 YOLOv8 推理），详见 `backend/app/mock_data.py` 中的注释。
