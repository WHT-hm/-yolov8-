## 🔧 问题修复指南

### 问题 1: 平均置信度显示 7000%

**原因**：存储和返回逻辑中的数据格式转换错误

**修复已应用**：
- ✅ 已更新 `backend/app/routers/detections.py`
- ✅ 已确保 `models.py` 中的 `to_dict()` 正确转换百分比

**需要做的**：
1. 停止当前后端进程
2. 删除 `backend/app/data/app.db` （需要先释放进程锁）
3. 重新启动后端

**临时修复**（如果无法删除数据库）：
在前端 Detection.vue 中，如果看到超过 100 的置信度，自动除以 100：
```javascript
const displayConfidence = (confidence) => {
  if (confidence > 100) return (confidence / 100).toFixed(0)
  return (confidence * 100).toFixed(0)
}
```

---

### 问题 2: 摄像头配置界面 ✅

**已完成修复**：
- ✅ 添加了"实时识别配置"界面（无需自动打开摄像头）
- ✅ 用户现在需要：
  1. 在配置面板中启用摄像头
  2. 允许浏览器权限请求
  3. 点击"开启摄像头"按钮

**新功能**：
- 可配置识别间隔（300-5000ms）
- 可随时修改配置或关闭摄像头

---

### 问题 3: 超级管理员查看其他用户的记录

**原因**：前端界面还未实现"子系统管理"页面

**解决方案**：

#### 方式 A：通过 API 直接查看（现在可用）

```bash
# 1. 先登录获取 token
TOKEN=$(curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test123456"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 2. 列出所有子系统
curl http://127.0.0.1:8000/api/organizations \
  -H "Authorization: Bearer $TOKEN"

# 3. 查看特定子系统的检测记录
curl "http://127.0.0.1:8000/api/organizations/1/detections?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 方式 B：快速前端修复

在 `frontend/src/layout/MainLayout.vue` 中添加"子系统管理"菜单项（临时）：

```javascript
// 在 menuItems 数组中添加
{
  path: '/admin/organizations',
  label: '子系统管理',
  icon: 'Management',
  color: 'var(--accent-settings)',
  hidden: currentUser.value?.role !== 'super_admin'
}
```

---

## 📋 立即测试这些修复

### 测试 1：创建子系统并验证权限

```bash
# 用 testuser（超级管理员）创建新子系统
ADMIN_TOKEN="<testuser的token>"

curl -X POST http://127.0.0.1:8000/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "name": "农场 B",
    "admin_username": "farm_b_admin",
    "admin_email": "farm_b@example.com",
    "admin_password": "123456"
  }'

# 应该返回新建的子系统信息
```

### 测试 2：用子系统管理员上传图片

```bash
# 用新创建的管理员账号登录并上传图片
# 应该在该子系统的检测记录中看到该图片
```

### 测试 3：超级管理员查看所有记录

```bash
# 用超级管理员账号查询该子系统的记录
curl "http://127.0.0.1:8000/api/organizations/2/detections" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 应该看到该子系统管理员上传的所有图片
```

---

## 🎯 后续优化待办

- [ ] 完整的前端"子系统管理"页面
- [ ] 数据库性能优化（大数据量查询）
- [ ] WebSocket 连接池管理
- [ ] 实时识别帧率自适应

