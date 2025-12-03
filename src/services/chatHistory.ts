import type { ChatMessage } from '../types'

// ==================== 配置区域 ====================
// 后端API配置
const API_BASE_URL = 'http://localhost:3001/api'

/**
 * 生成用户ID（账号）
 * 格式：{api_key}:{user}
 * 当user为空时，仅使用 {api_key}
 */
function getUserId(apiKey: string, user: string): string {
  if (!user || user.trim() === '') {
    return apiKey
  }
  return `${apiKey}:${user}`
}

// ==================== API调用函数 ====================

/**
 * 保存对话消息
 */
export async function saveChatMessage(
  role: 'user' | 'assistant' | 'system',
  content: string,
  apiKey: string,
  user: string,
  timestamp?: number,
  characterId?: string
): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role,
      content,
      userId,
      characterId,
      timestamp: timestamp || Date.now()
    })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '保存消息失败' }))
    throw new Error(error.error || '保存消息失败')
  }
}

/**
 * 获取对话历史
 */
export async function getChatHistory(
  apiKey: string,
  user: string,
  limit: number = 50,
  offset: number = 0,
  before?: number,
  after?: number
): Promise<ChatMessage[]> {
  const userId = getUserId(apiKey, user)
  const params = new URLSearchParams({
    userId,
    limit: limit.toString(),
    offset: offset.toString()
  })
  if (before) params.append('before', before.toString())
  if (after) params.append('after', after.toString())
  
  const response = await fetch(`${API_BASE_URL}/chat/messages?${params}`)
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '获取历史记录失败' }))
    throw new Error(error.error || '获取历史记录失败')
  }
  
  const data = await response.json()
  return data.data.messages || []
}

/**
 * 更新消息
 */
export async function updateChatMessage(
  id: number,
  content: string,
  characterId?: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/messages/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, characterId })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '更新消息失败' }))
    throw new Error(error.error || '更新消息失败')
  }
}

/**
 * 删除消息
 */
export async function deleteChatMessage(
  id: number,
  apiKey: string,
  user: string
): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages/${id}?userId=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '删除消息失败' }))
    throw new Error(error.error || '删除消息失败')
  }
}

/**
 * 清空对话历史
 */
export async function clearChatHistory(apiKey: string, user: string): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages?userId=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '清空聊天记录失败' }))
    throw new Error(error.error || '清空聊天记录失败')
  }
}

/**
 * 同步内存历史到数据库
 */
export async function syncMemoryHistory(
  messages: ChatMessage[],
  apiKey: string,
  user: string
): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, messages })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '同步历史记录失败' }))
    throw new Error(error.error || '同步历史记录失败')
  }
}
