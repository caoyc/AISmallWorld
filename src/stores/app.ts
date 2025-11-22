import { reactive, ref } from 'vue'
import type { AppState, AvatarConfig, AsrConfig, LlmConfig } from '../types'
import { LLM_CONFIG, APP_CONFIG, AVATAR_CONFIG } from '../constants'
import { validateConfig, delay, generateSSML, extractMarkdownImages, removeMarkdownImages } from '../utils'
import { avatarService } from '../services/avatar'
import { llmService } from '../services/llm'

// 应用状态
export const appState = reactive<AppState>({
  avatar: {
    appId: AVATAR_CONFIG.DEFAULT_APP_ID,
    appSecret: AVATAR_CONFIG.DEFAULT_APP_SECRET,
    connected: false,
    instance: null
  },
  asr: {
    provider: 'tx',
    appId: '',
    secretId: '',
    secretKey: '',
    isListening: false
  },
  llm: {
    model: LLM_CONFIG.DEFAULT_MODEL,
    apiKey: LLM_CONFIG.DEFAULT_API_KEY,
    baseURL: LLM_CONFIG.BASE_URL
  },
  ui: {
    text: '',
    subTitleText: '',
    backgroundImage: ''
  },
  chatHistory: []
})

const MIN_SPLIT_LENGTH = 2 // 最小切分长度
const MAX_SPLIT_LENGTH = 20 // 最大切分长度
function splitSentence(text: string): string[] {
  if (!text) return []

  // 定义中文标点（不需要空格）
  const chinesePunctuations = new Set(['、', '，', '：', '；', '。', '？', '！', '…', '\n'])
  // 定义英文标点（需要后跟空格）
  const englishPunctuations = new Set([',', ':', ';', '.', '?', '!'])

  let count = 0
  let firstValidPunctAfterMin = -1 // 最小长度后第一个有效标点位置
  let forceBreakIndex = -1 // 强制切分位置
  let i = 0
  const n = text.length

  // 扫描文本直到达到最大长度或文本结束
  while (i < n && count < MAX_SPLIT_LENGTH) {
    const char = text[i]

    // 处理汉字
    if (char >= '\u4e00' && char <= '\u9fff') {
      count++
      // 记录达到最大长度时的位置
      if (count === MAX_SPLIT_LENGTH) {
        forceBreakIndex = i + 1 // 在汉字后切分
      }
      i++
    }
    // 处理数字序列
    else if (char >= '0' && char <= '9') {
      count++
      if (count === MAX_SPLIT_LENGTH) {
        forceBreakIndex = i + 1
      }
      i++
    }
    // 处理英文字母序列（单词）
    else if ((char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z')) {
      // 扫描整个英文单词
      const start = i
      i++
      while (i < n && ((text[i] >= 'a' && text[i] <= 'z') || (text[i] >= 'A' && text[i] <= 'Z'))) {
        i++
      }
      count++
      if (count === MAX_SPLIT_LENGTH) {
        forceBreakIndex = i // 在单词后切分
      }
    }
    // 处理标点符号
    else {
      if (chinesePunctuations.has(char)) {
        // 达到最小长度后记录第一个有效中文标点
        if (count >= MIN_SPLIT_LENGTH && firstValidPunctAfterMin === -1) {
          firstValidPunctAfterMin = i
        }
        i++
      } else if (englishPunctuations.has(char)) {
        // 英文标点：检查后跟空格或结束
        if (i + 1 >= n || text[i + 1] === ' ') {
          // 达到最小长度后记录第一个有效英文标点
          if (count >= MIN_SPLIT_LENGTH && firstValidPunctAfterMin === -1) {
            firstValidPunctAfterMin = i
          }
        }
        i++
      } else {
        // 其他字符（如空格、符号等），跳过
        i++
      }
    }
  }

  // 确定切分位置
  let splitIndex = -1
  if (firstValidPunctAfterMin !== -1) {
    splitIndex = firstValidPunctAfterMin + 1
  } else if (forceBreakIndex !== -1) {
    splitIndex = forceBreakIndex
  }

  // 返回切分结果
  if (splitIndex > 0 && splitIndex < text.length) {
    return [text.substring(0, splitIndex), text.substring(splitIndex)]
  }
  
  return [text]
}

// 虚拟人状态
export const avatarState = ref('')

// Store类 - 业务逻辑处理
export class AppStore {
  /**
   * 连接虚拟人
   * @returns {Promise<void>} - 返回连接结果的Promise
   * @throws {Error} - 当appId或appSecret为空或连接失败时抛出错误
   */
  async connectAvatar(): Promise<void> {
    const { appId, appSecret } = appState.avatar
    
    if (!validateConfig({ appId, appSecret }, ['appId', 'appSecret'])) {
      throw new Error('appId 或 appSecret 为空')
    }

    try {
      const avatar = await avatarService.connect({
        appId,
        appSecret
      }, {
        onSubtitleOn: (text: string) => {
          appState.ui.subTitleText = text
        },
        onSubtitleOff: () => {
          appState.ui.subTitleText = ''
        },
        onStateChange: (state: string) => {
          avatarState.value = state
        }
      })

      appState.avatar.instance = avatar
      appState.avatar.connected = true
    } catch (error) {
      appState.avatar.connected = false
      throw error
    }
  }

  /**
   * 断开虚拟人连接
   * @returns {void}
   */
  disconnectAvatar(): void {
    if (appState.avatar.instance) {
      avatarService.disconnect(appState.avatar.instance)
      appState.avatar.instance = null
      appState.avatar.connected = false
      avatarState.value = ''
    }
  }

  /**
   * 发送消息到LLM并让虚拟人播报
   * @returns {Promise<string | undefined>} - 返回大语言模型的回复内容，失败时返回undefined
   * @throws {Error} - 当发送消息失败时抛出错误
   */
  async sendMessage(): Promise<string | undefined> {
    const { llm, ui, avatar } = appState
    
    if (!validateConfig(llm, ['apiKey']) || !ui.text || !avatar.instance) {
      return
    }

    // 保存用户消息到历史记录
    const userMessage = ui.text.trim()
    
    // 处理用户消息中的 markdown 图像（如果存在）
    const userImages = extractMarkdownImages(userMessage)
    let processedUserMessage = userMessage
    if (userImages.length > 0) {
      // 获取最后一个图像的地址作为背景
      const lastImage = userImages[userImages.length - 1]
      appState.ui.backgroundImage = lastImage.imageUrl
      
      // 从消息内容中移除所有图像标记
      processedUserMessage = removeMarkdownImages(userMessage)
    }
    
    appState.chatHistory.push({
      role: 'user',
      content: processedUserMessage,
      timestamp: Date.now()
    })

    try {
      // 发送到LLM获取回复
      const stream = await llmService.sendMessageWithStream({
        provider: 'openai',
        model: llm.model,
        apiKey: llm.apiKey,
        baseURL: llm.baseURL
      }, userMessage)

      if (!stream) return

      // 等待虚拟人停止说话
      await this.waitForAvatarReady()

      // 流式播报响应内容 - 只处理第一个非空行
      let buffer = '' // 用于累积内容的 buffer
      let fullResponse = '' // 保存完整的回复内容
      let hasStartedSpeaking = false // 是否已开始播报
      
      for await (const chunk of stream) {
        buffer += chunk
        fullResponse += chunk // 同时保存到完整回复中
        
        // 如果还没有找到第一个非空行，检查是否有完整的行
        if (!hasStartedSpeaking) {
          // 按换行符分割，检查是否有完整的行（最后一部分可能是不完整的）
          const lines = buffer.split(/\r?\n/)
          
          // 查找第一个完整的非空行（除了最后一部分，因为可能还没接收完）
          for (let i = 0; i < lines.length - 1; i++) {
            const trimmedLine = lines[i].trim()
            if (trimmedLine.length > 0) {
              // 找到第一个完整的非空行，立即播报
              const ssml = generateSSML(trimmedLine)
              avatar.instance.speak(ssml, true, true)
              hasStartedSpeaking = true
              break
            }
          }
        }
      }

      // 如果流结束时还没有开始播报
      if (!hasStartedSpeaking && buffer.length > 0) {
        // 检查是否有换行符
        const hasNewline = /\r?\n/.test(buffer)
        
        if (hasNewline) {
          // 有换行符，查找第一个非空行
          const lines = buffer.split(/\r?\n/)
          for (const line of lines) {
            const trimmedLine = line.trim()
            if (trimmedLine.length > 0) {
              // 播报第一个非空行
              const ssml = generateSSML(trimmedLine)
              avatar.instance.speak(ssml, true, true)
              hasStartedSpeaking = true
              break
            }
          }
        } else {
          // 没有换行符，播放全部内容
          const trimmedBuffer = buffer.trim()
          if (trimmedBuffer.length > 0) {
            const ssml = generateSSML(trimmedBuffer)
            avatar.instance.speak(ssml, true, true)
            hasStartedSpeaking = true
          }
        }
      }

      // 如果没有找到任何非空行，发送空SSML结束标记
      if (!hasStartedSpeaking) {
        const finalSsml = generateSSML('')
        avatar.instance.speak(finalSsml, false, true)
      }

      // 使用完整的回复内容进行处理
      let finalContent = fullResponse

      // 处理 markdown 图像：检测并设置为背景
      const images = extractMarkdownImages(finalContent)
      if (images.length > 0) {
        // 获取最后一个图像的地址作为背景
        const lastImage = images[images.length - 1]
        appState.ui.backgroundImage = lastImage.imageUrl
        
        // 从消息内容中移除所有图像标记
        finalContent = removeMarkdownImages(finalContent)
      }

      // 保存助手回复到历史记录（使用完整内容）
      appState.chatHistory.push({
        role: 'assistant',
        content: finalContent,
        timestamp: Date.now()
      })

      // 清空输入框
      ui.text = ''

      return finalContent
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    }
  }

  /**
   * 开始语音输入
   * @param callbacks - 回调函数集合
   * @param callbacks.onFinished - 语音识别完成回调
   * @param callbacks.onError - 语音识别错误回调
   * @returns {void}
   */
  startVoiceInput(callbacks: {
    onFinished: (text: string) => void
    onError: (error: any) => void
  }): void {
    appState.asr.isListening = true
    // ASR逻辑由组件处理
  }

  /**
   * 停止语音输入
   * @returns {void}
   */
  stopVoiceInput(): void {
    appState.asr.isListening = false
  }

  /**
   * 等待虚拟人准备就绪（不在说话状态）
   * @returns {Promise<void>} - 返回等待完成的Promise
   */
  private async waitForAvatarReady(): Promise<void> {
    if (avatarState.value === 'speak') {
      appState.avatar.instance.think()
      await delay(APP_CONFIG.SPEAK_INTERRUPT_DELAY)
    }
  }
}

// 导出单例
export const appStore = new AppStore()
