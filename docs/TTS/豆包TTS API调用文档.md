# 豆包TTS API调用文档

## 一、API基本信息

### 1.1 接口地址
```
POST https://ark.cn-beijing.volces.com/api/v3/tts
```

### 1.2 认证方式
使用 `Authorization` 请求头，格式：
```
Authorization: Bearer {AccessToken}
```

### 1.3 请求头
```
Content-Type: application/json
Authorization: Bearer {AccessToken}
```

## 二、请求参数

### 2.1 请求体格式
```json
{
  "text": "要合成的文本内容",
  "voice": "音色ID",
  "speed": 1.0,
  "volume": 1.0,
  "format": "mp3",
  "sample_rate": 24000
}
```

### 2.2 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要合成的文本内容，最大长度5000字符 |
| voice | string | 否 | 音色ID，默认值根据API Key确定 |
| speed | number | 否 | 语速，范围0.5-2.0，默认1.0 |
| volume | number | 否 | 音量，范围0.5-2.0，默认1.0 |
| format | string | 否 | 音频格式，支持mp3/wav，默认mp3 |
| sample_rate | number | 否 | 采样率，支持16000/24000，默认24000 |

## 三、响应格式

### 3.1 成功响应
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "audio": "base64编码的音频数据"
  }
}
```

### 3.2 错误响应
```json
{
  "code": 10001,
  "message": "错误信息",
  "data": null
}
```

## 四、音色列表

### 4.1 常用音色

| 音色ID | 名称 | 性别 | 特点 |
|--------|------|------|------|
| zh_female_shuangkuai_meet | 双快-女声 | 女 | 快速、清晰 |
| zh_male_shuangkuai_meet | 双快-男声 | 男 | 快速、清晰 |
| zh_female_qingxin_meet | 清新-女声 | 女 | 清新、自然 |
| zh_male_qingxin_meet | 清新-男声 | 男 | 清新、自然 |
| zh_female_wennuan_meet | 温暖-女声 | 女 | 温暖、柔和 |
| zh_male_wennuan_meet | 温暖-男声 | 男 | 温暖、柔和 |

### 4.2 音色常量定义

```typescript
export const DOUBAO_VOICES = [
  { id: 'zh_female_shuangkuai_meet', name: '双快-女声', gender: 'female' },
  { id: 'zh_male_shuangkuai_meet', name: '双快-男声', gender: 'male' },
  { id: 'zh_female_qingxin_meet', name: '清新-女声', gender: 'female' },
  { id: 'zh_male_qingxin_meet', name: '清新-男声', gender: 'male' },
  { id: 'zh_female_wennuan_meet', name: '温暖-女声', gender: 'female' },
  { id: 'zh_male_wennuan_meet', name: '温暖-男声', gender: 'male' },
  // 更多音色...
]
```

## 五、实现示例

### 5.1 TypeScript实现

```typescript
interface DoubaoTtsRequest {
  text: string
  voice?: string
  speed?: number
  volume?: number
  format?: 'mp3' | 'wav'
  sample_rate?: 16000 | 24000
}

interface DoubaoTtsResponse {
  code: number
  message: string
  data: {
    audio: string  // base64编码的音频数据
  }
}

async function callDoubaoTts(
  text: string,
  apiKey: string,  // 格式: AppID:AccessToken
  config: {
    voice?: string
    speed?: number
    volume?: number
  } = {}
): Promise<ArrayBuffer> {
  // 解析API Key
  const [appId, accessToken] = apiKey.split(':')
  if (!appId || !accessToken) {
    throw new Error('API Key格式错误，应为 AppID:AccessToken')
  }
  
  // 构建请求
  const requestBody: DoubaoTtsRequest = {
    text,
    voice: config.voice || 'zh_female_shuangkuai_meet',
    speed: config.speed ?? 1.0,
    volume: config.volume ?? 1.0,
    format: 'mp3',
    sample_rate: 24000
  }
  
  // 发送请求
  const response = await fetch('https://ark.cn-beijing.volces.com/api/v3/tts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify(requestBody)
  })
  
  if (!response.ok) {
    throw new Error(`TTS API请求失败: ${response.status} ${response.statusText}`)
  }
  
  const result: DoubaoTtsResponse = await response.json()
  
  if (result.code !== 0) {
    throw new Error(`TTS API错误: ${result.message}`)
  }
  
  // 将base64音频数据转换为ArrayBuffer
  const audioBase64 = result.data.audio
  const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))
  return audioBytes.buffer
}
```

### 5.2 错误处理

```typescript
try {
  const audioData = await callDoubaoTts(text, apiKey, {
    voice: 'zh_female_shuangkuai_meet',
    speed: 1.0,
    volume: 1.0
  })
  // 播放音频...
} catch (error) {
  if (error instanceof Error) {
    if (error.message.includes('API Key格式错误')) {
      showToastMessage('API Key格式错误，请检查配置', 'error')
    } else if (error.message.includes('TTS API请求失败')) {
      showToastMessage('TTS服务请求失败，请检查网络连接', 'error')
    } else if (error.message.includes('TTS API错误')) {
      showToastMessage('TTS服务错误: ' + error.message, 'error')
    } else {
      showToastMessage('TTS调用失败: ' + error.message, 'error')
    }
  }
}
```

## 六、注意事项

1. **API Key格式**
   - 格式：`AppID:AccessToken`
   - AppID和AccessToken通过冒号分隔
   - 需要在豆包控制台获取

2. **文本长度限制**
   - 单次请求最大文本长度：5000字符
   - 如果文本过长，需要分段处理

3. **请求频率限制**
   - 注意API的请求频率限制
   - 避免短时间内大量请求

4. **音频格式**
   - 推荐使用mp3格式（文件小、兼容性好）
   - 采样率24000（音质更好）

5. **错误码说明**
   - code=0：成功
   - code!=0：失败，查看message字段获取错误信息

## 七、测试用例

### 7.1 基本调用测试
```typescript
const testText = '这是一段测试文本，用于验证TTS功能是否正常。'
const apiKey = 'your-app-id:your-access-token'

const audioData = await callDoubaoTts(testText, apiKey)
console.log('音频数据大小:', audioData.byteLength)
```

### 7.2 不同音色测试
```typescript
const voices = [
  'zh_female_shuangkuai_meet',
  'zh_male_shuangkuai_meet',
  'zh_female_qingxin_meet'
]

for (const voice of voices) {
  const audioData = await callDoubaoTts(testText, apiKey, { voice })
  // 播放音频进行对比...
}
```

### 7.3 不同语速测试
```typescript
const speeds = [0.5, 1.0, 1.5, 2.0]

for (const speed of speeds) {
  const audioData = await callDoubaoTts(testText, apiKey, { speed })
  // 播放音频进行对比...
}
```

