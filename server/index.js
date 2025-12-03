import express from 'express'
import cors from 'cors'
import multer from 'multer'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'
import { randomUUID } from 'node:crypto'
// Node.js 18+ 内置了 fetch，无需导入
import { 
  initDatabase, 
  saveMessage, 
  saveMessagesBatch,
  getHistory, 
  updateMessage,
  deleteMessage,
  clearHistory,
  syncMessages,
  getRoles,
  createRole,
  updateRole,
  deleteRole,
  getUserRoles,
  createUserRole,
  updateUserRole,
  deleteUserRole,
  setCurrentUserRole,
  getBackgrounds,
  createBackground,
  updateBackground,
  deleteBackground
} from './db.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = 3001

// 创建上传目录
const UPLOAD_DIR = path.join(__dirname, '../uploads/avatars')
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true })
}

// 创建背景上传目录
const BACKGROUND_UPLOAD_DIR = path.join(__dirname, '../uploads/backgrounds')
if (!fs.existsSync(BACKGROUND_UPLOAD_DIR)) {
  fs.mkdirSync(BACKGROUND_UPLOAD_DIR, { recursive: true })
}

// 配置multer用于文件上传
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOAD_DIR)
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9)
    const ext = path.extname(file.originalname)
    cb(null, `avatar-${uniqueSuffix}${ext}`)
  }
})

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB限制，支持8K高清图
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true)
    } else {
      cb(new Error('只允许上传图片文件'))
    }
  }
})

// 配置背景上传的multer
const backgroundStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, BACKGROUND_UPLOAD_DIR)
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9)
    const ext = path.extname(file.originalname)
    cb(null, `background-${uniqueSuffix}${ext}`)
  }
})

const uploadBackground = multer({
  storage: backgroundStorage,
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB限制
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true)
    } else {
      cb(new Error('只允许上传图片文件'))
    }
  }
})

app.use(cors())
app.use(express.json())
// 静态文件服务，提供上传的图片访问
app.use('/uploads', express.static(path.join(__dirname, '../uploads')))

// 初始化数据库
initDatabase()

// 验证账号格式
function validateUserId(userId) {
  if (!userId || typeof userId !== 'string') {
    return false
  }
  // 账号格式：{api_key} 或 {api_key}:{user}
  // 至少包含api_key部分
  return userId.trim().length > 0
}

// 保存单条消息
app.post('/api/chat/messages', async (req, res) => {
  try {
    const { role, content, userId, characterId, timestamp } = req.body
    
    if (!role || !content || !userId) {
      return res.status(400).json({ error: 'role, content, and userId are required' })
    }
    
    if (!validateUserId(userId)) {
      return res.status(400).json({ error: 'Invalid userId format' })
    }
    
    if (!['user', 'assistant', 'system'].includes(role)) {
      return res.status(400).json({ error: 'Invalid role' })
    }
    
    const message = saveMessage(userId, role, content, timestamp, characterId)
    res.json({ success: true, data: message })
  } catch (error) {
    console.error('保存消息失败:', error)
    res.status(500).json({ error: error.message })
  }
})

// 批量保存消息
app.post('/api/chat/messages/batch', async (req, res) => {
  try {
    const { userId, messages } = req.body
    
    if (!userId || !messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'userId and messages array are required' })
    }
    
    if (!validateUserId(userId)) {
      return res.status(400).json({ error: 'Invalid userId format' })
    }
    
    const messagesWithUserId = messages.map(msg => ({
      userId,
      role: msg.role,
      content: msg.content,
      characterId: msg.characterId,
      timestamp: msg.timestamp
    }))
    
    const ids = saveMessagesBatch(messagesWithUserId)
    res.json({ success: true, data: { count: ids.length, ids } })
  } catch (error) {
    console.error('批量保存消息失败:', error)
    res.status(500).json({ error: error.message })
  }
})

