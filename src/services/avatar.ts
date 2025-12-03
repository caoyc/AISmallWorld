import type { AvatarConfig } from '../types'
import { generateContainerId, getPromiseState } from '../utils'
import { SDK_CONFIG, APP_CONFIG } from '../constants'

interface AvatarCallbacks {
  onSubtitleOn: (text: string) => void
  onSubtitleOff: () => void
  onStateChange: (state: string) => void
}

class AvatarService {
  private containerId: string

  constructor() {
    this.containerId = generateContainerId()
  }

  /**
   * 获取容器ID
   * @returns {string} - 返回随机生成的容器ID
   */
  getContainerId(): string {
    return this.containerId
  }

  /**
   * 连接虚拟人SDK
   * @param config - 虚拟人配置对象
   * @param config.appId - 应用ID
   * @param config.appSecret - 应用密钥
   * @param callbacks - 回调函数集合
   * @param callbacks.onSubtitleOn - 字幕显示回调
   * @param callbacks.onSubtitleOff - 字幕隐藏回调
   * @param callbacks.onStateChange - 状态变化回调
   * @param containerId - 可选的容器ID，如果不提供则使用默认容器ID
   * @returns {Promise<any>} - 返回虚拟人SDK实例
   * @throws {Error} - 当连接失败时抛出错误
   */
  async connect(config: AvatarConfig, callbacks: AvatarCallbacks, containerId?: string): Promise<any> {
    const { appId, appSecret } = config
    const { onSubtitleOn, onSubtitleOff, onStateChange } = callbacks

    // 检查SDK是否已加载
    if (!window.XmovAvatar) {
      const error = new Error('XmovAvatar SDK 未加载，请刷新页面重试')
      console.error('SDK未加载:', error)
      throw error
    }

    // 使用提供的容器ID或默认容器ID
    const targetContainerId = containerId || this.containerId
    
    // 检查容器是否存在
    const container = document.getElementById(targetContainerId)
    if (!container) {
      const error = new Error(`容器元素不存在: #${targetContainerId}`)
      console.error('容器不存在:', error)
      throw error
    }

    console.log('开始连接数字人SDK，容器ID:', targetContainerId, '容器元素:', container)

    // 构建网关URL
    const url = new URL(SDK_CONFIG.GATEWAY_URL)
    url.searchParams.append('data_source', SDK_CONFIG.DATA_SOURCE)
    url.searchParams.append('custom_id', SDK_CONFIG.CUSTOM_ID)

    console.log('网关URL:', url.toString())

    // 连接Promise管理
    let resolve: (value: boolean) => void
    let reject: (reason?: any) => void
    const connectPromise = new Promise<boolean>((res, rej) => {
      resolve = res
      reject = rej
    })

    // SDK构造选项
    const constructorOptions = {
      containerId: `#${targetContainerId}`,
      appId,
      appSecret,
      enableDebugger: false,
      gatewayServer: url.toString(),
      onWidgetEvent: (event: any) => {
        console.log('SDK事件:', event)
        if (event.type === 'subtitle_on') {
          onSubtitleOn(event.text)
        } else if (event.type === 'subtitle_off') {
          onSubtitleOff()
        }
      },
      onStateChange,
      onMessage: async (error: any) => {
        console.error('SDK错误消息:', error)
        const state = await getPromiseState(connectPromise)
        const plainError = new Error(error?.message || error?.toString() || 'SDK连接错误')
        if (state === 'pending') {
          reject(plainError)
        }
      }
    }

    console.log('创建SDK实例，配置:', { ...constructorOptions, appSecret: '***' })

    // 创建SDK实例
    let avatar: any
    try {
      avatar = new window.XmovAvatar(constructorOptions)
      console.log('SDK实例创建成功')
    } catch (error) {
      console.error('创建SDK实例失败:', error)
      throw new Error(`创建SDK实例失败: ${error instanceof Error ? error.message : String(error)}`)
    }
    
    // 等待初始化
    await new Promise(resolve => {
      setTimeout(resolve, APP_CONFIG.AVATAR_INIT_TIMEOUT)
    })

    console.log('开始初始化SDK...')

    // 初始化SDK
    try {
    await avatar.init({
      onDownloadProgress: (progress: number) => {
        console.log(`初始化进度: ${progress}%`)
        if (progress >= 100) {
            console.log('初始化进度完成，等待连接确认...')
          resolve(true)
        }
      },
      onClose: () => {
        onStateChange('')
        console.log('SDK连接关闭')
      }
    })
      console.log('SDK init() 调用完成')
    } catch (error) {
      console.error('SDK初始化失败:', error)
      throw new Error(`SDK初始化失败: ${error instanceof Error ? error.message : String(error)}`)
    }

    // 等待连接完成（增加超时时间）
    const timeout = 10000 // 10秒超时
    const [result] = await Promise.allSettled([
      connectPromise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('连接超时')), timeout))
    ])

    if (result.status === 'rejected') {
      const error = result.reason instanceof Error ? result.reason : new Error(String(result.reason))
      console.error('SDK连接失败:', error)
      throw error
    }

    if (result.status === 'fulfilled' && result.value === true) {
      console.log('SDK连接成功')
    return avatar
    }

    // 如果连接Promise没有resolve，但也没有reject，可能是超时或其他问题
    throw new Error('SDK连接未完成，请检查网络连接和配置信息')
  }

  /**
   * 断开虚拟人连接
   * @param avatar - 虚拟人SDK实例
   * @returns {void}
   */
  disconnect(avatar: any): void {
    if (!avatar) return
    
    try {
      avatar.stop()
      avatar.destroy()
    } catch (error) {
      console.error('断开连接时出错:', error)
    }
  }

}

export const avatarService = new AvatarService()