import Database from 'better-sqlite3'
import path from 'path'
import { fileURLToPath } from 'url'
import fs from 'fs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const DB_DIR = path.join(__dirname, '../data')
const DB_PATH = path.join(DB_DIR, 'chat_history.db')

// 确保数据目录存在
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true })
}

let db = null

export function initDatabase() {
  try {
    db = new Database(DB_PATH)
    
    // 创建聊天消息表（新方案）
    db.exec(`
      CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
        content TEXT NOT NULL,
        character_id TEXT,
        timestamp INTEGER NOT NULL,
        created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
        updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
      )
    `)
    
    // 创建索引
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_user_timestamp 
      ON chat_messages(user_id, timestamp DESC);
      
      CREATE INDEX IF NOT EXISTS idx_role 
      ON chat_messages(role);
      
      CREATE INDEX IF NOT EXISTS idx_timestamp 
      ON chat_messages(timestamp DESC)
    `)
    
    // 创建角色表
    db.exec(`
      CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT,
        user TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'illustration' CHECK(type IN ('digital_human', 'illustration')),
        description TEXT,
        avatar TEXT,
        position_x REAL DEFAULT 80,
        position_y REAL DEFAULT 50,
        scale REAL DEFAULT 1.0,
        base_url TEXT,
        model TEXT,
        api_key TEXT,
        avatar_app_id TEXT,
        avatar_app_secret TEXT,
        created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
        updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
      )
    `)
    
    // 为现有表添加 avatar_app_id 和 avatar_app_secret 字段（如果不存在）
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN avatar_app_id TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN avatar_app_secret TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加 TTS 字段（如果不存在）
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN tts_provider TEXT DEFAULT 'doubao'`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN tts_voice TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN tts_speed REAL DEFAULT 1.0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN tts_volume REAL DEFAULT 1.0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加语音播放控制字段（如果不存在）
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN enable_voice_play INTEGER DEFAULT 1`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN enable_auto_play INTEGER DEFAULT 0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN enable_auto_switch INTEGER DEFAULT 0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加数字人语音选项字段（如果不存在）
    try {
      db.exec(`ALTER TABLE roles ADD COLUMN use_digital_human_voice INTEGER DEFAULT 1`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 创建用户角色表
    db.exec(`
      CREATE TABLE IF NOT EXISTS user_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT NOT NULL,
        user TEXT NOT NULL,
        name TEXT,
        type TEXT NOT NULL DEFAULT 'illustration' CHECK(type IN ('digital_human', 'illustration')),
        avatar TEXT,
        position_x REAL DEFAULT 20,
        position_y REAL DEFAULT 50,
        scale REAL DEFAULT 1.0,
        base_url TEXT,
        model TEXT,
        avatar_app_id TEXT,
        avatar_app_secret TEXT,
        is_current INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
        updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
      )
    `)
    
    // 如果user字段不存在，添加该字段（用于数据库迁移）
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN user TEXT NOT NULL DEFAULT ''`)
    } catch (e) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加 TTS 字段（如果不存在）
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN tts_provider TEXT DEFAULT 'doubao'`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN tts_voice TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN tts_speed REAL DEFAULT 1.0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN tts_volume REAL DEFAULT 1.0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加语音播放控制字段（如果不存在）
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN enable_voice_play INTEGER DEFAULT 1`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN enable_auto_play INTEGER DEFAULT 0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN enable_auto_switch INTEGER DEFAULT 0`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加数字人语音选项字段（如果不存在）
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN use_digital_human_voice INTEGER DEFAULT 1`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN tts_preview_text TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加 type 字段（如果不存在）
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN type TEXT NOT NULL DEFAULT 'illustration' CHECK(type IN ('digital_human', 'illustration'))`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 为现有表添加 avatar_app_id 和 avatar_app_secret 字段（如果不存在）
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN avatar_app_id TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    try {
      db.exec(`ALTER TABLE user_roles ADD COLUMN avatar_app_secret TEXT`)
    } catch (error) {
      // 字段已存在，忽略错误
    }
    
    // 创建用户角色表索引
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_user_roles_api_key 
      ON user_roles(api_key);
      
      CREATE INDEX IF NOT EXISTS idx_user_roles_is_current 
      ON user_roles(api_key, is_current);
    `)
    
    // 创建角色表索引
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_roles_api_key 
      ON roles(api_key);
      
      CREATE INDEX IF NOT EXISTS idx_roles_user_id 
      ON roles(user_id)
    `)
    
    // 创建背景表
    db.exec(`
      CREATE TABLE IF NOT EXISTS backgrounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT NOT NULL,
        name TEXT,
        url TEXT NOT NULL,
        created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
        updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
      )
    `)
    
    // 创建背景表索引
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_backgrounds_api_key 
      ON backgrounds(api_key);
      
      CREATE INDEX IF NOT EXISTS idx_backgrounds_created_at 
      ON backgrounds(api_key, created_at DESC)
    `)
    
    console.log('数据库初始化成功')
  } catch (error) {
    console.error('数据库初始化失败:', error)
    throw error
  }
}