// 获取聊天历史
app.get('/api/chat/messages', async (req, res) => {
  try {
    const { userId, limit, offset, before, after, role } = req.query
    
    if (!userId) {
      return res.status(400).json({ error: 'userId is required' })
    }
    
    if (!validateUserId(userId)) {
      return res.status(400).json({ error: 'Invalid userId format' })
    }
    
    const options = {
      limit: limit ? parseInt(limit) : 50,
      offset: offset ? parseInt(offset) : 0,
      before: before ? parseInt(before) : null,
      after: after ? parseInt(after) : null,
      role: role || null
    }
    
    const result = getHistory(userId, options)
    res.json({ success: true, data: result })
  } catch (error) {
    console.error('获取历史失败:', error)
    res.status(500).json({ error: error.message })
  }
})

// 更新消息
app.put('/api/chat/messages/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { content, characterId } = req.body
    
    if (!content) {
      return res.status(400).json({ error: 'content is required' })
    }
    
    const message = updateMessage(parseInt(id), content, characterId)
    res.json({ success: true, data: message })
  } catch (error) {
    console.error('更新消息失败:', error)
    if (error.message === '消息不存在') {
      res.status(404).json({ error: error.message })
    } else {
      res.status(500).json({ error: error.message })
    }
  }
})

// 删除单条消息
app.delete('/api/chat/messages/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { userId } = req.query
    
    // 验证userId格式（如果提供）
    if (userId && !validateUserId(userId)) {
      return res.status(400).json({ error: 'Invalid userId format' })
    }
    
    deleteMessage(parseInt(id), userId)
    res.json({ success: true, message: '消息已删除' })
  } catch (error) {
    console.error('删除消息失败:', error)
    if (error.message === '消息不存在' || error.message === '消息不存在或不属于当前用户') {
      res.status(404).json({ error: error.message })
    } else {
      res.status(500).json({ error: error.message })
    }
  }
})

// 清空用户聊天记录
app.delete('/api/chat/messages', async (req, res) => {
  try {
    const { userId } = req.query
    
    if (!userId) {
      return res.status(400).json({ error: 'userId is required' })
    }
    
    if (!validateUserId(userId)) {
      return res.status(400).json({ error: 'Invalid userId format' })
    }
    
    const deletedCount = clearHistory(userId)
    res.json({ 
      success: true, 
      message: '聊天记录已清空',
      data: { deletedCount }
    })
  } catch (error) {
    console.error('清空历史失败:', error)
    res.status(500).json({ error: error.message })
  }
})

// 同步内存历史到数据库
app.post('/api/chat/messages/sync', async (req, res) => {
  try {
    const { userId, messages } = req.body
    
    if (!userId || !messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'userId and messages array are required' })
    }
    
    if (!validateUserId(userId)) {
      return res.status(400).json({ error: 'Invalid userId format' })
    }
    
    const result = syncMessages(userId, messages)
    res.json({ success: true, data: result })
  } catch (error) {
    console.error('同步历史失败:', error)
    res.status(500).json({ error: error.message })
  }
})

// ==================== 文件上传API ====================

// 上传头像图片
app.post('/api/upload/avatar', upload.single('avatar'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: '没有上传文件' })
    }
    
    // 返回图片URL（相对于uploads目录）
    const imageUrl = `/uploads/avatars/${req.file.filename}`
    res.json({ success: true, url: imageUrl })
  } catch (error) {
    console.error('上传头像失败:', error)
    res.status(500).json({ error: error.message || '上传头像失败' })
  }
})

// ==================== 角色管理API ====================

// 获取角色列表
app.get('/api/roles', async (req, res) => {
  try {
    const { apiKey } = req.query
    
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roles = getRoles(apiKey)
    res.json({ success: true, data: roles })
  } catch (error) {
    console.error('获取角色列表失败:', error)
    res.status(500).json({ error: error.message || '获取角色列表失败' })
  }
})

