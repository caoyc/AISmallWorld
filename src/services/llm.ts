import OpenAI from 'openai'
import type { LlmConfig, ChatMessage } from '../types'
import { LLM_CONFIG } from '../constants'

class LlmService {
  private openai: OpenAI | null = null
  private currentApiKey: string = ''

  /**
   * 初始化LLM客户端
   * @param config - LLM配置对象
   * @param config.apiKey - API密钥
   * @param config.model - 模型名称
   * @param config.baseURL - 可选的基础URL
   * @returns void
   */
  private openaiBaseURL: string = ''

  private initClient(config: LlmConfig): void {
    const baseURL = config.baseURL || LLM_CONFIG.BASE_URL
    // 如果 API Key 或 baseURL 发生变化，重新初始化客户端
    if (this.currentApiKey === config.apiKey && this.openaiBaseURL === baseURL && this.openai) {
      return
    }

    this.openai = new OpenAI({
      apiKey: config.apiKey,
      dangerouslyAllowBrowser: true,
      baseURL: baseURL
    })
    
    this.currentApiKey = config.apiKey
    this.openaiBaseURL = baseURL
  }

  /**
   * 发送消息到大语言模型
   * @param config - LLM配置对象
   * @param config.apiKey - API密钥
   * @param config.model - 模型名称
   * @param config.baseURL - 可选的基础URL
   * @param userMessage - 用户输入的消息内容
   * @returns Promise<string | null> - 返回模型的回复内容，失败时返回null
   * @throws {Error} - 当LLM客户端未初始化或请求失败时抛出错误
   */
  async sendMessage(config: LlmConfig, userMessage: string): Promise<string | null> {
    this.initClient(config)
    
    if (!this.openai) {
      throw new Error('LLM客户端未初始化')
    }

    const messages: ChatMessage[] = [
      { role: 'system', content: LLM_CONFIG.SYSTEM_PROMPT },
      { role: 'user', content: userMessage }
    ]

    try {
      console.log('发送LLM请求:', { model: config.model, message: userMessage })
      
      const completion = await this.openai.chat.completions.create({
        messages,
        model: config.model,
        ...(config.user && { user: config.user })
      })

      const response = completion.choices[0]?.message?.content
      console.log('LLM响应:', response)
      
      return response || null
    } catch (error) {
      console.error('LLM请求失败:', error)
      throw error
    }
  }

  /**
   * 流式发送消息（预留接口）
   * @param config - LLM配置对象
   * @param config.apiKey - API密钥
   * @param config.model - 模型名称
   * @param config.baseURL - 可选的基础URL
   * @param userMessage - 用户输入的消息内容
   * @param chatHistory - 聊天历史记录（可选）
   * @returns Promise<AsyncIterable<string>> - 返回异步可迭代的字符串流
   * @throws {Error} - 当LLM客户端未初始化或请求失败时抛出错误
   */
  async sendMessageWithStream(config: LlmConfig, userMessage: string, chatHistory?: ChatMessage[]): Promise<AsyncIterable<string>> {
    this.initClient(config)
    
    if (!this.openai) {
      throw new Error('LLM客户端未初始化')
    }

    const messages: ChatMessage[] = [
      { role: 'system', content: LLM_CONFIG.SYSTEM_PROMPT }
    ]
    
    // 添加聊天历史（如果有）
    if (chatHistory && chatHistory.length > 0) {
      messages.push(...chatHistory)
    }
    
    // 添加当前用户消息
    messages.push({ role: 'user', content: userMessage })

    try {
      const stream = await this.openai.chat.completions.create({
        messages,
        model: config.model,
        stream: true,
        ...(config.user && { user: config.user })
      })

      return (async function* () {
        try {
          for await (const part of stream) {
            const content = part.choices[0]?.delta?.content
            if (content) {
              yield content
            }
          }
        } catch (error) {
          console.error('流式读取失败:', error)
          throw error
        }
      })()
    } catch (error: any) {
      console.error('LLM流式请求失败:', error)
      // 提取详细错误信息
      let errorMessage = 'LLM请求失败'
      if (error?.message) {
        errorMessage = error.message
      } else if (error?.error?.message) {
        errorMessage = error.error.message
      } else if (typeof error === 'string') {
        errorMessage = error
      } else if (error?.toString) {
        errorMessage = error.toString()
      }
      
      // 添加状态码和错误类型信息
      if (error?.status) {
        errorMessage += ` (状态码: ${error.status})`
      }
      if (error?.code) {
        errorMessage += ` (错误代码: ${error.code})`
      }
      if (error?.type) {
        errorMessage += ` (错误类型: ${error.type})`
      }
      
      throw new Error(errorMessage)
    }
  }
}

export const llmService = new LlmService()