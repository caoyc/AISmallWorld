import type { TtsConfig, TtsService } from '../types'
import { DEFAULT_VOICE } from '../constants/tts'


/**
 * 豆包TTS服务实现
 */
export class DoubaoTtsService implements TtsService {
  /**
   * 合成语音
   * @param text 要合成的文本内容
   * @param config TTS配置
   * @returns 音频数据的ArrayBuffer
   */
  async synthesize(text: string, config: TtsConfig): Promise<ArrayBuffer> {
    if (!config.apiKey) {
      throw new Error('API Key不能为空')
    }
    
    const voiceType = config.voice || DEFAULT_VOICE
    
    console.debug('Doubao TTS request', {
      voice: voiceType,
      text: text.substring(0, 50) + '...',
      speed: config.speed,
      volume: config.volume
    })
    
    // 通过后端代理API调用（避免CORS问题）
    const response = await fetch('http://localhost:3001/api/doubao/generate-voice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        apiKey: config.apiKey,
        text: text || '',
        voice: voiceType,
        speed: config.speed ?? 1.0,
        volume: config.volume ?? 1.0,
      })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.warn('Doubao TTS request failed', response.statusText, errorText)
      throw new Error(`TTS API请求失败: ${response.status} ${response.statusText} - ${errorText}`)
    }
    
    // 后端返回的是音频数据的ArrayBuffer（已经是解码后的二进制数据）
    const audioArrayBuffer = await response.arrayBuffer()
    return audioArrayBuffer
  }
}

/**
 * TTS服务工厂
 */
export class TtsServiceFactory {
  /**
   * 创建TTS服务实例
   * @param provider TTS引擎名称
   * @returns TTS服务实例
   */
  static create(provider: string): TtsService {
    switch (provider) {
      case 'doubao':
        return new DoubaoTtsService()
      default:
        throw new Error(`不支持的TTS引擎: ${provider}`)
    }
  }
}

