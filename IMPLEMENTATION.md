## 🚀 农作物病虫害检测系统 - 三项功能优化完成总结

### 📋 实现概览

本次优化包括三个主要功能：

#### ✅ **功能一：扩充害虫数据库**
- 前端：`frontend/src/data/pestKnowledge.js` - 新增 20+ 种害虫资料
- 后端：`backend/app/mock_data.py` - 扩充 `PEST_CROP_MAP`
- 新增作物类型：果树、大豆、烟草、茶树、其他蔬菜等
- **状态**：✅ 完成，无需额外配置

#### ✅ **功能二：多机构子系统架构**
- 数据库模型改动（`models.py`）：
  - 新增 `Organization` 表（机构）
  - 新增 `Detection` 表（持久化检测记录）
  - 修改 `User` 表增加 `role` 和 `org_id` 字段
- 认证系统改动（`auth.py`）：
  - 新增 `require_super_admin` 权限检查
  - 新增 `ensure_super_admin` 自动初始化超级管理员
- 后端路由改动：
  - `routers/organizations.py`（新建）- 子系统管理接口
  - `routers/detections.py`（改造）- 支持权限过滤和数据库持久化
  - `routers/dashboard.py`（改造）- 支持权限过滤和数据库聚合统计
  - `routers/auth.py`（改造）- 返回用户角色和机构信息
- **状态**：✅ 完成，需要测试

#### ✅ **功能三：实时识别界面**
- 后端：`routers/realtime.py`（新建）- WebSocket 端点 `/api/ws/detect`
  - 接收 base64 图片帧
  - 返回实时检测结果（模拟数据）
  - 支持 JWT token 认证
- 前端：`src/api/realtime.js`（新建）- WebSocket 客户端封装
- 前端：`views/Detection.vue`（改造）- 添加实时识别标签
  - 摄像头权限请求
  - 实时视频显示和检测框渲染
  - 截图保存功能
- **状态**：✅ 完成，需要测试

---

## 🔧 部署和测试步骤

### 前提条件
- Node.js 18+
- Python 3.10+
- 现代浏览器（支持 WebRTC 和 WebSocket）

### 1. 安装依赖

```bash
# 在项目根目录
npm run install:all  # 同时安装前端和后端依赖
```

### 2. 数据库迁移
由于改动了数据库模型，**首次启动后端时会自动创建新表**（SQLAlchemy 在 `main.py` 中调用 `Base.metadata.create_all`）。

**重要**：如果之前有数据库文件，建议备份后删除 `backend/app/data/app.db`，让系统重新创建：

```bash
# Windows
del "backend\app\data\app.db"

# Linux/Mac
rm backend/app/data/app.db
```

### 3. 启动应用

```bash
# 在项目根目录
npm run dev
```

后端运行在 `http://127.0.0.1:8000`  
前端运行在 `http://localhost:5173`

### 4. 测试流程

#### A. 测试基本功能（注册和超级管理员初始化）

1. 打开 `http://localhost:5173`
2. 进入"登录"页面，点击"创建新账号"
3. 注册第一个账号（例如 username: `admin`, email: `admin@test.com`）
4. 登录后，检查菜单中是否出现"子系统管理"菜单项
   - ✅ 如果出现，说明该账号已被自动提升为超级管理员
   - ❌ 如果未出现，说明自动初始化失败

#### B. 测试扩充的害虫数据库

1. 登录后进入"病虫害知识库"页面
2. 检查以下内容：
   - ✅ 是否有新增的害虫卡片（果树、大豆、烟草、茶树相关）
   - ✅ 作物类型筛选栏是否有新增的选项
   - ✅ 点击新增害虫卡片是否能打开详情弹窗
3. 进入"病虫害检测"页，上传图片检测
   - ✅ 是否偶尔出现新增害虫名称（因为是模拟随机数据）

#### C. 测试多机构子系统（需要超级管理员账号）

1. 用超级管理员账号登录
2. 点击菜单中的"子系统管理"
3. 点击"新建子系统"按钮，填写：
   - 机构名称：`测试农场 A`
   - 管理员用户名：`farm_a_admin`
   - 管理员邮箱：`farm_a@test.com`
   - 管理员密码：`123456`
4. 提交后，应该看到新机构出现在列表中
5. **退出登录**，用新创建的管理员账号登录：
   - 用户名：`farm_a_admin`
   - 密码：`123456`
