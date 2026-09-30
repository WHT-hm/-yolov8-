# 开发笔记

本文件汇总项目当前已知的限制、待办事项和素材缺口，替代此前散落的
`FIXES_AND_WORKAROUNDS.md`、`IMAGE_DOWNLOAD_GUIDE.md`、`IMAGE_STATUS_REPORT.md`、
`IMPLEMENTATION.md` 四份文档。功能与技术栈说明见 [README.md](./README.md)。

## 已知限制

- **检测结果为模拟数据**：图片检测与实时摄像头检测目前都调用
  `backend/app/mock_data.py` 生成随机结果，尚未接入真实 YOLOv8 推理。
- **内存记录未清理**：`mock_data.py` 中的内存 `_records` 列表会随检测次数持续增长，
  检测记录的持久化已迁移到数据库 `Detection` 表，`_records` 已无实际用途，后续可移除。
- **机构管理无前端页面**：`backend/app/routers/organizations.py` 已提供机构创建 /
  查询 API（仅限超级管理员），但 `frontend/src/views/Organizations.vue` 尚未实现，
  目前只能通过直接调用 API 测试（见下方"机构管理 API 示例"）。
- **JWT 密钥为开发用固定值**：写在 `backend/app/auth.py` 中，仅适用于本地学习环境，
  不要在生产环境直接使用。

## 后续优化建议

- [ ] 实现前端"机构管理"页面（可参考 `History.vue` 的表格模式）
- [ ] 接入真实 YOLOv8 模型，替换 `detections.py` / `realtime.py` 中的模拟推理逻辑
- [ ] 移除 `mock_data.py` 中不再需要的内存 `_records` 列表
- [ ] 数据库事务补充异常捕获与回滚
- [ ] 实时识别帧率自适应、WebSocket 连接池管理
- [ ] 上传图片大小限制、WebSocket 消息校验、token 过期自动刷新

## 病虫害图片素材状态

`frontend/src/data/pestKnowledge.js` 中共登记 30 种病虫害，图片文件存放于
`frontend/public/pest-images/`。截至目前，以下条目引用的图片文件**尚未下载**，
页面上会显示占位样式：

| 中文名 | 学名 | 文件名 | 参考来源 |
|---|---|---|---|
| 介壳虫 | Icerya purchasi | `icerya-purchasi.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Scale_insects_(7244837120).jpg) |
| 豆秆蝇 | Melanagromyza sojae | `melanagromyza-sojae.jpg` | [iNaturalist](https://www.inaturalist.org/taxa/403948) |
| 豆天蛾 | Theretra oldenlandiae | `theretra-oldenlandiae.jpg` | [iNaturalist](https://www.inaturalist.org/taxa/125110-Theretra-oldenlandiae) |
| 烟青虫 | Heliothis virescens | `heliothis-virescens.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Heliothis_virescens_%E2%80%93_Tobacco_Budworm_Moth_(14513506849).jpg) |
| 烟草天蛾 | Manduca sexta | `manduca-sexta.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Tobacco_Hornworm_1.jpg) |
| 烟蚜 | Myzus nicotianae | `myzus-nicotianae.jpg` | [Bugwood.org](https://www.invasive.org/browse/image/1402116) |
| 茶毛虫 | Euproctis pseudoconspersa | `euproctis-pseudoconspersa.jpg` | [iNaturalist](https://www.inaturalist.org/taxa/924893-Euproctis) |
| 茶尺蠖 | Ectropis obliqua | `ectropis-obliqua.jpg` | [iNaturalist](https://www.inaturalist.org/taxa/924893-Ectropis-obliqua) |
| 茶叶蝉 | Empoasca flavescens | `empoasca-flavescens.jpg` | [iNaturalist](https://www.inaturalist.org/taxa/173635-Empoasca) |
| 稻飞虱若虫 | Nilaparvata lugens | `nilaparvata-lugens-nymph.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg) |
| 小麦吸浆虫 | Sitodiplosis mosellana | `sitodiplosis-mosellana.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Hessian_Fly.jpg) |
| 小麦纹枯病虫 | Rhizoctonia cerealis | `rhizoctonia-cerealis.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Sharp_eyespot_of_wheat.jpg) |
| 棉盲蝽 | Adelphocoris lineolatus | `adelphocoris-lineolatus.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Noorwijk_-_Luzernesierblindwants_(Adelphocoris_lineolatus).jpg) |
| 棉蚜 | Aphis gossypii | `aphis-gossypii.jpg` | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:CSIRO_ScienceImage_7331_Aphids_on_cotton.jpg) |

下载方法：打开来源链接，选择清晰的图片，右键"图片另存为"，
以上表文件名保存到 `frontend/public/pest-images/`（区分大小写）。
图片建议 200×200 像素以上、50–300 KB，使用知识共享（CC）或公共领域授权的素材。

> 注：`rhizoctonia-cerealis`（小麦纹枯病）实际是真菌病害而非昆虫，图片仅作占位说明。

## 机构管理 API 示例

前端页面未实现前，可直接调用后端接口验证多机构逻辑（需超级管理员 token）：

```bash
# 创建子机构
curl -X POST http://127.0.0.1:8000/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "测试农场 A",
    "admin_username": "farm_a_admin",
    "admin_email": "farm_a@example.com",
    "admin_password": "123456"
  }'

# 列出所有子机构
curl http://127.0.0.1:8000/api/organizations \
  -H "Authorization: Bearer $TOKEN"

# 查看指定机构的检测记录
curl "http://127.0.0.1:8000/api/organizations/1/detections?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

## 故障排查

- **后端启动报 `module 'app.routers' has no attribute 'organizations'`**：
  确认 `app/routers/__init__.py` 已正确导入新增的路由模块。
- **WebSocket 连接失败**：检查浏览器控制台中的连接地址、后端是否已注册
  WebSocket 路由，以及 `localStorage` 中的 `pw_token` 是否过期。
- **实时识别画面卡顿**：调低 `Detection.vue` 中的 `frameInterval`（提高间隔毫秒数），
  并检查网络与浏览器性能。
- **置信度显示异常（如超过 100%）**：确认 `models.py` 的 `to_dict()`
  与 `routers/detections.py` 中的百分比换算逻辑一致，必要时删除本地
  `backend/app/data/app.db` 后重新启动，让数据库重建。
