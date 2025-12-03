# 后端服务说明

## 启动后端服务

```bash
npm install
npm run server
```

后端服务运行在 `http://localhost:3001`

## API 接口

### 保存对话消息
POST `/api/chat/history`
```json
{
  "user": "default_user",
  "role": "user",
  "content": "消息内容",
  "timestamp": 1234567890
}
```

### 获取对话历史
GET `/api/chat/history?user=default_user&limit=100`

### 清空对话历史
DELETE `/api/chat/history?user=default_user`

## 数据库

使用 SQLite 存储，数据库文件位于 `data/chat_history.db`

表结构：
- `id`: 主键
- `user_id`: 用户ID（当前使用 default_user）
- `role`: 角色（user/assistant）
- `content`: 消息内容
- `timestamp`: 时间戳
- `created_at`: 创建时间

## 多租户支持

当前所有用户使用 `default_user`，后续可扩展账号体系。