export function saveMessage(userId, role, content, timestamp = null, characterId = null) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const insertTime = timestamp || Date.now()
  const now = Math.floor(Date.now() / 1000) // Unix时间戳（秒）
  
  const stmt = db.prepare(`
    INSERT INTO chat_messages (user_id, role, content, character_id, timestamp, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `)
  
  const result = stmt.run(userId, role, content, characterId, insertTime, now, now)
  
  return {
    id: result.lastInsertRowid,
    userId,
    role,
    content,
    characterId,
    timestamp: insertTime,
    createdAt: now * 1000,
    updatedAt: now * 1000
  }
}

export function saveMessagesBatch(messages) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    INSERT INTO chat_messages (user_id, role, content, character_id, timestamp, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `)
  
  const insertMany = db.transaction((messages) => {
    const ids = []
    for (const msg of messages) {
      const insertTime = msg.timestamp || Date.now()
      const result = stmt.run(
        msg.userId,
        msg.role,
        msg.content,
        msg.characterId || null,
        insertTime,
        now,
        now
      )
      ids.push(result.lastInsertRowid)
    }
    return ids
  })
  
  return insertMany(messages)
}

export function getHistory(userId, options = {}) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const {
    limit = 50,
    offset = 0,
    before = null,
    after = null,
    role = null
  } = options
  
  let query = `
    SELECT id, user_id, role, content, character_id, timestamp, created_at, updated_at
    FROM chat_messages
    WHERE user_id = ?
  `
  const params = [userId]
  
  if (role) {
    query += ' AND role = ?'
    params.push(role)
  }
  
  if (before) {
    query += ' AND timestamp < ?'
    params.push(before)
  }
  
  if (after) {
    query += ' AND timestamp > ?'
    params.push(after)
  }
  
  query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
  params.push(limit, offset)
  
  const stmt = db.prepare(query)
  const rows = stmt.all(...params)
  
  // 获取总数
  let countQuery = 'SELECT COUNT(*) as total FROM chat_messages WHERE user_id = ?'
  const countParams = [userId]
  
  if (role) {
    countQuery += ' AND role = ?'
    countParams.push(role)
  }
  if (before) {
    countQuery += ' AND timestamp < ?'
    countParams.push(before)
  }
  if (after) {
    countQuery += ' AND timestamp > ?'
    countParams.push(after)
  }
  
  const countStmt = db.prepare(countQuery)
  const countResult = countStmt.get(...countParams)
  const total = countResult.total
  
  // 反转顺序，让最新的在最后
  return {
    messages: rows.reverse().map(row => ({
      id: row.id,
      role: row.role,
      content: row.content,
      characterId: row.character_id,
      timestamp: row.timestamp,
      createdAt: row.created_at * 1000,
      updatedAt: row.updated_at * 1000
    })),
    total,
    limit,
    offset
  }
}

export function updateMessage(id, content, characterId = null) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    UPDATE chat_messages
    SET content = ?, character_id = ?, updated_at = ?
    WHERE id = ?
  `)
  
  const result = stmt.run(content, characterId, now, id)
  
  if (result.changes === 0) {
    throw new Error('消息不存在')
  }
  
  return getMessageById(id)
}

export function getMessageById(id) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const stmt = db.prepare(`
    SELECT id, user_id, role, content, character_id, timestamp, created_at, updated_at
    FROM chat_messages
    WHERE id = ?
  `)
  
  const row = stmt.get(id)
  if (!row) {
    return null
  }
  
  return {
    id: row.id,
    userId: row.user_id,
    role: row.role,
    content: row.content,
    characterId: row.character_id,
    timestamp: row.timestamp,
    createdAt: row.created_at * 1000,
    updatedAt: row.updated_at * 1000
  }
}

export function deleteMessage(id, userId) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  // 如果提供了userId，验证消息是否属于该用户
  if (userId) {
    const checkStmt = db.prepare(`
      SELECT id FROM chat_messages
      WHERE id = ? AND user_id = ?
    `)
    const message = checkStmt.get(id, userId)
    
    if (!message) {
      throw new Error('消息不存在或不属于当前用户')
    }
  }
  
  const stmt = db.prepare(`
    DELETE FROM chat_messages
    WHERE id = ?
  `)
  
  const result = stmt.run(id)
  
  if (result.changes === 0) {
    throw new Error('消息不存在')
  }
  
  return true
}

export function clearHistory(userId) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const stmt = db.prepare(`
    DELETE FROM chat_messages
    WHERE user_id = ?
  `)
  
  const result = stmt.run(userId)
  return result.changes
}

