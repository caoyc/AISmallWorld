import { reactive, ref } from 'vue'
import type { AppState } from '../types'
import { LLM_CONFIG, APP_CONFIG } from '../constants'
import { validateConfig, delay } from '../utils'
import { llmService } from '../services/llm'
import { saveChatMessage } from '../services/chatHistory'
import type { ChatMessage } from '../types'

// 应用状态
export const appState = reactive<AppState>({
  avatar: {
    position: 'center' as 'left' | 'center' | 'right',
    positionX: 50,
    positionY: 50,
    scale: 1.0
    // 注意：数字人的连接状态、显示状态、实例都定义在角色对象上，不再使用全局变量
    // connected 和 instance 已移除，使用 role.isConnected 和 role.digitalHumanInstance
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
    apiKey: '',
    baseURL: LLM_CONFIG.BASE_URL,
    user: ''
  },
  tts: {
    provider: 'doubao',
    apiKey: '',
    speed: 1.0,
    volume: 1.0
  },
  ui: {
    text: '',
    subTitleText: '',
    backgroundImage: ''
  },
  conversationMode: 'ai',  // 默认AI对话模式
  chatHistory: [],
  currentUserRole: null,
  currentPartnerRole: null
})


// 虚拟人状态
export const avatarState = ref('')

// Store类 - 业务逻辑处理
export class AppStore {
  /**
   * 断开虚拟人连接（已废弃，使用角色级别的断开逻辑）
   * @deprecated 请使用角色级别的断开逻辑，如 handleDisconnectUserRoleFromList 或 handleDisconnectRoleFromList
   * @returns {void}
   */
  disconnectAvatar(): void {
    // 已废弃：数字人连接状态和实例现在存储在角色对象上
    // 此函数保留仅为兼容性，实际应该使用角色级别的断开逻辑
    console.warn('disconnectAvatar() 已废弃，请使用角色级别的断开逻辑')
  }

  /**
   * 发送消息到LLM并让虚拟人播报
   * @returns {Promise<string | undefined>} - 返回大语言模型的回复内容，失败时返回undefined
   * @throws {Error} - 当发送消息失败时抛出错误
   */
  async sendMessage(): Promise<string | undefined> {
    const { llm, ui } = appState
    
    if (!validateConfig(llm, ['apiKey']) || !ui.text) {
      return
    }

    // 保存用户消息
    const userMessage = ui.text.trim()
    
    // 保存用户消息到历史记录（原样保存，不做任何处理）
    const userChatMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    }
    appState.chatHistory.push(userChatMessage)
    
    // 保存到数据库（原样保存，不做处理）
    try {
      await saveChatMessage(
        'user',
        userMessage,
        llm.apiKey,
        llm.user || '',
        userChatMessage.timestamp
      )
    } catch (error) {
      console.error('保存用户消息失败:', error)
    }
    
    // 自动切换角色（如果启用）- 用户消息
    if (appState.currentUserRole?.enableAutoSwitch) {
      // 触发自定义事件，让 ConfigPanel 处理切换
      window.dispatchEvent(new CustomEvent('autoSwitchRole', { detail: { role: 'user' } }))
    }

    try {
      // 获取最近7条聊天历史（不包括刚添加的当前用户消息）
      const recentHistory = appState.chatHistory
        .slice(0, -1) // 排除刚添加的当前用户消息
        .slice(-7) // 取最后7条
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      
      // 发送到LLM获取回复（原样发送，不做处理）
      const stream = await llmService.sendMessageWithStream({
        provider: 'openai',
        model: llm.model,
        apiKey: llm.apiKey,
        baseURL: llm.baseURL,
        user: llm.user
      }, userMessage, recentHistory)

      if (!stream) return

      // 不再自动播放，改为手动控制
      // 等待虚拟人停止说话（如果之前有播放，且已连接数字人）
      if (appState.currentUserRole?.digitalHumanInstance) {
      await this.waitForAvatarReady()
      }

      // 流式接收响应内容（不自动播放）
      let fullResponse = '' // 保存完整的回复内容
      
      for await (const chunk of stream) {
        fullResponse += chunk // 累积完整回复
      }

      // 使用完整的回复内容进行处理
      const finalContent = fullResponse

    // 保存助手回复到历史记录
    const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: finalContent,
        timestamp: Date.now()
    }
    appState.chatHistory.push(assistantMessage)
    
    // 保存到数据库
    try {
      await saveChatMessage(
        'assistant',
        finalContent,
        llm.apiKey,
        llm.user || '',
        assistantMessage.timestamp
      )
    } catch (error) {
      console.error('保存助手回复失败:', error)
    }
    
    // 自动切换角色（如果启用）- 助手消息
    if (appState.currentPartnerRole?.enableAutoSwitch) {
      // 触发自定义事件，让 ConfigPanel 处理切换
      window.dispatchEvent(new CustomEvent('autoSwitchRole', { detail: { role: 'assistant' } }))
    }
    
    // 自动播放（如果启用且允许播放）- 助手消息
    if (appState.currentPartnerRole?.enableAutoPlay && appState.currentPartnerRole?.enableVoicePlay !== false) {
      // 触发自定义事件，让 ConfigPanel 处理播放
      window.dispatchEvent(new CustomEvent('autoPlayMessage', { detail: { messageIndex: appState.chatHistory.length - 1 } }))
    }

      // 清空输入框
      ui.text = ''

      return finalContent
    } catch (error) {
      console.error('发送消息失败:', error)
      
      // 提取详细错误信息并重新抛出，确保错误信息完整传递
      if (error instanceof Error) {
        throw error
      } else if (error && typeof error === 'object' && 'message' in error) {
        throw new Error(String(error.message))
      } else {
        throw new Error('发送消息失败: ' + String(error))
      }
    }
  }

  /**
   * 开始语音输入
   * @param callbacks - 回调函数集合
   * @param callbacks.onFinished - 语音识别完成回调
   * @param callbacks.onError - 语音识别错误回调
   * @returns {void}
   */
  startVoiceInput(_callbacks: {
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
    if (!appState.currentUserRole?.digitalHumanInstance) {
      return
    }
    if (avatarState.value === 'speak') {
      appState.currentUserRole.digitalHumanInstance.think()
      await delay(APP_CONFIG.SPEAK_INTERRUPT_DELAY)
    }
  }
}

// 导出单例
export const appStore = new AppStore()
