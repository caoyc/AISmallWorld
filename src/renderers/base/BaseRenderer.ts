// 基础渲染器抽象类
// 提供通用的渲染器功能，子类可以覆盖特定方法

import type { IRenderer, IRendererConfig, IRendererState } from './IRenderer'

export abstract class BaseRenderer implements IRenderer {
  protected config: IRendererConfig
  protected state: IRendererState
  protected container: HTMLElement | null = null
  protected dragEnabled: boolean = false
  protected dragCallbacks: {
    onStart?: (event: MouseEvent) => void
    onMove?: (event: MouseEvent) => void
    onEnd?: (event: MouseEvent) => void
  } = {}

  constructor(config: IRendererConfig) {
    this.config = config
    this.state = {
      visible: false
    }
  }

  // 抽象方法，子类必须实现
  abstract render(container: HTMLElement): Promise<void>
  abstract destroy(): void

  // 通用方法，子类可以覆盖
  async init(config: IRendererConfig): Promise<void> {
    this.config = { ...this.config, ...config }
    await this.onConfigUpdated()
  }

  async updateConfig(config: Partial<IRendererConfig>): Promise<void> {
    this.config = { ...this.config, ...config }
    await this.onConfigUpdated()
  }

  show(): void {
    this.state.visible = true
    this.onVisibilityChanged(true)
  }

  hide(): void {
    this.state.visible = false
    this.onVisibilityChanged(false)
  }

  toggle(): void {
    if (this.state.visible) {
      this.hide()
    } else {
      this.show()
    }
  }

  enableDrag(): void {
    this.dragEnabled = true
  }

  disableDrag(): void {
    this.dragEnabled = false
  }

  onDragStart(callback: (event: MouseEvent) => void): void {
    this.dragCallbacks.onStart = callback
  }

  onDragMove(callback: (event: MouseEvent) => void): void {
    this.dragCallbacks.onMove = callback
  }

  onDragEnd(callback: (event: MouseEvent) => void): void {
    this.dragCallbacks.onEnd = callback
  }

  getState(): IRendererState {
    return { ...this.state }
  }

  getConfig(): IRendererConfig {
    return { ...this.config }
  }

  // 钩子方法，子类可以覆盖
  protected async onConfigUpdated(): Promise<void> {}
  protected onVisibilityChanged(visible: boolean): void {}
}

