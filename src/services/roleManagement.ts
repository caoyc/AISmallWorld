import type { Role } from '../types'

const API_BASE_URL = 'http://localhost:3001/api'

/**
 * 获取用户ID（与聊天历史保持一致）
 * 
 * 说明：
 * - apiKey: 用户的账号标识
 * - user: 用于区分不同会话/角色（可选）
 * - 返回值：
 *   - 如果user为空：返回 apiKey（表示这是用户的主账号）
 *   - 如果user不为空：返回 apiKey:user（表示这是用户的某个角色/会话）
 * 
 * 在角色管理中：
 * - 创建/更新角色时，传空字符串作为user参数，这样userId = apiKey
 * - 这样设计是为了让同一个apiKey下的所有角色都使用相同的userId（apiKey）
 * - 角色的user字段（传给大模型的user参数）是另一个概念，存储在roles表的user字段中
 */
function getUserId(apiKey: string, user: string): string {
  if (!user || user.trim() === '') {
    return apiKey
  }
  return `${apiKey}:${user}`
}

// 获取所有角色
export async function getRoles(apiKey: string): Promise<Role[]> {
  if (!apiKey || !apiKey.trim()) {
    throw new Error('API Key不能为空')
  }
  
  const response = await fetch(`${API_BASE_URL}/roles?apiKey=${encodeURIComponent(apiKey)}`)
  
  if (!response.ok) {
    let errorMessage = '获取角色列表失败'
    try {
      const error = await response.json()
      errorMessage = error.error || errorMessage
    } catch {
      // 如果响应不是JSON，使用状态文本
      errorMessage = `请求失败: ${response.status} ${response.statusText}`
    }
    throw new Error(errorMessage)
  }
  
  const result = await response.json()
  return result.data || []
}

// 创建角色
export async function createRole(
  apiKey: string,
  role: Omit<Role, 'id' | 'createdAt' | 'updatedAt'>
): Promise<Role> {
  try {
    const response = await fetch(`${API_BASE_URL}/roles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...role,
        apiKey
      })
    })
    
    if (!response.ok) {
      let errorMessage = '创建角色失败'
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
    throw new Error('创建角色失败: ' + String(error))
  }
}

// 更新角色
export async function updateRole(
  id: number,
  apiKey: string,
  updates: Partial<Omit<Role, 'id' | 'createdAt' | 'updatedAt'>>
): Promise<Role> {
  const response = await fetch(`${API_BASE_URL}/roles/${id}?apiKey=${encodeURIComponent(apiKey)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '更新角色失败' }))
    throw new Error(error.error || '更新角色失败')
  }
  
  const result = await response.json()
  return result.data
}

// 删除角色
export async function deleteRole(id: number, apiKey: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/roles/${id}?apiKey=${encodeURIComponent(apiKey)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '删除角色失败' }))
    throw new Error(error.error || '删除角色失败')
  }
}

