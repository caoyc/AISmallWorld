# TTS模块开发方案

## 一、需求概述

### 1.1 整体目标
在对话历史中实现完整的TTS播放功能，支持数字人和立绘两种角色类型使用不同的TTS引擎。

### 1.2 核心需求

1. **角色类型判断**
   - 数字人：使用数字人自带的TTS（通过 `digitalHumanInstance.speak()`）
   - 立绘：使用豆包的TTS（通过API调用）

2. **立绘音色设置**
   - 在编辑面板中添加TTS音色配置
   - TTS引擎选择（目前只有豆包，后续可扩展）
   - 音色试听功能
   - 为当前角色设置指定的音色

## 二、技术方案

### 2.1 架构设计

```
对话历史消息播放
    ↓
判断角色类型
    ├─ 数字人 → 使用数字人SDK的TTS (digitalHumanInstance.speak)
    └─ 立绘 → 使用豆包TTS API
        ├─ 获取角色音色配置
        ├─ 调用豆包TTS API
        └─ 播放音频
```

### 2.2 数据结构设计

#### 2.2.1 角色类型扩展

在 `Role` 和 `UserRole` 接口中添加TTS配置字段（仅对立绘类型有效）：

```typescript
export interface Role {
  // ... 现有字段 ...
  
  // TTS配置（仅立绘类型使用）
  ttsProvider?: 'doubao' | string  // TTS引擎，默认'doubao'
  ttsVoice?: string                // 音色ID，例如：'zh_female_shuangkuai_meet'（豆包音色）
  ttsSpeed?: number                // 语速 (0.1-2.0)，默认1.0
  ttsVolume?: number               // 音量 (0.5-2.0)，默认1.0
}

export interface UserRole {
  // ... 现有字段 ...
  
  // TTS配置（仅立绘类型使用）
  ttsProvider?: 'doubao' | string
  ttsVoice?: string
  ttsSpeed?: number
  ttsVolume?: number
}
```

#### 2.2.2 数据库字段扩展

在 `roles` 和 `user_roles` 表中添加字段：

```sql
-- roles 表
ALTER TABLE roles ADD COLUMN tts_provider TEXT DEFAULT 'doubao';
ALTER TABLE roles ADD COLUMN tts_voice TEXT;
ALTER TABLE roles ADD COLUMN tts_speed REAL DEFAULT 1.0;
ALTER TABLE roles ADD COLUMN tts_volume REAL DEFAULT 1.0;

-- user_roles 表
ALTER TABLE user_roles ADD COLUMN tts_provider TEXT DEFAULT 'doubao';
ALTER TABLE user_roles ADD COLUMN tts_voice TEXT;
ALTER TABLE user_roles ADD COLUMN tts_speed REAL DEFAULT 1.0;
ALTER TABLE user_roles ADD COLUMN tts_volume REAL DEFAULT 1.0;
```

### 2.3 服务层设计

#### 2.3.1 创建TTS服务

创建 `src/services/tts.ts`：

```typescript
// TTS服务接口
export interface TtsService {
  synthesize(text: string, config: TtsConfig): Promise<ArrayBuffer>
}

// TTS配置
export interface TtsConfig {
  provider: 'doubao' | string
  apiKey: string  // 格式: AppID:AccessToken
  voice?: string  // 音色ID
  speed?: number  // 语速
  volume?: number // 音量
}

// 豆包TTS实现
export class DoubaoTtsService implements TtsService {
  async synthesize(text: string, config: TtsConfig): Promise<ArrayBuffer> {
    // 调用豆包TTS API
    // 返回音频数据
  }
}

// TTS服务工厂
export class TtsServiceFactory {
  static create(provider: string): TtsService {
    switch (provider) {
      case 'doubao':
        return new DoubaoTtsService()
      default:
        throw new Error(`不支持的TTS引擎: ${provider}`)
    }
  }
}
```

#### 2.3.2 豆包TTS API调用

参考豆包TTS API文档：
- 接口地址：`https://ark.cn-beijing.volces.com/api/v3/tts`
- 请求方法：POST
- 请求头：需要Authorization（使用AccessToken）
- 请求体：包含文本、音色、语速等参数

### 2.4 UI设计

#### 2.4.1 编辑面板音色设置区域

在立绘角色的编辑面板中添加TTS配置区域：

