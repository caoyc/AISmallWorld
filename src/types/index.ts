// 导入数字人实例类型
import type { DigitalHumanInstance } from '../renderers/digital-human/types'

// 虚拟人相关类型定义
export interface AvatarConfig {
  appId: string
  appSecret: string
}

export interface AvatarState {
  connected: boolean
  speaking: boolean
  thinking: boolean
}

// ASR相关类型定义
export interface AsrConfig {
  provider: 'tx' // 目前只支持腾讯云
  appId: string | number
  secretId: string
  secretKey: string
  vadSilenceTime?: number
}

export interface AsrCallbacks {
  onFinished: (text: string) => void
  onError: (error: any) => void
}

// LLM相关类型定义
export interface LlmConfig {
  provider: string
  model: string
  apiKey: string
  baseURL?: string
  user?: string
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
  timestamp?: number
}

// 角色管理相关类型定义
export interface Role {
  id: number              // 角色唯一标识（数据库主键，自增整数）
  name?: string           // 角色名称（显示名称，可选）
  user: string            // user字段的值（传给大模型，必填）
  type: 'digital_human' | 'illustration'  // 角色类型：数字人、立绘
  description?: string    // 角色描述（可选）
  avatar?: string         // 角色头像URL（可选）
  positionX?: number      // 水平位置百分比 (0-100)
  positionY?: number      // 垂直位置百分比 (0-100)
  scale?: number          // 缩放比例 (0.5-2.0)
  baseURL?: string        // 大模型API Base URL（可选）
  model?: string          // 大模型名称（可选）
  apiKey?: string         // 大模型API Key（可选）
  avatarAppId?: string    // 数字人 SDK App ID（可选，仅数字人类型）
  avatarAppSecret?: string // 数字人 SDK App Secret（可选，仅数字人类型）
  // 语音选项（仅数字人类型使用）
  useDigitalHumanVoice?: boolean  // 是否使用数字人自带语音，默认true（true=数字人语音，false=TTS语音）
  // TTS配置（立绘类型使用，或数字人类型且useDigitalHumanVoice=false时使用）
  ttsProvider?: 'doubao' | string  // TTS引擎，默认'doubao'
  ttsVoice?: string                // 音色ID，例如：'BV700_streaming'（豆包音色）
  ttsSpeed?: number                // 语速 (0.1-2.0)，默认1.0
  ttsVolume?: number               // 音量 (0.5-2.0)，默认1.0
  ttsPreviewText?: string          // TTS试听文本
  // 语音播放控制（仅立绘类型使用）
  enableVoicePlay?: boolean      // 启用语音播放，默认true
  enableAutoPlay?: boolean       // 启用自动播放，默认false
  enableAutoSwitch?: boolean    // 自动切换角色，默认false
  isConnecting?: boolean  // 是否正在连接（前端状态，不存储到数据库）
  isConnected?: boolean   // 是否已连接（前端状态，不存储到数据库）
  showDigitalHuman?: boolean // 是否显示数字人（前端状态，不存储到数据库）
  digitalHumanInstance?: DigitalHumanInstance | null // 数字人SDK实例（前端状态，不存储到数据库）
  createdAt: number       // 创建时间戳（Unix时间戳）
  updatedAt: number       // 更新时间戳（Unix时间戳）
}

