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
│   │   ├── judgment_model.py  # JEV 判断模型客户端：自动复核 YOLO 检测结果，见下方说明
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

## 判断模型接入设计（Judgment Model / Jev）

项目接入了一个可插拔的"判断模型"客户端（`backend/app/judgment_model.py`），
用 TypeSafe AI 的 Jev（"System One" 判断模型）对检测结果做自动复核。设计上
把"YOLO 这次识别得准不准"抽象成对一组**类型化问题**（Choice / Score / Noul）
的并行判断，而不是自由文本生成式调用：一次请求传入 `state`（待判断的上下文）
和若干 `questions`，模型并行给出带置信度的结构化答案。

### 自动检测流程：用户输入 → YOLOv8 检测 → JEV 复核 → 结果输出

`POST /api/detections`（图片检测接口）就是按这四个阶段串起来的，**全自动、
无需额外调用**：

```
用户输入（上传图片 + 可选作物类型）
        │
        ▼
YOLOv8 检测（backend/app/routers/detections.py::create_detection，
             当前由 mock_data.create_mock_detection 占位，
             产出 pest_types / severity / avg_confidence / boxes）
        │
        ▼
JEV 复核（judgment_model.judge_yolo_result，见下方"判断结构"；
         若未在设置页配置判断模型接口，或调用失败，自动跳过本步，
         不影响检测结果返回）
        │
        ▼
结果输出（DetectionRecord：YOLO 检测字段保持不变，
         JEV 的复核结论写入 remark 一并返回并持久化）
```

对应代码位置：`backend/app/routers/detections.py` 的 `create_detection()`，
三步分别标注了"第一步：YOLOv8 检测""第二步：JEV 判断模型自动复核"
"第三步：结果输出"三段注释，便于对照。

关键设计取舍是**复核不改写检测结果**：JEV 只对 YOLO 已经给出的识别结果做
"是否可信"的第二意见判断，不会反过来修改 `pest_types` / `severity` /
`avg_confidence`——避免了"两个模型谁说了算"的冲突，也让"检测"和"复核"
职责清晰分开。

如果某条记录是在判断模型配置好之前创建的、或想拿到一次新的复核意见，可以
调用 `POST /api/judgment/detections/{detection_id}/verify` 手动重新触发一次
复核（见下方"判断模型相关路由"）。

### 判断结构

JEV 扮演的是"第二意见"角色：YOLO（目前由 `mock_data` 占位，接入真实
YOLOv8 后同样适用）先给出一个候选识别结果（pest_name + confidence），
再把它连同图片上下文交给 JEV，并行问三个类型化问题：

| 问题 key | 类型 | 作用 |
|---|---|---|
| `result_plausible` | Noul（是非概率） | YOLO 识别出的具体种类本身站不站得住脚，与"置信度数值是否可信"分开判断 |
| `confidence_alignment` | Score（三档：明显不符 / 大致相符 / 高度吻合） | YOLO 报出的置信度数值，是否与图片证据的清晰程度相符——用于发现"模型对某些类别系统性过度自信"这类比单纯识别错类更隐蔽的问题 |
| `likely_alternative` | Choice（候选集按 `crop_type` 过滤，且排除 YOLO 已选中的类别） | 仅当 `result_plausible` 判定为不可信时才有业务意义，但与另外两个问题一起并行问出，避免"先判断是否可信、再决定要不要问替代项"这种需要两次往返的串行调用 |

对应函数：`build_yolo_verification_questions()` 构造问题、
`judge_yolo_result()` 是调用入口（均在 `backend/app/judgment_model.py`）。

设计上的优化点：
- **一次调用、并行回答**：三个问题合并成一次请求，而非三次串行调用，减少往返延迟。
- **用已知信息收窄候选集**：`likely_alternative` 的选项按作物类型过滤，而不是让模型在全量病虫害列表中选择。
- **"是否可信"与"置信度是否校准"分开判断**：避免把两种不同的不确定性来源混在一个问题里。
- **复核不等于改写**：`judge_yolo_result` 返回的 `YoloVerificationResult` 只给出"是否可信 / 置信度校准程度 / 建议的替代项"，调用方将其作为旁路信息写入 `DetectionRecord.remark`，提示需要人工复核，而不是直接覆盖 YOLO 的原始输出。
- **职责边界**：判断模型只对 YOLO 已给出的 `pest_types` / `avg_confidence` 做复核；检测框坐标（`boxes`，像素级定位）始终由 `mock_data`（未来是真实 YOLOv8）生成，因为 Jev 这类判断模型不具备目标检测模型的定位能力。
- **失败不阻塞**：未配置判断模型接口，或请求/响应出现任何异常，`judge_yolo_result` 都返回 `None`，调用方按"未复核"处理——复核是增强，不是检测流程的前提。

