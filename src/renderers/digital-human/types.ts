// 数字人渲染器类型定义

export interface DigitalHumanConfig {
  appId: string
  appSecret: string
  containerId?: string
}

export interface DigitalHumanCallbacks {
  onSubtitleOn: (text: string) => void
  onSubtitleOff: () => void
  onStateChange: (state: string) => void
}

export interface DigitalHumanInstance {
  stop: () => void
  destroy: () => void
  [key: string]: any
}

