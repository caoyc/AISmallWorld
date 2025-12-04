import type { TtsConfig, TtsService } from '../types'
import { DEFAULT_VOICE } from '../constants/tts'
import { splitRecursive } from '../utils'


/**
 * 豆包TTS服务实现
 */
export class DoubaoTtsService implements TtsService {
  /**
   * 合成语音
   * @param text 要合成的文本内容
   * @param config TTS配置
   * @returns 音频数据的ArrayBuffer（单个）或ArrayBuffer[]（多个片段，需要依次播放）
   */
  async synthesize(text: string, config: TtsConfig): Promise<ArrayBuffer | ArrayBuffer[]> {
    if (!config.apiKey) {
      throw new Error('API Key不能为空')
    }
    
    const voiceType = config.voice || DEFAULT_VOICE
    
    // 使用中英文标点符号作为分隔符，按优先级排序
    // 分割策略：
    // 1. 优先按段落分割（\n\n），然后按行分割（\n）
    // 2. 再按句子分割（中英文句号、问号、感叹号）- 确保每次传送尽可能多的完整句子
    // 3. 如果单句超限，按标点分割（逗号、分号、冒号等）
    // 4. 最后按空格和强制分割（空字符串）- 如果单句仍超限则强制截断
    const delimiters = [
      '\n\n',           // 段落分隔
      '\n',             // 行分隔
      '。', '.',        // 中文句号、英文句号 - 句子结束符
      '？', '?',        // 中文问号、英文问号 - 句子结束符
      '！', '!',        // 中文感叹号、英文感叹号 - 句子结束符
      '，', ',',        // 中文逗号、英文逗号 - 如果单句超限，按逗号分割
      '；', ';',        // 中文分号、英文分号
      '：', ':',        // 中文冒号、英文冒号
      ' ',              // 空格
      ''                // 强制分割（最后手段）- 如果单句超限则强制截断
    ]
    
    // 获取配置的最大长度，如果没有配置则使用默认值（320字符）
    // 测试确定豆包TTS API最大成功长度为349字符，设置320留29字符安全余量
    const maxLength = 320
    
    // 使用splitRecursive分割文本
    // 行为：1. 尽可能合并完整句子（在320字符限制内）
    //       2. 如果单句超过320字符，会递归使用更细粒度分隔符，最终强制截断
    const chunks = splitRecursive(text, maxLength, delimiters)
    
    if (chunks.length > 1) {
      console.debug(`Doubao TTS: 文本已分割为 ${chunks.length} 个片段，最大长度: ${maxLength} 字符`)
    }
    
    // 逐个处理每个文本片段
    const audioChunks: ArrayBuffer[] = []
    
    for (const chunk of chunks) {
      console.debug('Doubao TTS request', {
        voice: voiceType,
        text: chunk.substring(0, 50) + '...',
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
          text: chunk,
          voice: voiceType,
          speed: config.speed ?? 1.0,
          volume: config.volume ?? 1.0,
        })
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Doubao TTS chunk failed:', errorText)
        throw new Error(`TTS API请求失败: ${response.status} ${response.statusText} - ${errorText}`)
      }
      
      // 后端返回的是音频数据的ArrayBuffer（已经是解码后的二进制数据）
      const audioArrayBuffer = await response.arrayBuffer()
      audioChunks.push(audioArrayBuffer)
    }
    
    // 如果有多个chunk，返回数组，让播放逻辑依次播放
    // 注意：不能直接合并MP3文件，因为每个MP3都有独立的文件头，直接拼接会导致播放器无法解析
    if (audioChunks.length === 1) {
      return audioChunks[0]
    }
    
    // 返回多个音频片段数组，需要依次播放
    return audioChunks
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