// 用户角色相关类型定义
export interface UserRole {
  id: number              // 用户角色唯一标识（数据库主键，自增整数）
  apiKey: string         // 用户账号（登录的apiKey）
  user: string           // user字段（必填，仅用于和伙伴角色形式一致）
  name?: string          // 角色名称（可选，为空时使用user字段）
  type?: 'digital_human' | 'illustration'  // 角色类型：数字人、立绘
  avatar?: string        // 头像URL（可选）
  positionX?: number      // 水平位置百分比 (0-100)
  positionY?: number      // 垂直位置百分比 (0-100)
  scale?: number          // 缩放比例 (0.5-2.0)
  baseURL?: string        // 大模型API Base URL（可选）
  model?: string          // 大模型名称（可选）
  avatarAppId?: string    // 数字人 SDK App ID（可选，仅数字人类型）
  avatarAppSecret?: string // 数字人 SDK App Secret（可选，仅数字人类型）
  // 语音选项（仅数字人类型使用）
  useDigitalHumanVoice?: boolean  // 是否使用数字人自带语音，默认true（true=数字人语音，false=TTS语音）
  // TTS配置（立绘类型使用，或数字人类型且useDigitalHumanVoice=false时使用）
  ttsProvider?: 'doubao' | string  // TTS引擎，默认'doubao'
  ttsVoice?: string                // 音色ID，例如：'BV700_streaming'（豆包音色）
  ttsSpeed?: number                // 语速 (0.1-2.0)，默认1.0
  ttsVolume?: number               // 音量 (0.5-2.0)，默认1.0
  ttsPreviewText?: string          // TTS试听文本
  // 语音播放控制（仅立绘类型使用）
  enableVoicePlay?: boolean      // 启用语音播放，默认true
  enableAutoPlay?: boolean       // 启用自动播放，默认false
  enableAutoSwitch?: boolean    // 自动切换角色，默认false
  isCurrent: boolean     // 是否为当前角色
  isConnecting?: boolean  // 是否正在连接（前端状态，不存储到数据库）
  isConnected?: boolean   // 是否已连接（前端状态，不存储到数据库）
  showDigitalHuman?: boolean // 是否显示数字人（前端状态，不存储到数据库）
  digitalHumanInstance?: DigitalHumanInstance | null // 数字人SDK实例（前端状态，不存储到数据库）
  createdAt: number       // 创建时间戳（Unix时间戳）
  updatedAt: number       // 更新时间戳（Unix时间戳）
}

// 背景管理相关类型定义
export interface Background {
  id: number              // 背景唯一标识（数据库主键，自增整数）
  apiKey: string         // 用户账号（登录的apiKey）
  name?: string          // 背景名称（可选）
  url: string            // 背景图像URL
  createdAt: number       // 创建时间戳（Unix时间戳）
  updatedAt: number       // 更新时间戳（Unix时间戳）
}

// TTS相关类型定义
export interface TtsConfig {
  provider: 'doubao' | string
  apiKey: string  // 格式: AppID:AccessToken
  voice?: string  // 音色ID
  speed?: number  // 语速
  volume?: number // 音量
}

// TTS服务接口
export interface TtsService {
  synthesize(text: string, config: TtsConfig): Promise<ArrayBuffer>
}

// Store类型定义
export interface AppStore {
  disconnectAvatar(): void
  sendMessage(): Promise<string | undefined>
  startVoiceInput(callbacks: AsrCallbacks): void
  stopVoiceInput(): void
}

// Store状态类型定义
export interface AppState {
  // 虚拟人配置
  avatar: {
    position: 'left' | 'center' | 'right'
    positionX: number // 水平位置百分比 (0-100)
    positionY: number // 垂直位置百分比 (0-100)
    scale: number // 缩放比例 (0.5-2.0)
    // 注意：数字人的连接状态、显示状态、实例都定义在角色对象上，不再使用全局变量
    // connected 和 instance 已移除，使用 role.isConnected 和 role.digitalHumanInstance
  }
  
  // ASR配置
  asr: {
    provider: string
    appId: string | number
    secretId: string
    secretKey: string
    isListening: boolean
  }
  
  // LLM配置
  llm: {
    model: string
    apiKey: string
    baseURL: string
    user: string
  }
  
  // 当前角色（全局共享）
  currentUserRole: UserRole | null
  currentPartnerRole: Role | null
  
  // TTS配置
  tts: {
    provider: string
    apiKey: string
    speed: number
    volume: number
  }
  
  // UI状态
  ui: {
    text: string
    subTitleText: string
    backgroundImage: string
  }
  
  // 对话模式
  conversationMode: 'ai' | 'speech'  // 'ai': AI对话模式（默认），'speech': 演示对话模式
  
  // 对话历史
  chatHistory: ChatMessage[]
}

// SDK事件类型定义
export interface SdkEvent {
  type: 'subtitle_on' | 'subtitle_off' | string
  text?: string
  [key: string]: any
}

// 全局窗口类型扩展
declare global {
  interface Window {
    XmovAvatar: any
    CryptoJSTest: any
    CryptoJS: any
    WebAudioSpeechRecognizer: any
  }
}