// 创建角色
app.post('/api/roles', async (req, res) => {
  try {
    const { apiKey, name, user, type, description, avatar, positionX, positionY, scale, baseURL, model, avatarAppId, avatarAppSecret, ttsProvider, ttsVoice, ttsSpeed, ttsVolume } = req.body
    
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    if (!user || !user.trim()) {
      return res.status(400).json({ error: 'user is required' })
    }
    
    const roleType = type || 'illustration'
    if (!['digital_human', 'illustration'].includes(roleType)) {
      return res.status(400).json({ error: 'Invalid type, must be digital_human or illustration' })
    }
    
    const role = createRole(apiKey, name, user, roleType, description, avatar, positionX, positionY, scale, baseURL, model, avatarAppId, avatarAppSecret)
    
    // 如果提供了语音选项或TTS字段，更新角色
    if (useDigitalHumanVoice !== undefined || ttsProvider !== undefined || ttsVoice !== undefined || ttsSpeed !== undefined || ttsVolume !== undefined) {
      const updates = {}
      if (useDigitalHumanVoice !== undefined) updates.useDigitalHumanVoice = useDigitalHumanVoice
      if (ttsProvider !== undefined) updates.ttsProvider = ttsProvider
      if (ttsVoice !== undefined) updates.ttsVoice = ttsVoice
      if (ttsSpeed !== undefined) updates.ttsSpeed = ttsSpeed
      if (ttsVolume !== undefined) updates.ttsVolume = ttsVolume
      const updatedRole = updateRole(role.id, apiKey, updates)
      res.json({ success: true, data: updatedRole })
    } else {
      res.json({ success: true, data: role })
    }
  } catch (error) {
    console.error('创建角色失败:', error)
    const errorMessage = error.message || '创建角色失败'
    console.error('详细错误:', errorMessage)
    res.status(500).json({ error: errorMessage })
  }
})

// 更新角色
app.put('/api/roles/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey } = req.query
    const { name, user, type, description, avatar, positionX, positionY, scale, baseURL, model, avatarAppId, avatarAppSecret, useDigitalHumanVoice, ttsProvider, ttsVoice, ttsSpeed, ttsVolume, enableVoicePlay, enableAutoPlay, enableAutoSwitch } = req.body
    
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roleId = parseInt(id)
    if (isNaN(roleId)) {
      return res.status(400).json({ error: 'Invalid role id' })
    }
    
    const updates = {}
    if (name !== undefined) updates.name = name
    if (user !== undefined) updates.user = user
    if (type !== undefined) updates.type = type
    if (description !== undefined) updates.description = description
    if (avatar !== undefined) updates.avatar = avatar
    if (positionX !== undefined) updates.positionX = positionX
    if (positionY !== undefined) updates.positionY = positionY
    if (scale !== undefined) updates.scale = scale
    if (baseURL !== undefined) updates.baseURL = baseURL
    if (model !== undefined) updates.model = model
    if (avatarAppId !== undefined) updates.avatarAppId = avatarAppId
    if (avatarAppSecret !== undefined) updates.avatarAppSecret = avatarAppSecret
    if (ttsProvider !== undefined) updates.ttsProvider = ttsProvider
    if (ttsVoice !== undefined) updates.ttsVoice = ttsVoice
    if (ttsSpeed !== undefined) updates.ttsSpeed = ttsSpeed
    if (ttsVolume !== undefined) updates.ttsVolume = ttsVolume
    if (enableVoicePlay !== undefined) updates.enableVoicePlay = enableVoicePlay
    if (enableAutoPlay !== undefined) updates.enableAutoPlay = enableAutoPlay
    if (enableAutoSwitch !== undefined) updates.enableAutoSwitch = enableAutoSwitch
    
    const role = updateRole(roleId, apiKey, updates)
    res.json({ success: true, data: role })
  } catch (error) {
    console.error('更新角色失败:', error)
    res.status(500).json({ error: error.message || '更新角色失败' })
  }
})