export function syncMessages(userId, messages) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO chat_messages (user_id, role, content, character_id, timestamp, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `)
  
  let synced = 0
  let skipped = 0
  
  const syncMany = db.transaction((messages) => {
    for (const msg of messages) {
      try {
        const insertTime = msg.timestamp || Date.now()
        const result = stmt.run(
          userId,
          msg.role,
          msg.content,
          msg.characterId || null,
          insertTime,
          now,
          now
        )
        if (result.changes > 0) {
          synced++
        } else {
          skipped++
        }
      } catch (error) {
        skipped++
      }
    }
    return { synced, skipped }
  })
  
  return syncMany(messages)
}

// ==================== 角色管理相关函数 ====================

// 获取用户的所有角色
// 如果userId不包含冒号，则查询所有以该userId开头的角色（支持apiKey前缀查询）
// 如果userId包含冒号，则精确匹配
export function getRoles(apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  if (!apiKey || !apiKey.trim()) {
    throw new Error('apiKey不能为空')
  }
  
  // 按 api_key 过滤，确保用户隔离
  const stmt = db.prepare(`
    SELECT id, user_id, name, user, type, description, avatar, position_x, position_y, scale, base_url, model, api_key, avatar_app_id, avatar_app_secret, use_digital_human_voice, tts_provider, tts_voice, tts_speed, tts_volume, enable_voice_play, enable_auto_play, enable_auto_switch, created_at, updated_at
    FROM roles
    WHERE api_key = ?
    ORDER BY created_at DESC
  `)
  const roles = stmt.all(apiKey)
  return roles.map(role => ({
    id: role.id,
    name: role.name || null,
    user: role.user,
    type: role.type || 'illustration',
    description: role.description || null,
    avatar: role.avatar || null,
    positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
    positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
    scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
    baseURL: role.base_url || null,
    model: role.model || null,
    apiKey: role.api_key || null,
    avatarAppId: role.avatar_app_id || null,
    avatarAppSecret: role.avatar_app_secret || null,
    useDigitalHumanVoice: role.use_digital_human_voice !== null && role.use_digital_human_voice !== undefined ? (role.use_digital_human_voice === 1) : undefined,
    ttsProvider: role.tts_provider || null,
    ttsVoice: role.tts_voice || null,
    ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
    ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
    enableVoicePlay: role.enable_voice_play !== null && role.enable_voice_play !== undefined ? (role.enable_voice_play === 1) : undefined,
    enableAutoPlay: role.enable_auto_play !== null && role.enable_auto_play !== undefined ? (role.enable_auto_play === 1) : undefined,
    enableAutoSwitch: role.enable_auto_switch !== null && role.enable_auto_switch !== undefined ? (role.enable_auto_switch === 1) : undefined,
    createdAt: role.created_at,
    updatedAt: role.updated_at
  }))
}

// 创建角色
export function createRole(apiKey, name, user, type = 'illustration', description = null, avatar = null, positionX = null, positionY = null, scale = null, baseURL = null, model = null, avatarAppId = null, avatarAppSecret = null) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  if (!apiKey || !apiKey.trim()) {
    throw new Error('apiKey不能为空')
  }
  
  if (!user || !user.trim()) {
    throw new Error('user字段不能为空')
  }
  
  if (!type || !['digital_human', 'illustration'].includes(type)) {
    throw new Error('角色类型无效')
  }
  
  // user_id 格式：apiKey:user（用于兼容历史数据，但查询时使用 api_key）
  const userId = `${apiKey}:${user}`
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    INSERT INTO roles (api_key, user_id, name, user, type, description, avatar, position_x, position_y, scale, base_url, model, avatar_app_id, avatar_app_secret, tts_provider, tts_voice, tts_speed, tts_volume, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `)
  
  const result = stmt.run(
    apiKey.trim(),
    userId,
    name ? name.trim() : null, 
    user.trim(), 
    type,
    description || null, 
    avatar || null,
    positionX !== null && positionX !== undefined ? positionX : null,
    positionY !== null && positionY !== undefined ? positionY : null,
    scale !== null && scale !== undefined ? scale : null,
    baseURL || null,
    model || null,
    avatarAppId || null,
    avatarAppSecret || null,
    'doubao', // tts_provider 默认值
    null, // tts_voice
    1.0, // tts_speed 默认值
    1.0, // tts_volume 默认值
    now, 
    now
  )
  
  return {
    id: result.lastInsertRowid,
    name: name ? name.trim() : null,
    user: user.trim(),
    type: type,
    description: description || null,
    avatar: avatar || null,
    positionX: positionX !== null && positionX !== undefined ? positionX : undefined,
    positionY: positionY !== null && positionY !== undefined ? positionY : undefined,
    scale: scale !== null && scale !== undefined ? scale : undefined,
    baseURL: baseURL || null,
    model: model || null,
    apiKey: apiKey || null,
    avatarAppId: avatarAppId || null,
    avatarAppSecret: avatarAppSecret || null,
    useDigitalHumanVoice: true,
    ttsProvider: 'doubao',
    ttsVoice: null,
    ttsSpeed: 1.0,
    ttsVolume: 1.0,
    enableVoicePlay: true,
    enableAutoPlay: false,
    enableAutoSwitch: false,
    createdAt: now,
    updatedAt: now
  }
}

