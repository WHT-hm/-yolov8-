# 农作物病虫害检测系统（pipeline-widget）

基于 Vue 3 + Element Plus + FastAPI 的农作物病虫害检测演示系统，包含用户注册登录、图片 / 实时摄像头检测、数据统计仪表盘、病虫害知识库、个人中心与多主题切换等功能。

## 技术栈

- **前端**：Vue 3（`<script setup>`）+ Vite + Element Plus + Vue Router + Axios + ECharts
- **后端**：FastAPI + SQLAlchemy（SQLite）+ JWT 鉴权 + WebSocket

## 目录结构

```
pipeline-widget/
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── routers/        # 各功能路由（auth / settings / detections / dashboard / meta / organizations / realtime）
│   │   ├── models.py       # 数据库模型（用户、机构、用户设置、检测记录）
│   │   ├── auth.py         # 密码哈希、JWT 签发校验、权限依赖
│   │   ├── mock_data.py    # 模拟检测结果生成（尚未接入真实 YOLOv8 推理）
│   │   ├── database.py     # SQLite 连接配置
│   │   └── data/           # 运行时生成的数据库文件（已加入 .gitignore）
│   └── static/uploads/     # 检测图片上传目录（已加入 .gitignore）
└── frontend/            # Vue 3 前端
    └── src/
        ├── views/           # 页面：首页 / 仪表盘 / 检测 / 历史 / 知识库 / 登录 / 个人中心 / 设置
        ├── components/      # 通用组件（全局搜索等）
        ├── api/             # 后端接口封装（auth / detection / realtime / settings / dashboard）
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

- **注册 / 登录**：真实账号体系，密码使用 bcrypt 哈希存储，登录状态通过 JWT 维护（`Authorization: Bearer <token>`）。首个注册用户会被自动提升为超级管理员（`super_admin`）。
- **首页**：项目入口与导航概览。
- **病虫害检测**：
  - *图片检测*：上传图片、可选指定作物类型，返回病虫害种类、严重程度、平均置信度等模拟检测结果。
  - *实时摄像头检测*（在"设置"页中开启）：通过浏览器摄像头采集帧，经 WebSocket（`/api/ws/detect`）发送到后端，实时返回检测框与识别结果，并在视频画面上叠加绘制。
  - 当前检测结果均为模拟数据（`backend/app/mock_data.py`），尚未接入真实的 YOLOv8 模型推理。
- **数据统计仪表盘**：基于 ECharts 展示病虫害种类分布、严重程度分布、近 7 天检测趋势、各病虫害受害程度排行、受害部位分布等图表。
- **检测历史记录**：查看、检索历史检测记录。
- **病虫害知识库**：常见农作物病虫害的图文知识条目，支持全局搜索（同时检索检测记录与知识库）。
- **个人中心**：查看与修改用户名 / 邮箱，修改密码。
- **设置**：
  - 模型接口设置：配置你自己的 AI 模型接口地址、API Key、模型名称，并可通过"测试连接"验证接口是否可达。
  - 实时摄像头检测（默认折叠）：详见上方"病虫害检测"说明。
  - 外观设置：在森林绿 / 海洋蓝 / 皇家紫 / 日落橙四套配色主题间切换，实时生效并保存。
- **多主题**：基于 CSS 变量 + `data-theme` 属性实现，切换主题会同步更新侧边栏、强调色、Element Plus 组件配色。
- **多机构管理（后端 API，暂无前端页面）**：`backend/app/routers/organizations.py` 提供机构（子系统）创建、列表与按机构查询检测记录的接口，仅限超级管理员调用，用于支撑未来的多租户场景。

## 数据存储说明

用户账号、机构、用户设置与检测记录保存在 SQLite 文件 `backend/app/data/app.db` 中，该文件不会被提交到 Git（详见 `.gitignore`）。首次启动后端时会自动创建数据库和数据表。

## 注意事项

- `backend/app/auth.py` 中的 JWT 密钥（`SECRET_KEY`）是写死的开发用密钥，仅适用于本地学习环境，**不要**在生产环境中直接使用。
- 检测功能（图片检测与实时摄像头检测）目前返回的都是模拟结果（尚未接入真实的 YOLOv8 推理），详见 `backend/app/mock_data.py` 中的注释。
- 实时摄像头检测需要浏览器摄像头权限，请在浏览器权限弹窗中允许访问。