```vue
<!-- 立绘TTS配置（仅当角色类型为立绘时显示） -->
<div v-if="roleForm.type === 'illustration'">
  <div class="config-divider"></div>
  <div class="config-section">
    <h4 class="section-title">语音合成设置</h4>
    
    <!-- TTS引擎选择 -->
    <div class="form-group">
      <label for="tts-provider">TTS 引擎:</label>
      <select id="tts-provider" v-model="roleForm.ttsProvider">
        <option value="doubao">豆包 TTS</option>
      </select>
    </div>
    
    <!-- 音色选择 -->
    <div class="form-group">
      <label for="tts-voice">音色:</label>
      <select id="tts-voice" v-model="roleForm.ttsVoice">
        <option v-for="voice in doubaoVoices" :key="voice.id" :value="voice.id">
          {{ voice.name }}
        </option>
      </select>
      <button class="btn btn-small" @click="previewVoice">试听</button>
    </div>
    
    <!-- 语速 -->
    <div class="form-group">
      <label for="tts-speed">语速: {{ roleForm.ttsSpeed || 1.0 }}</label>
      <input 
        id="tts-speed"
        type="range" 
        v-model.number="roleForm.ttsSpeed"
        min="0.1" 
        max="2.0" 
        step="0.1"
      />
    </div>
    
    <!-- 音量 -->
    <div class="form-group">
      <label for="tts-volume">音量: {{ roleForm.ttsVolume || 1.0 }}</label>
      <input 
        id="tts-volume"
        type="range" 
        v-model.number="roleForm.ttsVolume"
        min="0.5" 
        max="2.0" 
        step="0.1"
      />
    </div>
  </div>
</div>
```

#### 2.4.2 音色列表

定义豆包TTS支持的音色列表：

```typescript
export const DOUBAO_VOICES = [
  { id: 'zh_female_shuangkuai_meet', name: '双快-女声' },
  { id: 'zh_male_shuangkuai_meet', name: '双快-男声' },
  // ... 更多音色
]
```

## 三、实现步骤

### 3.1 第一阶段：数据结构扩展

1. **类型定义扩展**
   - 在 `src/types/index.ts` 中为 `Role` 和 `UserRole` 添加TTS字段
   - 定义TTS相关类型（TtsConfig、TtsService等）

2. **数据库扩展**
   - 在 `server/db.js` 中添加TTS字段的数据库迁移
   - 更新 `createRole`、`updateRole`、`createUserRole`、`updateUserRole` 函数

3. **后端API扩展**
   - 更新角色创建/更新接口，支持TTS字段的保存和读取

### 3.2 第二阶段：TTS服务实现

1. **创建TTS服务**
   - 创建 `src/services/tts.ts`
   - 实现 `DoubaoTtsService` 类
   - 实现豆包TTS API调用逻辑

2. **音色列表定义**
   - 创建 `src/constants/tts.ts`
   - 定义豆包TTS支持的音色列表

### 3.3 第三阶段：UI实现

1. **编辑面板扩展**
   - 在伙伴角色编辑面板中添加TTS配置区域
   - 在用户角色编辑面板中添加TTS配置区域
   - 实现音色选择下拉框
   - 实现试听功能

2. **表单处理**
   - 更新 `roleForm` 和 `userRoleForm` 的初始化
   - 更新保存逻辑，包含TTS字段

### 3.4 第四阶段：播放功能实现

1. **修改播放逻辑**
   - 修改 `playMessageAudio` 函数
   - 根据角色类型选择TTS引擎
   - 数字人：使用现有逻辑（`digitalHumanInstance.speak`）
   - 立绘：调用豆包TTS服务，获取音频后播放

2. **音频播放**
   - 使用 `Audio` API播放音频
   - 处理播放状态（播放中、暂停、停止）
   - 更新 `playingMessageId` 状态

## 四、详细设计

### 4.1 播放逻辑流程