// 更新角色
export function updateRole(id, apiKey, updates) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  if (!apiKey || !apiKey.trim()) {
    throw new Error('apiKey不能为空')
  }
  
  // 先检查角色是否存在且属于该用户（按 api_key 过滤）
  const checkStmt = db.prepare('SELECT id, api_key, user_id FROM roles WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  
  if (!existing) {
    throw new Error('角色不存在或无权限')
  }
  
  // 如果更新了 user 字段，需要更新 user_id
  if (updates.user !== undefined && updates.user && updates.user.trim()) {
    updates.user_id = `${apiKey}:${updates.user.trim()}`
  }
  
  // 构建更新字段
  const fields = []
  const values = []
  
  if (updates.name !== undefined) {
    fields.push('name = ?')
    values.push(updates.name ? updates.name.trim() : null)
  }
  
  if (updates.user !== undefined) {
    if (!updates.user || !updates.user.trim()) {
      throw new Error('user字段不能为空')
    }
    fields.push('user = ?')
    values.push(updates.user.trim())
  }
  
  if (updates.type !== undefined) {
    if (!['digital_human', 'illustration'].includes(updates.type)) {
      throw new Error('角色类型无效')
    }
    fields.push('type = ?')
    values.push(updates.type)
  }
  
  if (updates.description !== undefined) {
    fields.push('description = ?')
    values.push(updates.description || null)
  }
  
  if (updates.avatar !== undefined) {
    fields.push('avatar = ?')
    values.push(updates.avatar || null)
  }
  
  if (updates.positionX !== undefined) {
    fields.push('position_x = ?')
    values.push(updates.positionX !== null && updates.positionX !== undefined ? updates.positionX : null)
  }
  
  if (updates.positionY !== undefined) {
    fields.push('position_y = ?')
    values.push(updates.positionY !== null && updates.positionY !== undefined ? updates.positionY : null)
  }
  
  if (updates.scale !== undefined) {
    fields.push('scale = ?')
    values.push(updates.scale !== null && updates.scale !== undefined ? updates.scale : null)
  }
  
  if (updates.baseURL !== undefined) {
    fields.push('base_url = ?')
    values.push(updates.baseURL || null)
  }
  
  if (updates.model !== undefined) {
    fields.push('model = ?')
    values.push(updates.model || null)
  }
  
  if (updates.avatarAppId !== undefined) {
    fields.push('avatar_app_id = ?')
    values.push(updates.avatarAppId || null)
  }
  
  if (updates.avatarAppSecret !== undefined) {
    fields.push('avatar_app_secret = ?')
    values.push(updates.avatarAppSecret || null)
  }
  
  if (updates.ttsProvider !== undefined) {
    fields.push('tts_provider = ?')
    values.push(updates.ttsProvider || 'doubao')
  }
  
  if (updates.ttsVoice !== undefined) {
    fields.push('tts_voice = ?')
    values.push(updates.ttsVoice || null)
  }
  
  if (updates.ttsSpeed !== undefined) {
    fields.push('tts_speed = ?')
    values.push(updates.ttsSpeed !== null && updates.ttsSpeed !== undefined ? updates.ttsSpeed : 1.0)
  }
  
  if (updates.ttsVolume !== undefined) {
    fields.push('tts_volume = ?')
    values.push(updates.ttsVolume !== null && updates.ttsVolume !== undefined ? updates.ttsVolume : 1.0)
  }
  
  if (updates.enableVoicePlay !== undefined) {
    fields.push('enable_voice_play = ?')
    values.push(updates.enableVoicePlay ? 1 : 0)
  }
  
  if (updates.enableAutoPlay !== undefined) {
    fields.push('enable_auto_play = ?')
    values.push(updates.enableAutoPlay ? 1 : 0)
  }
  
  if (updates.enableAutoSwitch !== undefined) {
    fields.push('enable_auto_switch = ?')
    values.push(updates.enableAutoSwitch ? 1 : 0)
  }
  
  if (updates.useDigitalHumanVoice !== undefined) {
    fields.push('use_digital_human_voice = ?')
    values.push(updates.useDigitalHumanVoice ? 1 : 0)
  }
  
  if (updates.user_id !== undefined) {
    fields.push('user_id = ?')
    values.push(updates.user_id)
  }
  
  if (fields.length === 0) {
    // 没有要更新的字段，直接返回现有角色（按 api_key 查询）
    const getStmt = db.prepare('SELECT * FROM roles WHERE id = ? AND api_key = ?')
    const role = getStmt.get(id, apiKey)
  return {
    id: role.id,
    name: role.name || null,
    user: role.user,
    type: role.type || 'illustration',
    description: role.description || null,
    avatar: role.avatar || null,
    positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
    positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
    scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
    baseURL: role.base_url || null,
    model: role.model || null,
    apiKey: role.api_key || null,
    avatarAppId: role.avatar_app_id || null,
    avatarAppSecret: role.avatar_app_secret || null,
    useDigitalHumanVoice: role.use_digital_human_voice !== null && role.use_digital_human_voice !== undefined ? (role.use_digital_human_voice === 1) : undefined,
    ttsProvider: role.tts_provider || null,
    ttsVoice: role.tts_voice || null,
    ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
    ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
    enableVoicePlay: role.enable_voice_play !== null && role.enable_voice_play !== undefined ? (role.enable_voice_play === 1) : undefined,
    enableAutoPlay: role.enable_auto_play !== null && role.enable_auto_play !== undefined ? (role.enable_auto_play === 1) : undefined,
    enableAutoSwitch: role.enable_auto_switch !== null && role.enable_auto_switch !== undefined ? (role.enable_auto_switch === 1) : undefined,
    createdAt: role.created_at,
    updatedAt: role.updated_at
  }
  }
  
  // 添加更新时间
  fields.push('updated_at = ?')
  values.push(Math.floor(Date.now() / 1000))
  
  // 按 api_key 过滤更新
  values.push(id, apiKey)
  
  const updateStmt = db.prepare(`
    UPDATE roles 
    SET ${fields.join(', ')}
    WHERE id = ? AND api_key = ?
  `)
  
  updateStmt.run(...values)
  
  // 返回更新后的角色（按 api_key 查询）
  const getStmt = db.prepare('SELECT * FROM roles WHERE id = ? AND api_key = ?')
  const role = getStmt.get(id, apiKey)
  if (!role) {
    throw new Error('角色不存在或无权限')
  }
  return {
    id: role.id,
    name: role.name,
    user: role.user,
    type: role.type || 'illustration',
    description: role.description || null,
    avatar: role.avatar || null,
    positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
    positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
    scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
    baseURL: role.base_url || null,
    model: role.model || null,
    apiKey: role.api_key || null,
    avatarAppId: role.avatar_app_id || null,
    avatarAppSecret: role.avatar_app_secret || null,
    useDigitalHumanVoice: role.use_digital_human_voice !== null && role.use_digital_human_voice !== undefined ? (role.use_digital_human_voice === 1) : undefined,
    ttsProvider: role.tts_provider || null,
    ttsVoice: role.tts_voice || null,
    ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
    ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
    enableVoicePlay: role.enable_voice_play !== null && role.enable_voice_play !== undefined ? (role.enable_voice_play === 1) : undefined,
    enableAutoPlay: role.enable_auto_play !== null && role.enable_auto_play !== undefined ? (role.enable_auto_play === 1) : undefined,
    enableAutoSwitch: role.enable_auto_switch !== null && role.enable_auto_switch !== undefined ? (role.enable_auto_switch === 1) : undefined,
    createdAt: role.created_at,
    updatedAt: role.updated_at
  }
}