// 删除角色
app.delete('/api/roles/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey } = req.query
    
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roleId = parseInt(id)
    if (isNaN(roleId)) {
      return res.status(400).json({ error: 'Invalid role id' })
    }
    
    const deleted = deleteRole(roleId, apiKey)
    if (!deleted) {
      return res.status(404).json({ error: '角色不存在或无权限' })
    }
    
    res.json({ success: true })
  } catch (error) {
    console.error('删除角色失败:', error)
    res.status(500).json({ error: error.message || '删除角色失败' })
  }
})

// ========== 用户角色管理 API ==========

// 获取用户角色列表
app.get('/api/user-roles', async (req, res) => {
  try {
    const { apiKey } = req.query
    
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roles = getUserRoles(apiKey)
    res.json({ success: true, data: roles })
  } catch (error) {
    console.error('获取用户角色列表失败:', error)
    res.status(500).json({ error: error.message || '获取用户角色列表失败' })
  }
})

// 创建用户角色
app.post('/api/user-roles', async (req, res) => {
  try {
    const { apiKey, user, name, type, avatar, positionX, positionY, scale, baseURL, model, avatarAppId, avatarAppSecret, ttsProvider, ttsVoice, ttsSpeed, ttsVolume, ttsPreviewText } = req.body
    
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    if (!user || !user.trim()) {
      return res.status(400).json({ error: 'user字段不能为空' })
    }
    
    const role = createUserRole(apiKey, user, name, type, avatar, positionX, positionY, scale, baseURL, model, avatarAppId, avatarAppSecret)
    
    // 如果提供了语音选项或TTS字段，更新角色
    if (useDigitalHumanVoice !== undefined || ttsProvider !== undefined || ttsVoice !== undefined || ttsSpeed !== undefined || ttsVolume !== undefined || ttsPreviewText !== undefined) {
      const updates = {}
      if (useDigitalHumanVoice !== undefined) updates.useDigitalHumanVoice = useDigitalHumanVoice
      if (ttsProvider !== undefined) updates.ttsProvider = ttsProvider
      if (ttsVoice !== undefined) updates.ttsVoice = ttsVoice
      if (ttsSpeed !== undefined) updates.ttsSpeed = ttsSpeed
      if (ttsVolume !== undefined) updates.ttsVolume = ttsVolume
      if (ttsPreviewText !== undefined) updates.ttsPreviewText = ttsPreviewText
      const updatedRole = updateUserRole(role.id, apiKey, updates)
      res.json({ success: true, data: updatedRole })
    } else {
      res.json({ success: true, data: role })
    }
  } catch (error) {
    console.error('创建用户角色失败:', error)
    res.status(500).json({ error: error.message || '创建用户角色失败' })
  }
})

// 更新用户角色
app.put('/api/user-roles/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey } = req.query
    const { user, name, type, avatar, positionX, positionY, scale, baseURL, model, avatarAppId, avatarAppSecret, useDigitalHumanVoice, ttsProvider, ttsVoice, ttsSpeed, ttsVolume, ttsPreviewText, enableVoicePlay, enableAutoPlay, enableAutoSwitch } = req.body
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roleId = parseInt(id)
    if (isNaN(roleId)) {
      return res.status(400).json({ error: 'Invalid role id' })
    }
    
    const updates = {}
    if (user !== undefined) updates.user = user
    if (name !== undefined) updates.name = name
    if (type !== undefined) updates.type = type
    if (avatar !== undefined) updates.avatar = avatar
    if (positionX !== undefined) updates.positionX = positionX
    if (positionY !== undefined) updates.positionY = positionY
    if (scale !== undefined) updates.scale = scale
    if (baseURL !== undefined) updates.baseURL = baseURL
    if (model !== undefined) updates.model = model
    if (avatarAppId !== undefined) updates.avatarAppId = avatarAppId
    if (avatarAppSecret !== undefined) updates.avatarAppSecret = avatarAppSecret
    if (ttsProvider !== undefined) updates.ttsProvider = ttsProvider
    if (ttsVoice !== undefined) updates.ttsVoice = ttsVoice
    if (ttsSpeed !== undefined) updates.ttsSpeed = ttsSpeed
    if (ttsVolume !== undefined) updates.ttsVolume = ttsVolume
    if (ttsPreviewText !== undefined) updates.ttsPreviewText = ttsPreviewText
    if (enableVoicePlay !== undefined) updates.enableVoicePlay = enableVoicePlay
    if (enableAutoPlay !== undefined) updates.enableAutoPlay = enableAutoPlay
    if (enableAutoSwitch !== undefined) updates.enableAutoSwitch = enableAutoSwitch
    
    const role = updateUserRole(roleId, apiKey, updates)
    res.json({ success: true, data: role })
  } catch (error) {
    console.error('更新用户角色失败:', error)
    res.status(500).json({ error: error.message || '更新用户角色失败' })
  }
})

