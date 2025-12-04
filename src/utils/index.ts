import { APP_CONFIG } from '../constants'
import md5 from 'md5'

/**
 * 生成随机容器ID
 * @returns {string} - 返回以CONTAINER_为前缀的随机字符串
 */
export function generateContainerId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(8))
  let randomID = ''
  for (let i = 0; i < bytes.length; i++) {
    randomID += bytes[i].toString(16).padStart(2, '0')
  }
  return `${APP_CONFIG.CONTAINER_PREFIX}${randomID}`
}

/**
 * 将字符串转换为MD5哈希（用于生成有效的CSS选择器ID）
 * @param str - 要哈希的字符串
 * @returns {string} - 返回32个十六进制字符的哈希值
 */
export function toMd5(str: string): string {
  return md5(str)
}

/**
 * 延迟函数
 * @param ms - 延迟的毫秒数
 * @returns {Promise<void>} - 返回Promise，在指定时间后解决
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 检查Promise状态
 * @param promise - 要检查的Promise对象
 * @returns {Promise<'pending' | 'fulfilled' | 'rejected'>} - 返回Promise的当前状态
 */
export async function getPromiseState(promise: Promise<any>): Promise<'pending' | 'fulfilled' | 'rejected'> {
  const t = {}
  return await Promise.race([promise, t]).then(
    (v: any) => (v === t ? 'pending' : 'fulfilled'),
    () => 'rejected'
  )
}

/**
 * 生成SSML格式的语音文本
 * @param text - 要转换的文本内容
 * @param options - 语音参数配置
 * @param options.pitch - 音调（默认为1）
 * @param options.speed - 语速（默认为1）
 * @param options.volume - 音量（默认为1）
 * @returns {string} - 返回SSML格式的字符串
 */
export function generateSSML(text: string, options: {
  pitch?: number
  speed?: number
  volume?: number
} = {}): string {
  const { pitch = 1, speed = 1, volume = 1 } = options
  return `<speak pitch="${pitch}" speed="${speed}" volume="${volume}">${text}</speak>`
}

/**
 * 安全的JSON解析
 * @template T - 返回类型
 * @param json - 要解析的JSON字符串
 * @param defaultValue - 解析失败时的默认值
 * @returns {T} - 返回解析结果或默认值
 */
export function safeJsonParse<T>(json: string, defaultValue: T): T {
  try {
    return JSON.parse(json)
  } catch {
    return defaultValue
  }
}

/**
 * 验证配置是否完整
 * @param config - 要验证的配置对象
 * @param requiredFields - 必填字段数组
 * @returns {boolean} - 返回是否所有必填字段都不为空
 */
export function validateConfig(config: Record<string, any>, requiredFields: string[]): boolean {
  return requiredFields.every(field => config[field] && config[field] !== '')
}

/**
 * 从文本中提取 markdown 图像
 * @param text - 要处理的文本
 * @returns {Array<{fullMatch: string, altText: string, imageUrl: string}>} - 返回匹配的图像数组
 */
export function extractMarkdownImages(text: string): Array<{fullMatch: string, altText: string, imageUrl: string}> {
  const markdownImageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g
  const matches: Array<{fullMatch: string, altText: string, imageUrl: string}> = []
  let match

  while ((match = markdownImageRegex.exec(text)) !== null) {
    const [fullMatch, altText, imageUrl] = match
    matches.push({ fullMatch, altText, imageUrl })
  }

  // 重置正则表达式的 lastIndex，确保下次调用时从字符串开头开始匹配
  markdownImageRegex.lastIndex = 0

  // 显示匹配到的最后图片的信息
  if (matches.length > 0) {
    const lastImage = matches[matches.length - 1]
    console.log('匹配到的最后图片信息:', lastImage)
  }

  return matches
}

/**
 * 从文本中移除 markdown 图像标记
 * @param text - 要处理的文本
 * @returns {string} - 返回移除图像标记后的文本
 */
export function removeMarkdownImages(text: string): string {
  const markdownImageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g
  return text.replace(markdownImageRegex, '').trim()
}
