"""实时视频检测 WebSocket 接口"""
import base64
import json
from io import BytesIO

from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
from PIL import Image

from .. import auth, mock_data

router = APIRouter(prefix="/api/ws", tags=["realtime"])


@router.websocket("/detect")
async def websocket_detect(
    websocket: WebSocket,
    token: str = Query(None),
):
    """
    WebSocket 实时检测端点
    客户端发送 base64 编码的图片帧，服务端返回检测框坐标

    连接参数：
    - token: JWT token（放在查询参数中，因为 WebSocket 无法自定义 Header）

    客户端消息格式：
    {
        "type": "frame",
        "image": "data:image/jpeg;base64,...",  // base64 编码的图片
        "crop_type": "水稻"  // 可选，作物类型
    }

    服务端响应格式：
    {
        "type": "detection",
        "boxes": [
            {"pest_name": "稻飞虱", "confidence": 0.85, "x": 0.1, "y": 0.2, ...},
            ...
        ],
        "severity": "高",
        "avg_confidence": 0.83,
        "error": null
    }
    """
    await websocket.accept()

    try:
        # 验证 token
        if not token:
            await websocket.send_json({
                "type": "error",
                "error": "缺少认证令牌"
            })
            await websocket.close(code=1008)
            return

        try:
            user_id = auth.decode_access_token(token)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "error": "认证失败"
            })
            await websocket.close(code=1008)
            return

        # 接收和处理帧
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "frame":
                try:
                    # 解析 base64 图片
                    image_data = data.get("image", "")
                    if image_data.startswith("data:image"):
                        # 移除 data URL 前缀
                        image_data = image_data.split(",", 1)[1]

                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(BytesIO(image_bytes))

                    # 生成模拟检测结果（使用 mock_data）
                    # 注意：这里暂时使用空的 image_url，因为是实时流不需要保存
                    mock_result = mock_data.create_mock_detection(
                        crop_type=data.get("crop_type"),
                        image_url=""  # 实时流不保存图片
                    )

                    # 发送检测结果
                    await websocket.send_json({
                        "type": "detection",
                        "boxes": [box.dict() for box in mock_result.boxes],
                        "severity": mock_result.severity,
                        "avg_confidence": mock_result.avg_confidence,
                        "pest_types": mock_result.pest_types,
                        "error": None
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"处理图片失败：{str(e)}"
                    })

            elif data.get("type") == "ping":
                # 心跳检测
                await websocket.send_json({
                    "type": "pong"
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket 错误：{e}")
        try:
            await websocket.close(code=1011)
        except:
            pass