// 删除用户角色
app.delete('/api/user-roles/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey } = req.query
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roleId = parseInt(id)
    if (isNaN(roleId)) {
      return res.status(400).json({ error: 'Invalid role id' })
    }
    
    deleteUserRole(roleId, apiKey)
    res.json({ success: true })
  } catch (error) {
    console.error('删除用户角色失败:', error)
    res.status(500).json({ error: error.message || '删除用户角色失败' })
  }
})

// 设置当前用户角色
app.put('/api/user-roles/:id/set-current', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey } = req.query
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const roleId = parseInt(id)
    if (isNaN(roleId)) {
      return res.status(400).json({ error: 'Invalid role id' })
    }
    
    const role = setCurrentUserRole(roleId, apiKey)
    res.json({ success: true, data: role })
  } catch (error) {
    console.error('设置当前用户角色失败:', error)
    res.status(500).json({ error: error.message || '设置当前用户角色失败' })
  }
})

// ========== 背景管理 API ==========

// 获取背景列表
app.get('/api/backgrounds', async (req, res) => {
  try {
    const { apiKey } = req.query
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const backgrounds = getBackgrounds(apiKey)
    res.json({ success: true, data: backgrounds })
  } catch (error) {
    console.error('获取背景列表失败:', error)
    res.status(500).json({ error: error.message || '获取背景列表失败' })
  }
})

// 上传背景图像
app.post('/api/backgrounds', uploadBackground.single('file'), async (req, res) => {
  try {
    const { apiKey, name } = req.body
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    if (!req.file) {
      return res.status(400).json({ error: '请上传图片文件' })
    }
    
    const url = `/uploads/backgrounds/${req.file.filename}`
    const background = createBackground(apiKey, name || null, url)
    
    res.json({ success: true, data: background })
  } catch (error) {
    console.error('上传背景失败:', error)
    res.status(500).json({ error: error.message || '上传背景失败' })
  }
})

// 从URL创建背景（保存当前背景）
app.post('/api/backgrounds/from-url', async (req, res) => {
  try {
    const { apiKey, name, url } = req.body
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    if (!url) {
      return res.status(400).json({ error: 'url is required' })
    }
    
    const background = createBackground(apiKey, name || null, url)
    
    res.json({ success: true, data: background })
  } catch (error) {
    console.error('保存背景失败:', error)
    res.status(500).json({ error: error.message || '保存背景失败' })
  }
})

// 更新背景信息
app.put('/api/backgrounds/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey, name } = req.body
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const backgroundId = parseInt(id)
    if (isNaN(backgroundId)) {
      return res.status(400).json({ error: 'Invalid background id' })
    }
    
    const background = updateBackground(backgroundId, apiKey, name)
    res.json({ success: true, data: background })
  } catch (error) {
    console.error('更新背景失败:', error)
    res.status(500).json({ error: error.message || '更新背景失败' })
  }
})

// 删除背景
app.delete('/api/backgrounds/:id', async (req, res) => {
  try {
    const { id } = req.params
    const { apiKey } = req.query
    
    if (!apiKey) {
      return res.status(400).json({ error: 'apiKey is required' })
    }
    
    const backgroundId = parseInt(id)
    if (isNaN(backgroundId)) {
      return res.status(400).json({ error: 'Invalid background id' })
    }
    
    deleteBackground(backgroundId, apiKey)
    res.json({ success: true })
  } catch (error) {
    console.error('删除背景失败:', error)
    res.status(500).json({ error: error.message || '删除背景失败' })
  }
})

