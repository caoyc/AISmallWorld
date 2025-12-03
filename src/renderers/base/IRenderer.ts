// 渲染器接口定义
// 所有角色渲染器（立绘、数字人等）都必须实现此接口

export interface IRendererConfig {
  roleId: string
  roleType: 'illustration' | 'digital_human' | string
  positionX: number
  positionY: number
  scale: number
  [key: string]: any  // 允许扩展特定配置
}

export interface IRendererState {
  visible: boolean
  connected?: boolean  // 数字人等需要连接的类型
  [key: string]: any
}

export interface IRenderer {
  // 初始化
  init(config: IRendererConfig): Promise<void>
  
  // 渲染
  render(container: HTMLElement): Promise<void>
  
  // 更新配置
  updateConfig(config: Partial<IRendererConfig>): Promise<void>
  
  // 显示/隐藏
  show(): void
  hide(): void
  toggle(): void
  
  // 拖拽支持
  enableDrag(): void
  disableDrag(): void
  onDragStart(callback: (event: MouseEvent) => void): void
  onDragMove(callback: (event: MouseEvent) => void): void
  onDragEnd(callback: (event: MouseEvent) => void): void
  
  // 连接/断开（可选，仅适用于需要连接的类型）
  connect?(): Promise<void>
  disconnect?(): Promise<void>
  
  // 获取状态
  getState(): IRendererState
  
  // 获取配置
  getConfig(): IRendererConfig
  
  // 清理
  destroy(): void
}