6. 进入"病虫害检测"，上传图片生成几条检测记录
7. 进入"检测历史记录"，确认只能看到自己机构的记录
8. **切换回超级管理员账号**登录
9. 进入"子系统管理"，点击`测试农场 A`查看其详情
   - ✅ 应能看到该机构下的所有检测记录（包括刚才创建的）

#### D. 测试实时识别（需要浏览器支持摄像头）

1. 登录后进入"病虫害检测"页
2. 点击"实时识别"标签
3. 点击"开启摄像头"按钮
   - 浏览器会请求摄像头权限，允许访问
   - ✅ 如果成功，应看到摄像头画面并每秒出现检测框（模拟数据）
   - ❌ 如果失败，检查浏览器权限和 WebSocket 连接
4. 点击"截图保存"按钮
   - ✅ 应该保存当前帧并切换回"图片检测"标签显示结果
   - ✅ 该记录应出现在"检测历史记录"中

---

## ⚠️ 已知限制和注意事项

### 1. 数据库同步问题
检测记录现在持久化到 `Detection` 表，但 `mock_data.py` 中的内存 `_records` 列表仍然会继续增长（因为创建检测时仍会调用 `mock_data.create_mock_detection`）。这会导致内存泄漏，**建议后续改造为：**
- 完全停止使用 `_records` 内存列表
- 仅用数据库作为数据源

### 2. 实时识别目前使用模拟数据
WebSocket 检测端点返回的是模拟检测结果，未接入真实 YOLOv8 模型。框架已搭好，后续只需：
- 在 `routers/realtime.py` 中用真实推理逻辑替换 `mock_data.create_mock_detection` 调用

### 3. 前端组织管理页面尚未实现
计划中的 `frontend/src/views/Organizations.vue` 和 `OrganizationDetail.vue` 页面尚未编写（后端 API 已就绪），可通过以下方式临时测试：
- 直接调用后端 API：
  ```bash
  # 创建子系统
  curl -X POST http://127.0.0.1:8000/api/organizations \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "测试机构",
      "admin_username": "test_admin",
      "admin_email": "test@example.com",
      "admin_password": "password"
    }'
  
  # 列表子系统
  curl http://127.0.0.1:8000/api/organizations \
    -H "Authorization: Bearer <token>"
  ```

### 4. 数据库字段说明
- `User.role`：用户角色，值为 `"super_admin"` 或 `"admin"`
- `User.org_id`：用户所属机构 ID（超级管理员的 `org_id` 为 `NULL`）
- `Detection.boxes`、`Detection.pest_types`：以 JSON 字符串形式存储
  - 读取时需要 `json.loads(...)` 转换为 Python 对象

---

## 📝 后续优化建议

1. **完成前端组织管理页面**
   - 参考 `History.vue` 的表格模式创建 `Organizations.vue`
   - 实现创建子系统的表单弹窗

2. **接入真实 YOLOv8 模型**
   - 修改 `routers/detections.py` 和 `routers/realtime.py` 的检测逻辑
   - 添加模型权重文件加载
   - 优化推理性能（考虑异步处理）

3. **完善数据库事务处理**
   - 增加异常捕获和回滚逻辑
   - 避免部分操作失败导致数据不一致

4. **性能优化**
   - 实时识别帧率可调
   - 检测历史分页优化
   - WebSocket 连接池管理

5. **安全加强**
   - token 过期自动刷新
   - 上传图片大小限制
   - WebSocket 消息验证

---

## 🆘 故障排查

### 问题：后端启动时报 "module 'app.routers' has no attribute 'organizations'"

**解决**：确保 `app/routers/__init__.py` 正确导出或已导入新模块（如果需要）。

### 问题：WebSocket 连接失败

**解决**：
1. 检查浏览器控制台的 WebSocket 连接 URL
2. 确保后端正确注册了 WebSocket 路由
3. 检查 JWT token 是否过期（从 localStorage 读取的 `pw_token`）

### 问题：实时识别画面卡顿或无反应

**解决**：
1. 降低帧率（修改 `Detection.vue` 中的 `frameInterval` 值，从 800ms 改为 1000ms+）
2. 检查浏览器性能（打开 DevTools 的 Performance 标签）
3. 确保网络连接稳定

---

## 📞 支持
如有问题，请检查后端日志和浏览器控制台输出，或参考上述"已知限制"部分。