// 豆包TTS代理API（完全照抄SillyTavern的实现）
app.post('/api/doubao/generate-voice', async (req, res) => {
  try {
    const { apiKey, text, voice, speed, volume } = req.body

    if (!apiKey) {
      return res.status(400).json({ error: 'API Key is required' })
    }

    if (!text) {
      return res.status(400).json({ error: 'Text is required' })
    }

    // 豆包 TTS API 端点：https://openspeech.bytedance.com/api/v1/tts
    const apiUrl = 'https://openspeech.bytedance.com/api/v1/tts'

    // 生成唯一 reqid 和 uid
    const reqid = randomUUID()
    const uid = randomUUID()

    // 根据官方示例，cluster 需要根据 voice_type 判断
    // 如果 voice_type 以 "S_" 开头，使用 "volcano_icl"，否则使用 "volcano_tts"
    const voiceType = voice || 'BV700_streaming' // 默认使用灿灿
    const cluster = voiceType.startsWith('S_') ? 'volcano_icl' : 'volcano_tts'

    // 根据官方示例代码，请求格式需要包含 app, user, audio, request 四个部分
    // 根据官方示例：app.token 和 Authorization header 都使用 access_token
    // 如果 key 是格式 "appid:token"，则分别使用；否则 key 同时作为 appid 和 access_token
    let appid, accessToken
    if (apiKey.includes(':')) {
      [appid, accessToken] = apiKey.split(':', 2)
      appid = appid.trim()
      accessToken = accessToken.trim()
    } else {
      // 如果只提供一个值，同时用作 appid 和 access_token
      appid = apiKey
      accessToken = apiKey
    }

    console.debug('Doubao TTS API Key parsed', { appid, accessTokenLength: accessToken?.length })

    const requestBody = {
      app: {
        appid: appid,
        token: "access_token", // 根据官方示例代码，这里写的是字符串"access_token"（该字段不生效）
        cluster: cluster,
      },
      user: {
        uid: uid, // 使用 UUID 作为用户标识
      },
      audio: {
        voice_type: voiceType,
        encoding: 'mp3', // 支持 mp3, wav, pcm, ogg_opus
        speed_ratio: speed ?? 1.0,
        volume_ratio: volume ?? 1.0, // 根据官方示例，使用 volume_ratio
      },
      request: {
        reqid: reqid,
        text: text || '',
        operation: 'query', // query 表示非流式（HTTP 接口），submit 表示流式（WebSocket）
      },
    }

    console.debug('Doubao TTS request', requestBody)

    // 注意：Authorization header 格式是 "Bearer;{access_token}"，使用分号分隔
    // 根据官方示例，这里应该使用 access_token
    const result = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer;${accessToken}`,
      },
      body: JSON.stringify(requestBody),
    })

    if (!result.ok) {
      const errorText = await result.text()
      console.warn('Doubao TTS request failed', result.statusText, errorText)
      return res.status(500).send(errorText)
    }

    // 响应是 JSON 格式，包含 base64 编码的音频数据
    const responseData = await result.json()

    if (responseData.code !== 3000) {
      console.warn('Doubao TTS error', {
        code: responseData.code,
        message: responseData.message,
        reqid: responseData.reqid,
        appid: appid,
      })
      return res.status(500).json(responseData)
    }

    // 解码 base64 音频数据
    const audioBuffer = Buffer.from(responseData.data, 'base64')
    res.setHeader('Content-Type', 'audio/mpeg')
    return res.send(audioBuffer)
  } catch (error) {
    console.error('Doubao TTS generation failed', error)
    res.status(500).send('Internal server error')
  }
})

app.listen(PORT, () => {
  console.log(`后端服务运行在 http://localhost:${PORT}`)
})