// ========== 用户角色管理函数 ==========

// 获取用户角色列表
export function getUserRoles(apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  if (!apiKey || !apiKey.trim()) {
    throw new Error('apiKey不能为空')
  }
  
  const stmt = db.prepare(`
    SELECT id, api_key, user, name, type, avatar, position_x, position_y, scale, base_url, model, avatar_app_id, avatar_app_secret, use_digital_human_voice, tts_provider, tts_voice, tts_speed, tts_volume, tts_preview_text, enable_voice_play, enable_auto_play, enable_auto_switch, is_current, created_at, updated_at
    FROM user_roles
    WHERE api_key = ?
    ORDER BY created_at DESC
  `)
  
  const roles = stmt.all(apiKey)
  return roles.map(role => ({
    id: role.id,
    apiKey: role.api_key,
    user: role.user || '',
    name: role.name || null,
    type: role.type || 'illustration',
    avatar: role.avatar || null,
    positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
    positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
    scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
    baseURL: role.base_url || null,
    model: role.model || null,
    avatarAppId: role.avatar_app_id || null,
    avatarAppSecret: role.avatar_app_secret || null,
    useDigitalHumanVoice: role.use_digital_human_voice !== null && role.use_digital_human_voice !== undefined ? (role.use_digital_human_voice === 1) : undefined,
    ttsProvider: role.tts_provider || null,
    ttsVoice: role.tts_voice || null,
    ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
    ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
    ttsPreviewText: role.tts_preview_text || null,
    enableVoicePlay: role.enable_voice_play !== null && role.enable_voice_play !== undefined ? (role.enable_voice_play === 1) : undefined,
    enableAutoPlay: role.enable_auto_play !== null && role.enable_auto_play !== undefined ? (role.enable_auto_play === 1) : undefined,
    enableAutoSwitch: role.enable_auto_switch !== null && role.enable_auto_switch !== undefined ? (role.enable_auto_switch === 1) : undefined,
    isCurrent: role.is_current === 1,
    createdAt: role.created_at,
    updatedAt: role.updated_at
  }))
}

