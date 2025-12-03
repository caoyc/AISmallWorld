import type { Background } from '../types'

const API_BASE_URL = 'http://localhost:3001/api'

// 获取背景列表
export async function getBackgrounds(apiKey: string): Promise<Background[]> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/backgrounds?apiKey=${encodeURIComponent(apiKey)}`)
  
  if (!response.ok) {
    let errorMessage = '获取背景列表失败'
    try {
      const error = await response.json()
      errorMessage = error.error || errorMessage
    } catch {
      errorMessage = `请求失败: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }
  
  const result = await response.json()
  return result.data || []
}

// 上传背景图像
export async function uploadBackground(
  apiKey: string,
  file: File,
  name?: string
): Promise<Background> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  if (!file) {
    throw new Error('请选择图片文件')
  }
  
  const formData = new FormData()
  formData.append('file', file)
  formData.append('apiKey', apiKey)
  if (name) {
    formData.append('name', name)
  }
  
  const response = await fetch(`${API_BASE_URL}/backgrounds`, {
    method: 'POST',
    body: formData
  })
  
  if (!response.ok) {
    let errorMessage = '上传背景失败'
    try {
      const error = await response.json()
      errorMessage = error.error || errorMessage
    } catch {
      errorMessage = `请求失败: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }
  
  const result = await response.json()
  return result.data
}

// 从URL创建背景（保存当前背景）
export async function createBackgroundFromUrl(
  apiKey: string,
  url: string,
  name?: string
): Promise<Background> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  if (!url || !url.trim()) {
    throw new Error('URL不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/backgrounds/from-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      apiKey,
      url: url.trim(),
      name: name || undefined
    })
  })
  
  if (!response.ok) {
    let errorMessage = '保存背景失败'
    try {
      const error = await response.json()
      errorMessage = error.error || errorMessage
    } catch {
      errorMessage = `请求失败: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }
  
  const result = await response.json()
  return result.data
}

// 更新背景信息
export async function updateBackground(
  id: number,
  apiKey: string,
  name?: string
): Promise<Background> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/backgrounds/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      apiKey,
      name: name || undefined
    })
  })
  
  if (!response.ok) {
    let errorMessage = '更新背景失败'
    try {
      const error = await response.json()
      errorMessage = error.error || errorMessage
    } catch {
      errorMessage = `请求失败: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }
  
  const result = await response.json()
  return result.data
}

// 删除背景
export async function deleteBackground(id: number, apiKey: string): Promise<void> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/backgrounds/${id}?apiKey=${encodeURIComponent(apiKey)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    let errorMessage = '删除背景失败'
    try {
      const error = await response.json()
      errorMessage = error.error || errorMessage
    } catch {
      errorMessage = `请求失败: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }
}

