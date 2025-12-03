import type { UserRole } from '../types'

const API_BASE_URL = 'http://localhost:3001/api'

// 获取用户角色列表
export async function getUserRoles(apiKey: string): Promise<UserRole[]> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/user-roles?apiKey=${encodeURIComponent(apiKey)}`)
  
  if (!response.ok) {
    let errorMessage = '获取用户角色列表失败'
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

// 创建用户角色
export async function createUserRole(
  apiKey: string,
  role: Omit<UserRole, 'id' | 'apiKey' | 'isCurrent' | 'createdAt' | 'updatedAt'>
): Promise<UserRole> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/user-roles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...role,
        apiKey
      })
    })
    
    if (!response.ok) {
      let errorMessage = '创建用户角色失败'
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
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
    throw new Error('创建用户角色失败: ' + String(error))
  }
}

// 更新用户角色
export async function updateUserRole(
  id: number,
  apiKey: string,
  updates: Partial<Omit<UserRole, 'id' | 'apiKey' | 'isCurrent' | 'createdAt' | 'updatedAt'>>
): Promise<UserRole> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/user-roles/${id}?apiKey=${encodeURIComponent(apiKey)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '更新用户角色失败' }))
    throw new Error(error.error || '更新用户角色失败')
  }
  
  const result = await response.json()
  return result.data
}

// 删除用户角色
export async function deleteUserRole(id: number, apiKey: string): Promise<void> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/user-roles/${id}?apiKey=${encodeURIComponent(apiKey)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '删除用户角色失败' }))
    throw new Error(error.error || '删除用户角色失败')
  }
}

// 设置当前用户角色
export async function setCurrentUserRole(id: number, apiKey: string): Promise<UserRole> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/user-roles/${id}/set-current?apiKey=${encodeURIComponent(apiKey)}`, {
    method: 'PUT'
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '设置当前用户角色失败' }))
    throw new Error(error.error || '设置当前用户角色失败')
  }
  
  const result = await response.json()
  return result.data
}

