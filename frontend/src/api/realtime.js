/**
 * 实时视频检测 WebSocket 客户端
 */

let ws = null
let isConnected = false

/**
 * 建立 WebSocket 连接
 * @param {string} token - JWT token
 * @returns {Promise<void>}
 */
export async function connectWebSocket(token) {
  return new Promise((resolve, reject) => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/detect?token=${token}`

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        isConnected = true
        console.log('WebSocket 已连接')
        resolve()
      }

      ws.onerror = (error) => {
        console.error('WebSocket 连接错误：', error)
        isConnected = false
        reject(error)
      }

      ws.onclose = () => {
        isConnected = false
        console.log('WebSocket 已断开')
      }
    } catch (error) {
      console.error('创建 WebSocket 失败：', error)
      reject(error)
    }
  })
}

/**
 * 发送图片帧进行检测
 * @param {string} imageBase64 - base64 编码的图片
 * @param {string} cropType - 可选的作物类型
 * @returns {Promise<{boxes, severity, avg_confidence, pest_types, error}>}
 */
export async function sendFrame(imageBase64, cropType = null) {
  return new Promise((resolve, reject) => {
    if (!isConnected || !ws) {
      reject(new Error('WebSocket 未连接'))
      return
    }

    // 设置接收响应的回调
    const handler = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'detection') {
          ws.removeEventListener('message', handler)
          resolve(data)
        } else if (data.type === 'error') {
          ws.removeEventListener('message', handler)
          reject(new Error(data.error))
        }
      } catch (e) {
        console.error('解析响应失败：', e)
      }
    }

    ws.addEventListener('message', handler)

    // 发送帧
    ws.send(JSON.stringify({
      type: 'frame',
      image: imageBase64,
      crop_type: cropType
    }))

    // 设置超时
    setTimeout(() => {
      ws.removeEventListener('message', handler)
      reject(new Error('请求超时'))
    }, 10000)
  })
}

/**
 * 断开 WebSocket 连接
 */
export function disconnectWebSocket() {
  if (ws) {
    ws.close()
    ws = null
    isConnected = false
  }
}

/**
 * 获取连接状态
 */
export function isWebSocketConnected() {
  return isConnected
}

/**
 * 发送心跳包
 */
export function sendPing() {
  if (isConnected && ws) {
    ws.send(JSON.stringify({
      type: 'ping'
    }))
  }
}