// 创建用户角色
export function createUserRole(apiKey, user, name = null, type = 'illustration', avatar = null, positionX = null, positionY = null, scale = null, baseURL = null, model = null, avatarAppId = null, avatarAppSecret = null) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  if (!apiKey || !apiKey.trim()) {
    throw new Error('apiKey不能为空')
  }
  
  if (!user || !user.trim()) {
    throw new Error('user字段不能为空')
  }
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    INSERT INTO user_roles (api_key, user, name, type, avatar, position_x, position_y, scale, base_url, model, avatar_app_id, avatar_app_secret, tts_provider, tts_voice, tts_speed, tts_volume, tts_preview_text, is_current, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
  `)
  
  const result = stmt.run(
    apiKey.trim(),
    user.trim(),
    name ? name.trim() : null,
    type || 'illustration',
    avatar || null,
    positionX !== null && positionX !== undefined ? positionX : null,
    positionY !== null && positionY !== undefined ? positionY : null,
    scale !== null && scale !== undefined ? scale : null,
    baseURL || null,
    model || null,
    avatarAppId || null,
    avatarAppSecret || null,
    'doubao', // tts_provider 默认值
    null, // tts_voice
    1.0, // tts_speed 默认值
    1.0, // tts_volume 默认值
    null, // tts_preview_text
    now,
    now
  )
  
  return {
    id: result.lastInsertRowid,
    apiKey: apiKey.trim(),
    user: user.trim(),
    name: name ? name.trim() : null,
    type: type || 'illustration',
    avatar: avatar || null,
    positionX: positionX !== null && positionX !== undefined ? positionX : undefined,
    positionY: positionY !== null && positionY !== undefined ? positionY : undefined,
    scale: scale !== null && scale !== undefined ? scale : undefined,
    baseURL: baseURL || null,
    model: model || null,
    avatarAppId: avatarAppId || null,
    avatarAppSecret: avatarAppSecret || null,
    ttsProvider: 'doubao',
    ttsVoice: null,
    ttsSpeed: 1.0,
    ttsVolume: 1.0,
    ttsPreviewText: null,
    isCurrent: false,
    createdAt: now,
    updatedAt: now
  }
}

// 更新用户角色
export function updateUserRole(id, apiKey, updates) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  // 先检查角色是否存在且属于该apiKey
  const checkStmt = db.prepare('SELECT id, api_key FROM user_roles WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  if (!existing) {
    throw new Error('用户角色不存在或无权限')
  }
  
  const fields = []
  const values = []
  
  if (updates.user !== undefined) {
    if (!updates.user || !updates.user.trim()) {
      throw new Error('user字段不能为空')
    }
    fields.push('user = ?')
    values.push(updates.user.trim())
  }
  
  if (updates.name !== undefined) {
    fields.push('name = ?')
    values.push(updates.name || null)
  }
  
  if (updates.type !== undefined) {
    fields.push('type = ?')
    values.push(updates.type || 'illustration')
  }
  
  if (updates.avatar !== undefined) {
    fields.push('avatar = ?')
    values.push(updates.avatar || null)
  }
  
  if (updates.positionX !== undefined) {
    fields.push('position_x = ?')
    values.push(updates.positionX !== null && updates.positionX !== undefined ? updates.positionX : null)
  }
  
  if (updates.positionY !== undefined) {
    fields.push('position_y = ?')
    values.push(updates.positionY !== null && updates.positionY !== undefined ? updates.positionY : null)
  }
  
  if (updates.scale !== undefined) {
    fields.push('scale = ?')
    values.push(updates.scale !== null && updates.scale !== undefined ? updates.scale : null)
  }
  
  if (updates.baseURL !== undefined) {
    fields.push('base_url = ?')
    values.push(updates.baseURL || null)
  }
  
  if (updates.model !== undefined) {
    fields.push('model = ?')
    values.push(updates.model || null)
  }
  
  if (updates.avatarAppId !== undefined) {
    fields.push('avatar_app_id = ?')
    values.push(updates.avatarAppId || null)
  }
  
  if (updates.avatarAppSecret !== undefined) {
    fields.push('avatar_app_secret = ?')
    values.push(updates.avatarAppSecret || null)
  }
  
  if (updates.ttsProvider !== undefined) {
    fields.push('tts_provider = ?')
    values.push(updates.ttsProvider || 'doubao')
  }
  
  if (updates.ttsVoice !== undefined) {
    fields.push('tts_voice = ?')
    values.push(updates.ttsVoice || null)
  }
  
  if (updates.ttsSpeed !== undefined) {
    fields.push('tts_speed = ?')
    values.push(updates.ttsSpeed !== null && updates.ttsSpeed !== undefined ? updates.ttsSpeed : 1.0)
  }
  
  if (updates.ttsVolume !== undefined) {
    fields.push('tts_volume = ?')
    values.push(updates.ttsVolume !== null && updates.ttsVolume !== undefined ? updates.ttsVolume : 1.0)
  }
  
  if (updates.ttsPreviewText !== undefined) {
    fields.push('tts_preview_text = ?')
    values.push(updates.ttsPreviewText || null)
  }
  
  if (updates.enableVoicePlay !== undefined) {
    fields.push('enable_voice_play = ?')
    values.push(updates.enableVoicePlay ? 1 : 0)
  }
  
  if (updates.enableAutoPlay !== undefined) {
    fields.push('enable_auto_play = ?')
    values.push(updates.enableAutoPlay ? 1 : 0)
  }
  
  if (updates.enableAutoSwitch !== undefined) {
    fields.push('enable_auto_switch = ?')
    values.push(updates.enableAutoSwitch ? 1 : 0)
  }
  
  if (updates.useDigitalHumanVoice !== undefined) {
    fields.push('use_digital_human_voice = ?')
    values.push(updates.useDigitalHumanVoice ? 1 : 0)
  }
  
  if (fields.length === 0) {
    // 没有要更新的字段，直接返回现有角色
    const getStmt = db.prepare('SELECT * FROM user_roles WHERE id = ? AND api_key = ?')
    const role = getStmt.get(id, apiKey)
    return {
      id: role.id,
      apiKey: role.api_key,
      user: role.user || '',
      name: role.name || null,
      type: role.type || 'illustration',
      avatar: role.avatar || null,
      positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
      positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
      scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
      baseURL: role.base_url || null,
      model: role.model || null,
      avatarAppId: role.avatar_app_id || null,
      avatarAppSecret: role.avatar_app_secret || null,
      useDigitalHumanVoice: role.use_digital_human_voice !== null && role.use_digital_human_voice !== undefined ? (role.use_digital_human_voice === 1) : undefined,
      ttsProvider: role.tts_provider || null,
      ttsVoice: role.tts_voice || null,
      ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
      ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
      ttsPreviewText: role.tts_preview_text || null,
      enableVoicePlay: role.enable_voice_play !== null && role.enable_voice_play !== undefined ? (role.enable_voice_play === 1) : undefined,
      enableAutoPlay: role.enable_auto_play !== null && role.enable_auto_play !== undefined ? (role.enable_auto_play === 1) : undefined,
      enableAutoSwitch: role.enable_auto_switch !== null && role.enable_auto_switch !== undefined ? (role.enable_auto_switch === 1) : undefined,
      isCurrent: role.is_current === 1,
      createdAt: role.created_at,
      updatedAt: role.updated_at
    }
  }
  
  // 添加更新时间
  fields.push('updated_at = ?')
  values.push(Math.floor(Date.now() / 1000))
  
  values.push(id, apiKey)
  
  const updateStmt = db.prepare(`
    UPDATE user_roles 
    SET ${fields.join(', ')}
    WHERE id = ? AND api_key = ?
  `)
  
  updateStmt.run(...values)
  
  // 返回更新后的角色
  const getStmt = db.prepare('SELECT * FROM user_roles WHERE id = ? AND api_key = ?')
  const role = getStmt.get(id, apiKey)
  if (!role) {
    throw new Error('用户角色不存在或无权限')
  }
  return {
    id: role.id,
    apiKey: role.api_key,
    user: role.user || '',
    name: role.name || null,
    type: role.type || 'illustration',
    avatar: role.avatar || null,
    positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
    positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
    scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
    baseURL: role.base_url || null,
    model: role.model || null,
      avatarAppId: role.avatar_app_id || null,
      avatarAppSecret: role.avatar_app_secret || null,
      useDigitalHumanVoice: role.use_digital_human_voice !== null && role.use_digital_human_voice !== undefined ? (role.use_digital_human_voice === 1) : undefined,
      ttsProvider: role.tts_provider || null,
      ttsVoice: role.tts_voice || null,
      ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
      ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
      ttsPreviewText: role.tts_preview_text || null,
      enableVoicePlay: role.enable_voice_play !== null && role.enable_voice_play !== undefined ? (role.enable_voice_play === 1) : undefined,
      enableAutoPlay: role.enable_auto_play !== null && role.enable_auto_play !== undefined ? (role.enable_auto_play === 1) : undefined,
      enableAutoSwitch: role.enable_auto_switch !== null && role.enable_auto_switch !== undefined ? (role.enable_auto_switch === 1) : undefined,
      isCurrent: role.is_current === 1,
      createdAt: role.created_at,
      updatedAt: role.updated_at
    }
  }

// 删除用户角色
export function deleteUserRole(id, apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  // 检查角色是否存在且属于该apiKey
  const checkStmt = db.prepare('SELECT id FROM user_roles WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  if (!existing) {
    throw new Error('用户角色不存在或无权限')
  }
  
  const stmt = db.prepare('DELETE FROM user_roles WHERE id = ? AND api_key = ?')
  stmt.run(id, apiKey)
}

// 设置当前用户角色
export function setCurrentUserRole(id, apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  // 检查角色是否存在且属于该apiKey
  const checkStmt = db.prepare('SELECT id FROM user_roles WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  if (!existing) {
    throw new Error('用户角色不存在或无权限')
  }
  
  // 先将该apiKey下的所有角色设为非当前
  const clearStmt = db.prepare('UPDATE user_roles SET is_current = 0, updated_at = ? WHERE api_key = ?')
  clearStmt.run(Math.floor(Date.now() / 1000), apiKey)
  
  // 设置指定角色为当前
  const setStmt = db.prepare('UPDATE user_roles SET is_current = 1, updated_at = ? WHERE id = ? AND api_key = ?')
  setStmt.run(Math.floor(Date.now() / 1000), id, apiKey)
  
  // 返回更新后的角色
  const getStmt = db.prepare('SELECT * FROM user_roles WHERE id = ? AND api_key = ?')
  const role = getStmt.get(id, apiKey)
  return {
    id: role.id,
    apiKey: role.api_key,
    user: role.user || '',
    name: role.name || null,
    type: role.type || 'illustration',
    avatar: role.avatar || null,
    positionX: role.position_x !== null && role.position_x !== undefined ? role.position_x : undefined,
    positionY: role.position_y !== null && role.position_y !== undefined ? role.position_y : undefined,
    scale: role.scale !== null && role.scale !== undefined ? role.scale : undefined,
    baseURL: role.base_url || null,
    model: role.model || null,
    avatarAppId: role.avatar_app_id || null,
    avatarAppSecret: role.avatar_app_secret || null,
    ttsProvider: role.tts_provider || null,
    ttsVoice: role.tts_voice || null,
    ttsSpeed: role.tts_speed !== null && role.tts_speed !== undefined ? role.tts_speed : undefined,
    ttsVolume: role.tts_volume !== null && role.tts_volume !== undefined ? role.tts_volume : undefined,
    ttsPreviewText: role.tts_preview_text || null,
    isCurrent: true,
    createdAt: role.created_at,
    updatedAt: role.updated_at
  }
}

// 删除角色
export function deleteRole(id, apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  if (!apiKey || !apiKey.trim()) {
    throw new Error('apiKey不能为空')
  }
  
  // 先检查角色是否存在且属于该用户（按 api_key 过滤），并获取user字段
  const checkStmt = db.prepare('SELECT id, user FROM roles WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  
  if (!existing) {
    throw new Error('角色不存在或无权限')
  }
  
  // 删除与该角色关联的聊天记录（user_id格式：apiKey:user）
  const userId = `${apiKey}:${existing.user}`
  const deleteMessagesStmt = db.prepare('DELETE FROM chat_messages WHERE user_id = ?')
  const messagesResult = deleteMessagesStmt.run(userId)
  console.log(`删除角色 ${id} 时，同时删除了 ${messagesResult.changes} 条关联的聊天记录`)
  
  // 删除角色
  const stmt = db.prepare('DELETE FROM roles WHERE id = ? AND api_key = ?')
  const result = stmt.run(id, apiKey)
  
  return result.changes > 0
}

// ========== 背景管理相关函数 ==========

// 获取背景列表
export function getBackgrounds(apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const stmt = db.prepare('SELECT * FROM backgrounds WHERE api_key = ? ORDER BY created_at DESC')
  const rows = stmt.all(apiKey)
  
  return rows.map(row => ({
    id: row.id,
    apiKey: row.api_key,
    name: row.name || null,
    url: row.url,
    createdAt: row.created_at,
    updatedAt: row.updated_at
  }))
}

// 创建背景
export function createBackground(apiKey, name, url) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    INSERT INTO backgrounds (api_key, name, url, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
  `)
  
  const result = stmt.run(apiKey, name || null, url, now, now)
  
  const getStmt = db.prepare('SELECT * FROM backgrounds WHERE id = ?')
  const row = getStmt.get(result.lastInsertRowid)
  
  return {
    id: row.id,
    apiKey: row.api_key,
    name: row.name || null,
    url: row.url,
    createdAt: row.created_at,
    updatedAt: row.updated_at
  }
}

