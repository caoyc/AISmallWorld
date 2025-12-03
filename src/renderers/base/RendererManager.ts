// 渲染器管理器
// 负责创建、管理和销毁所有渲染器实例

import type { IRenderer, IRendererConfig } from './IRenderer'

export type RendererFactory = (config: IRendererConfig) => IRenderer

export class RendererManager {
  private renderers: Map<string, IRenderer> = new Map()
  
  // 注册渲染器工厂
  private factories: Map<string, RendererFactory> = new Map()
  
  /**
   * 注册渲染器工厂
   * @param type 渲染器类型（如 'illustration', 'digital_human'）
   * @param factory 工厂函数
   */
  registerFactory(type: string, factory: RendererFactory): void {
    this.factories.set(type, factory)
  }
  
  /**
   * 创建渲染器
   * @param roleId 角色ID（用于唯一标识渲染器实例）
   * @param config 渲染器配置
   * @returns 渲染器实例
   */
  async createRenderer(roleId: string, config: IRendererConfig): Promise<IRenderer> {
    const factory = this.factories.get(config.roleType)
    if (!factory) {
      throw new Error(`Unknown renderer type: ${config.roleType}`)
    }
    
    // 如果已存在，先销毁
    if (this.renderers.has(roleId)) {
      this.destroyRenderer(roleId)
    }
    
    const renderer = factory(config)
    await renderer.init(config)
    this.renderers.set(roleId, renderer)
    return renderer
  }
  
  /**
   * 获取渲染器
   * @param roleId 角色ID
   * @returns 渲染器实例或undefined
   */
  getRenderer(roleId: string): IRenderer | undefined {
    return this.renderers.get(roleId)
  }
  
  /**
   * 销毁渲染器
   * @param roleId 角色ID
   */
  destroyRenderer(roleId: string): void {
    const renderer = this.renderers.get(roleId)
    if (renderer) {
      renderer.destroy()
      this.renderers.delete(roleId)
    }
  }
  
  /**
   * 销毁所有渲染器
   */
  destroyAll(): void {
    for (const [roleId, renderer] of this.renderers) {
      renderer.destroy()
    }
    this.renderers.clear()
  }
  
  /**
   * 获取所有渲染器
   * @returns 所有渲染器的Map
   */
  getAllRenderers(): Map<string, IRenderer> {
    return new Map(this.renderers)
  }
}

// 单例实例
export const rendererManager = new RendererManager()