### 判断结果 → 业务结论

三个类型化问题的答案最终被归纳成一句话，直接写入 `DetectionRecord.remark`：

```python
if is_plausible:
    note = "判断模型复核：识别结果可信（置信度校准：{alignment}）"
else:
    note = ("判断模型复核：对「{predicted_pest}」持怀疑态度（置信度校准：{alignment}），"
            "更可能是「{alternative}」，建议人工复核")
```

### 代码落点速查

| 文件 | 内容 |
|---|---|
| `backend/app/judgment_model.py` | `JudgmentModelClient`（通用调用）+ `build_yolo_verification_questions` / `judge_yolo_result`（本场景判断结构） |
| `backend/app/routers/detections.py` | `create_detection()` 中自动触发复核（流水线第二步） |
| `backend/app/routers/judgment.py` | `GET /api/judgment/status`（是否已配置）、`POST /api/judgment/detections/{id}/verify`（手动重新触发） |

### 复用现有接口，零新增配置

本接口**复用**了"设置"页已有的模型接口配置（`UserSettings.api_base_url` /
`api_key` / `model_name`），不新增数据库字段或前端页面。用户在设置页把
`api_base_url` 填成 Jev 服务根地址（如 `https://api.typesafe.ai`）后，
`POST /api/detections` 就会自动触发复核；只要未配置、网络失败、响应格式
不符合预期等任何一种情况，都会**静默跳过**，不影响检测功能本身的可用性。

### 判断模型相关路由

`backend/app/routers/judgment.py`（前缀 `/api/judgment`）：

| 路由 | 方法 | 作用 |
|---|---|---|
| `/api/judgment/status` | `GET` | 查询当前用户是否已配置判断模型接口，供前端决定是否展示复核相关 UI |
| `/api/judgment/detections/{detection_id}/verify` | `POST` | 对指定检测记录**手动重新触发**一次 JEV 复核（例如记录创建于判断模型配置之前），结论同样写入该记录的 `remark` |

### 已对照官方文档确认的接口契约

已核对 [docs.typesafe.ai/introduction/quickstart](https://docs.typesafe.ai/introduction/quickstart)
与 [docs.typesafe.ai/primitives](https://docs.typesafe.ai/primitives)（2026-10 访问）：

- 端点固定为 `POST {api_base_url}/v1/systemone`，鉴权用 `Authorization: Bearer <api_key>`；
  设置页的 `api_base_url` 应填 Jev 服务根地址（如 `https://api.typesafe.ai`）。
- 请求体：`{"model", "state", "questions": {key: {"type", "instructions", "criteria"}}}`。
  `choice` 的 `criteria` 是"选项名 → 说明"字典；`score` 的 `criteria` 是按顺序排列的
  等级说明数组；`noul` 的 `criteria` 是可选的澄清字符串（不是字典）。
- 响应体：`{"model", "answers": {...}, "usage"}`。`choice` 返回 `choice` /
  `confidence` / `probabilities`；`score` 返回的 `score` 是等级区间上的**数值位置**
  （可能落在两个等级之间，不是等级文本本身），需配合 `legend` 或自行按发送顺序
  四舍五入取最近等级；`noul` 只返回 `noul`（0~1 概率），没有 `confidence` 字段。
  `judgment_model.py` 中的 `_build_payload` / `_parse_response` 已按此实现。

## 数据存储说明

用户账号、机构、用户设置与检测记录保存在 SQLite 文件 `backend/app/data/app.db` 中，该文件不会被提交到 Git（详见 `.gitignore`）。首次启动后端时会自动创建数据库和数据表。

## 注意事项

- `backend/app/auth.py` 中的 JWT 密钥（`SECRET_KEY`）是写死的开发用密钥，仅适用于本地学习环境，**不要**在生产环境中直接使用。
- 检测功能（图片检测与实时摄像头检测）默认返回模拟结果（尚未接入真实的 YOLOv8 推理），详见 `backend/app/mock_data.py` 中的注释；若在设置页配置了判断模型接口，图片检测会在 YOLO（当前为模拟）产出结果后自动触发一次 JEV 复核，详见下方"判断模型接入设计"。
- 实时摄像头检测需要浏览器摄像头权限，请在浏览器权限弹窗中允许访问。

已知限制、待办事项与病虫害图片素材缺口，见 [NOTES.md](./NOTES.md)。
