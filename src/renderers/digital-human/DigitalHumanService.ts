// 数字人服务类
// 封装数字人SDK的连接、断开等操作

import type { DigitalHumanConfig, DigitalHumanCallbacks, DigitalHumanInstance } from './types'
import { getPromiseState } from '../../utils'
import { SDK_CONFIG, APP_CONFIG } from '../../constants'

export class DigitalHumanService {
  /**
   * 连接数字人SDK
   * @param config 数字人配置
   * @param callbacks 回调函数
   * @param containerId 容器ID
   * @returns SDK实例
   */
  async connect(
    config: DigitalHumanConfig,
    callbacks: DigitalHumanCallbacks,
    containerId: string
  ): Promise<DigitalHumanInstance> {
    const { appId, appSecret } = config
    const { onSubtitleOn, onSubtitleOff, onStateChange } = callbacks

    // 检查SDK是否已加载
    if (!window.XmovAvatar) {
      const error = new Error('XmovAvatar SDK 未加载，请刷新页面重试')
      console.error('SDK未加载:', error)
      throw error
    }

    // 检查容器是否存在
    const container = document.getElementById(containerId)
    if (!container) {
      const error = new Error(`容器元素不存在: #${containerId}`)
      console.error('容器不存在:', error)
      throw error
    }

    console.log('开始连接数字人SDK，容器ID:', containerId, '容器元素:', container)

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
      containerId: `#${containerId}`,
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
    let avatar: DigitalHumanInstance
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
      console.log('准备调用 avatar.init()，容器ID:', containerId, '容器元素:', container)
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
      const errorDetails = error instanceof Error ? error.message : String(error)
      console.error('错误详情:', errorDetails)
      console.error('容器ID:', containerId)
      console.error('容器元素:', container)
      console.error('SDK实例:', avatar)
      throw new Error(`SDK初始化失败: ${errorDetails}`)
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
   * 断开数字人连接
   * @param instance SDK实例
   */
  disconnect(instance: DigitalHumanInstance): void {
    if (!instance) return
    
    try {
      instance.stop()
      instance.destroy()
    } catch (error) {
      console.error('断开连接时出错:', error)
    }
  }
}

