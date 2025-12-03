// 数字人渲染器实现
// 实现 IRenderer 接口，提供数字人的渲染、连接、断开等功能

import { BaseRenderer } from '../base/BaseRenderer'
import type { IRendererConfig } from '../base/IRenderer'
import { DigitalHumanService } from './DigitalHumanService'
import type { DigitalHumanCallbacks, DigitalHumanInstance } from './types'

export interface DigitalHumanRendererConfig extends IRendererConfig {
  avatarAppId?: string
  avatarAppSecret?: string
  containerId?: string // 容器ID从外部传入
}

export class DigitalHumanRenderer extends BaseRenderer {
  private service: DigitalHumanService
  private containerId: string
  private instance: DigitalHumanInstance | null = null
  private callbacks: DigitalHumanCallbacks | null = null

  constructor(config: IRendererConfig) {
    super(config)
    this.service = new DigitalHumanService()
    // 容器ID从配置中传入，或根据roleId判断（固定ID）
    const rendererConfig = config as DigitalHumanRendererConfig
    if (rendererConfig.containerId) {
      this.containerId = rendererConfig.containerId
    } else {
      // 根据roleId前缀判断是伙伴还是用户，使用固定容器ID
      if (config.roleId.startsWith('partner:')) {
        this.containerId = 'digital-human-partner'
      } else if (config.roleId.startsWith('user:')) {
        this.containerId = 'digital-human-user'
      } else {
        throw new Error(`无法确定容器ID，roleId格式不正确: ${config.roleId}`)
      }
    }
  }

  async render(container: HTMLElement): Promise<void> {
    this.container = container
    
    console.log('[DigitalHumanRenderer.render] roleId:', this.config.roleId, 'containerId:', this.containerId, '传入container.id:', container.id)
    
    // 容器已在模板中定义，这里只需要检查容器是否存在
    const digitalHumanContainer = document.getElementById(this.containerId)
    if (!digitalHumanContainer) {
      console.error('[DigitalHumanRenderer.render] 容器不存在, containerId:', this.containerId, '当前DOM中的容器:', Array.from(document.querySelectorAll('.sdk-container')).map(el => el.id))
      throw new Error(`数字人容器不存在: #${this.containerId}，请确保容器已在模板中定义`)
    }
    
    console.log('[DigitalHumanRenderer.render] 找到容器, containerId:', this.containerId, '容器元素ID:', digitalHumanContainer.id, '传入container与找到的容器是否相同:', container === digitalHumanContainer)
    
    // 样式由Vue的计算属性管理，不需要手动更新
  }

  async connect(): Promise<void> {
    if (this.instance) {
      return // 已连接
    }

    const config = this.config as DigitalHumanRendererConfig
    
    if (!config.avatarAppId || !config.avatarAppSecret) {
      throw new Error('数字人 App ID 和 App Secret 未配置')
    }

    if (!this.callbacks) {
      throw new Error('回调函数未设置，请先设置回调函数')
    }

    // 确保容器存在
    if (!this.container) {
      throw new Error('容器未初始化，请先调用 render()')
    }

    const containerElement = document.getElementById(this.containerId)
    if (!containerElement) {
      console.error('[DigitalHumanRenderer.connect] 容器元素不存在，容器ID:', this.containerId)
      console.error('[DigitalHumanRenderer.connect] 当前DOM中的容器:', Array.from(document.querySelectorAll('.sdk-container')).map(el => ({ id: el.id, className: el.className })))
      throw new Error(`容器元素不存在: #${this.containerId}，请确保已调用 render() 方法`)
    }

    console.log('[DigitalHumanRenderer.connect] 准备连接数字人, roleId:', this.config.roleId, 'containerId:', this.containerId, '容器元素ID:', containerElement.id, 'this.container.id:', this.container?.id)
    console.log('[DigitalHumanRenderer.connect] 配置:', { appId: config.avatarAppId, appSecret: config.avatarAppSecret ? '***' : '未设置' })
    console.log('[DigitalHumanRenderer.connect] 传递给SDK的containerId:', this.containerId)

    this.instance = await this.service.connect(
      {
        appId: config.avatarAppId,
        appSecret: config.avatarAppSecret
      },
      this.callbacks,
      this.containerId
    )
    
    console.log('[DigitalHumanRenderer.connect] SDK连接成功, 使用的containerId:', this.containerId)

    this.state.connected = true
  }

  async disconnect(): Promise<void> {
    if (!this.instance) {
      return // 未连接
    }

    this.service.disconnect(this.instance)
    this.instance = null
    this.state.connected = false
  }

  /**
   * 设置回调函数
   */
  setCallbacks(callbacks: DigitalHumanCallbacks): void {
    this.callbacks = callbacks
  }

  /**
   * 获取SDK实例（用于截图等操作）
   */
  getInstance(): DigitalHumanInstance | null {
    return this.instance
  }

  protected async onConfigUpdated(): Promise<void> {
    // 配置更新时，样式由Vue的计算属性自动更新，不需要手动更新
  }

  protected onVisibilityChanged(visible: boolean): void {
    if (this.container) {
      const element = document.getElementById(this.containerId)
      if (element) {
        if (visible) {
          element.classList.add('visible')
        } else {
          element.classList.remove('visible')
        }
      }
    }
  }

  destroy(): void {
    // 断开连接
    if (this.instance) {
      this.disconnect()
    }

    // 容器由Vue管理，不需要手动移除

    this.container = null
    this.instance = null
    this.callbacks = null
  }
}