```typescript
async function playMessageAudio(message: ChatMessage, index: number) {
  // 1. 判断消息角色
  const role = message.role === 'user' 
    ? appState.currentUserRole 
    : appState.currentPartnerRole
  
  if (!role) {
    showToastMessage('角色不存在', 'error')
    return
  }
  
  // 2. 根据角色类型选择TTS引擎
  if (role.type === 'digital_human') {
    // 数字人：使用SDK的TTS
    if (!role.isConnected || !role.digitalHumanInstance) {
      showToastMessage('数字人未连接，请先连接数字人', 'error')
      return
    }
    
    // 使用现有逻辑
    const ssml = generateSSML(message.content)
    role.digitalHumanInstance.speak(ssml, true, true)
    
  } else if (role.type === 'illustration') {
    // 立绘：使用豆包TTS
    if (!appState.tts.apiKey) {
      showToastMessage('请先在TTS设置中配置API Key', 'error')
      return
    }
    
    // 获取角色TTS配置（使用角色配置或全局配置作为默认值）
    const ttsConfig = {
      provider: role.ttsProvider || appState.tts.provider || 'doubao',
      apiKey: appState.tts.apiKey,
      voice: role.ttsVoice || 'zh_female_shuangkuai_meet', // 默认音色
      speed: role.ttsSpeed ?? appState.tts.speed ?? 1.0,
      volume: role.ttsVolume ?? appState.tts.volume ?? 1.0
    }
    
    // 调用TTS服务
    const ttsService = TtsServiceFactory.create(ttsConfig.provider)
    const audioData = await ttsService.synthesize(message.content, ttsConfig)
    
    // 播放音频
    await playAudio(audioData, index)
  }
}
```

### 4.2 音频播放实现

```typescript
let currentAudio: HTMLAudioElement | null = null

async function playAudio(audioData: ArrayBuffer, messageIndex: number) {
  // 停止当前播放
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  
  // 创建音频对象
  const blob = new Blob([audioData], { type: 'audio/mpeg' })
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  
  // 设置播放状态
  playingMessageId.value = messageIndex
  currentAudio = audio
  
  // 播放完成处理
  audio.onended = () => {
    playingMessageId.value = null
    URL.revokeObjectURL(url)
    currentAudio = null
  }
  
  // 播放错误处理
  audio.onerror = () => {
    playingMessageId.value = null
    URL.revokeObjectURL(url)
    currentAudio = null
    showToastMessage('音频播放失败', 'error')
  }
  
  // 开始播放
  await audio.play()
}

function stopMessageAudio() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  playingMessageId.value = null
}
```

### 4.3 音色试听功能

```typescript
async function previewVoice() {
  const testText = '这是一段测试语音，用于试听当前选择的音色效果。'
  
  const ttsConfig = {
    provider: roleForm.value.ttsProvider || 'doubao',
    apiKey: appState.tts.apiKey,
    voice: roleForm.value.ttsVoice || 'zh_female_shuangkuai_meet',
    speed: roleForm.value.ttsSpeed || 1.0,
    volume: roleForm.value.ttsVolume || 1.0
  }
  
  if (!ttsConfig.apiKey) {
    showToastMessage('请先在TTS设置中配置API Key', 'error')
    return
  }
  
  try {
    const ttsService = TtsServiceFactory.create(ttsConfig.provider)
    const audioData = await ttsService.synthesize(testText, ttsConfig)
    
    // 播放试听音频
    const blob = new Blob([audioData], { type: 'audio/mpeg' })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    await audio.play()
    
    audio.onended = () => {
      URL.revokeObjectURL(url)
    }
  } catch (error) {
    showToastMessage('试听失败: ' + (error as Error).message, 'error')
  }
}
```

## 五、注意事项

1. **API Key管理**
   - 全局TTS设置中的API Key用于立绘TTS
   - 每个角色可以有自己的音色配置，但共享API Key

2. **默认值处理**
   - 如果角色没有配置TTS字段，使用全局TTS设置的默认值
   - 音色默认值：`zh_female_shuangkuai_meet`

3. **错误处理**
   - TTS API调用失败时，显示错误提示
   - 音频播放失败时，清除播放状态

4. **性能优化**
   - 音频数据可以缓存（可选）
   - 避免重复调用TTS API

5. **扩展性**
   - TTS引擎选择为后续扩展其他TTS服务预留接口
   - 音色列表可以动态加载（如果需要）

## 六、测试要点

1. **功能测试**
   - 数字人角色播放消息音频（使用SDK TTS）
   - 立绘角色播放消息音频（使用豆包TTS）
   - 音色设置和保存
   - 音色试听功能

2. **边界测试**
   - 未配置API Key时的提示
   - 未选择音色时的默认值
   - 音频播放失败的处理

3. **兼容性测试**
   - 旧角色数据（没有TTS字段）的兼容性
   - 数据库迁移的正确性