// 更新背景
export function updateBackground(id, apiKey, name) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  // 检查背景是否存在且属于该apiKey
  const checkStmt = db.prepare('SELECT id FROM backgrounds WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  if (!existing) {
    throw new Error('背景不存在或无权限')
  }
  
  const now = Math.floor(Date.now() / 1000)
  const stmt = db.prepare(`
    UPDATE backgrounds 
    SET name = ?, updated_at = ? 
    WHERE id = ? AND api_key = ?
  `)
  
  stmt.run(name || null, now, id, apiKey)
  
  const getStmt = db.prepare('SELECT * FROM backgrounds WHERE id = ?')
  const row = getStmt.get(id)
  
  return {
    id: row.id,
    apiKey: row.api_key,
    name: row.name || null,
    url: row.url,
    createdAt: row.created_at,
    updatedAt: row.updated_at
  }
}

// 删除背景
export function deleteBackground(id, apiKey) {
  if (!db) {
    throw new Error('数据库未初始化')
  }
  
  // 检查背景是否存在且属于该apiKey
  const checkStmt = db.prepare('SELECT id, url FROM backgrounds WHERE id = ? AND api_key = ?')
  const existing = checkStmt.get(id, apiKey)
  if (!existing) {
    throw new Error('背景不存在或无权限')
  }
  
  const stmt = db.prepare('DELETE FROM backgrounds WHERE id = ? AND api_key = ?')
  const result = stmt.run(id, apiKey)
  
  // 如果删除成功，尝试删除文件（如果文件在uploads目录下）
  if (result.changes > 0 && existing.url) {
    try {
      const urlPath = existing.url
      // 如果是相对路径，尝试删除文件
      if (urlPath.startsWith('/uploads/backgrounds/')) {
        const filePath = path.join(__dirname, '..', urlPath)
        if (fs.existsSync(filePath)) {
          fs.unlinkSync(filePath)
        }
      }
    } catch (error) {
      console.error('删除背景文件失败:', error)
      // 不抛出错误，因为数据库记录已删除
    }
  }
  
  return result.changes > 0
}

