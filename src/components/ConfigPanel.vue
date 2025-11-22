<template>
  <div class="config-panel">
    <!-- Tab 导航 -->
    <div class="tab-header">
      <button 
        class="tab-button"
        :class="{ active: activeTab === 'chat' }"
        @click="activeTab = 'chat'"
      >
        对话
      </button>
      <button 
        class="tab-button"
        :class="{ active: activeTab === 'config' }"
        @click="activeTab = 'config'"
      >
        配置
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <!-- 对话页面 -->
      <div v-show="activeTab === 'chat'" class="chat-tab">
        <!-- 对话历史记录 -->
        <div class="chat-history" ref="chatHistoryRef">
          <div v-if="appState.chatHistory.length > 0" class="chat-history-header">
            <button 
              @click="handleClearHistory" 
              class="btn-clear-history"
              title="清空对话历史"
            >
              🗑️ 清空历史
            </button>
          </div>
          
          <template v-if="appState.chatHistory.length === 0">
            <div class="empty-history">
              暂无对话记录，开始对话吧~
            </div>
          </template>
          <template v-else>
            <div 
              v-for="(message, index) in appState.chatHistory" 
              :key="`msg-${index}-${message.timestamp || Date.now()}`"
              class="message-item"
              :class="message.role"
            >
              <div class="message-role">
                {{ message.role === 'user' ? '我' : 'AI' }}
              </div>
              <div class="message-content">{{ message.content || '(空消息)' }}</div>
              <div class="message-time" v-if="message.timestamp">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </template>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input-area">
          <div class="form-group">
            <textarea 
              v-model="appState.ui.text" 
              rows="3" 
              placeholder="请输入您的消息..."
              @keydown.enter.exact.prevent="handleSendMessage"
              @keydown.enter.shift.exact="handleShiftEnter"
            />
          </div>
          
          <div class="button-group">
            <button 
              @click="handleVoiceInput" 
              :disabled="!appState.avatar.connected || appState.asr.isListening"
              class="btn btn-voice"
            >
              {{ appState.asr.isListening ? '正在听...' : '语音输入' }}
            </button>
            
            <button 
              @click="handleSendMessage" 
              :disabled="!appState.avatar.connected || !appState.ui.text.trim() || isSending"
              class="btn btn-primary"
            >
              {{ isSending ? '发送中...' : '发送' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 配置页面 -->
      <div v-show="activeTab === 'config'" class="config-tab">
        <!-- 虚拟人配置 -->
        <section class="config-section">
          <h3 class="section-title">虚拟人 SDK 配置</h3>
          
          <div class="form-group">
            <label>应用 APP ID</label>
            <input 
              v-model="appState.avatar.appId" 
              type="text" 
              placeholder="请输入 APP ID"
            />
          </div>
          
          <div class="form-group">
            <label>应用 APP Secret</label>
            <input 
              v-model="appState.avatar.appSecret" 
              type="text" 
              placeholder="请输入 APP Secret"
            />
          </div>
        </section>

        <!-- ASR配置 -->
        <section class="config-section">
          <h3 class="section-title">语音识别配置</h3>
          
          <div class="form-group">
            <label>ASR 服务商</label>
            <select v-model="appState.asr.provider">
              <option value="tx">腾讯云</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>ASR App ID</label>
            <input 
              v-model="appState.asr.appId" 
              type="text" 
              placeholder="请输入 ASR App ID"
            />
          </div>
          
          <div class="form-group">
            <label>ASR Secret ID</label>
            <input 
              v-model="appState.asr.secretId" 
              type="text" 
              placeholder="请输入 Secret ID"
            />
          </div>
          
          <div class="form-group">
            <label>ASR Secret Key</label>
            <input 
              v-model="appState.asr.secretKey" 
              type="text" 
              placeholder="请输入 Secret Key"
            />
          </div>
        </section>

        <!-- LLM配置 -->
        <section class="config-section">
          <h3 class="section-title">大语言模型配置</h3>
          
          <div class="form-group">
            <label>API Base URL</label>
            <input 
              v-model="appState.llm.baseURL" 
              type="text" 
              placeholder="http://36.134.38.44:9000/v1"
            />
            <small class="form-hint">OpenAI 兼容 API 的基础 URL</small>
          </div>
          
          <div class="form-group">
            <label>模型名称</label>
            <input 
              v-model="appState.llm.model" 
              type="text" 
              placeholder="deepseek-chat"
            />
            <small class="form-hint">支持任何 OpenAI 兼容的模型名称</small>
          </div>
          
          <div class="form-group">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input 
                v-model="appState.llm.apiKey" 
                :type="showApiKey ? 'text' : 'password'"
                placeholder="请输入 API Key"
              />
              <button 
                type="button"
                class="toggle-visibility"
                @click="showApiKey = !showApiKey"
                :title="showApiKey ? '隐藏' : '显示'"
              >
                {{ showApiKey ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>
        </section>

        <!-- 控制按钮 -->
        <section class="control-section">
          <div class="button-group">
            <button 
              @click="handleConnect" 
              :disabled="isConnecting || appState.avatar.connected"
              class="btn btn-primary"
            >
              {{ isConnecting ? '连接中...' : appState.avatar.connected ? '已连接' : '连接' }}
            </button>
            
            <button 
              @click="handleDisconnect" 
              :disabled="!appState.avatar.connected"
              class="btn btn-secondary"
            >
              断开
            </button>
          </div>
          
          <div class="button-group" style="margin-top: 12px;">
            <button 
              @click="handleSaveConfig" 
              class="btn btn-secondary"
            >
              保存配置
            </button>
            
            <button 
              @click="handleLoadConfig" 
              class="btn btn-secondary"
            >
              加载配置
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, computed, nextTick, watch, onMounted } from 'vue'
import { useAsr } from '../composables/useAsr'
import type { AppState, AppStore } from '../types'

// 配置存储的 key
const CONFIG_STORAGE_KEY = 'xmov_avatar_config'

// 注入全局状态和方法
const appState = inject<AppState>('appState')!
const appStore = inject<AppStore>('appStore')!

// 组件状态
const activeTab = ref<'chat' | 'config'>('chat')
const isConnecting = ref(false)
const isSending = ref(false)
const showApiKey = ref(false)
const chatHistoryRef = ref<HTMLElement | null>(null)

// ASR Hook - 使用computed确保配置更新时重新创建
const asrConfig = computed(() => ({
  provider: 'tx' as const,
  appId: appState.asr.appId,
  secretId: appState.asr.secretId,
  secretKey: appState.asr.secretKey
}))

// 初始化ASR hook（用于停止功能）
const { stop: stopAsr } = useAsr(asrConfig.value)

// 格式化时间
function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// 监听对话历史变化，自动滚动到底部
watch(() => appState.chatHistory.length, () => {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
    }
  })
}, { immediate: false })

// 监听对话历史内容变化，确保所有消息都显示
watch(() => appState.chatHistory, (newHistory) => {
  console.log('对话历史内容变化，当前消息数:', newHistory.length, '消息列表:', newHistory)
  nextTick(() => {
    if (chatHistoryRef.value) {
      const messageElements = chatHistoryRef.value.querySelectorAll('.message-item')
      console.log('实际渲染的消息元素数:', messageElements.length, '容器高度:', chatHistoryRef.value.scrollHeight)
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
    }
  })
}, { deep: true })

// 处理 Shift+Enter（换行）
function handleShiftEnter() {
  // 允许换行，不做任何处理
}

// 事件处理函数
async function handleConnect() {
  if (isConnecting.value) return
  
  isConnecting.value = true
  try {
    await appStore.connectAvatar()
  } catch (error) {
    console.error('连接失败:', error)
    alert('连接失败，请检查配置信息')
  } finally {
    isConnecting.value = false
  }
}

function handleDisconnect() {
  appStore.disconnectAvatar()
}

function handleVoiceInput() {
  if (appState.asr.isListening) {
    stopAsr()
    appStore.stopVoiceInput()
    return
  }
  
  // 验证ASR配置
  const { appId, secretId, secretKey } = appState.asr
  if (!appId || !secretId || !secretKey) {
    alert('请先配置ASR信息（App ID、Secret ID、Secret Key）')
    return
  }
  
  // 创建新的ASR实例（使用当前配置）
  const { start: startAsrWithConfig, stop: stopAsrWithConfig } = useAsr({
    provider: 'tx',
    appId: appState.asr.appId,
    secretId: appState.asr.secretId,
    secretKey: appState.asr.secretKey
  })
  
  appStore.startVoiceInput({
    onFinished: (text: string) => {
      appState.ui.text = text
      stopAsrWithConfig()
      appStore.stopVoiceInput()
    },
    onError: (error: any) => {
      console.error('语音识别错误:', error)
      stopAsrWithConfig()
      appStore.stopVoiceInput()
    }
  })
  
  startAsrWithConfig({
    onFinished: (text: string) => {
      appState.ui.text = text
      appStore.stopVoiceInput()
    },
    onError: (error: any) => {
      console.error('语音识别错误:', error)
      appStore.stopVoiceInput()
    }
  })
}

async function handleSendMessage() {
  if (isSending.value || !appState.ui.text.trim()) return
  
  isSending.value = true
  try {
    await appStore.sendMessage()
  } catch (error) {
    console.error('发送消息失败:', error)
    alert('发送消息失败')
  } finally {
    isSending.value = false
  }
}

// 清空对话历史
function handleClearHistory() {
  if (appState.chatHistory.length === 0) {
    return
  }
  
  if (confirm('确定要清空所有对话历史吗？此操作不可恢复。')) {
    appState.chatHistory = []
  }
}

// 保存配置到 localStorage
function handleSaveConfig() {
  try {
    const config = {
      avatar: {
        appId: appState.avatar.appId,
        appSecret: appState.avatar.appSecret
      },
      asr: {
        provider: appState.asr.provider,
        appId: appState.asr.appId,
        secretId: appState.asr.secretId,
        secretKey: appState.asr.secretKey
      },
      llm: {
        model: appState.llm.model,
        apiKey: appState.llm.apiKey,
        baseURL: appState.llm.baseURL
      }
    }
    
    localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(config))
    alert('配置已保存')
  } catch (error) {
    console.error('保存配置失败:', error)
    alert('保存配置失败')
  }
}

// 从 localStorage 加载配置
function handleLoadConfig(showAlert = true) {
  try {
    const savedConfig = localStorage.getItem(CONFIG_STORAGE_KEY)
    if (!savedConfig) {
      if (showAlert) {
        alert('没有找到保存的配置')
      }
      return false
    }
    
    const config = JSON.parse(savedConfig)
    
    // 加载配置
    if (config.avatar) {
      appState.avatar.appId = config.avatar.appId || ''
      appState.avatar.appSecret = config.avatar.appSecret || ''
    }
    
    if (config.asr) {
      appState.asr.provider = config.asr.provider || 'tx'
      appState.asr.appId = config.asr.appId || ''
      appState.asr.secretId = config.asr.secretId || ''
      appState.asr.secretKey = config.asr.secretKey || ''
    }
    
    if (config.llm) {
      appState.llm.model = config.llm.model || ''
      appState.llm.apiKey = config.llm.apiKey || ''
      appState.llm.baseURL = config.llm.baseURL || ''
    }
    
    if (showAlert) {
      alert('配置已加载')
    }
    return true
  } catch (error) {
    console.error('加载配置失败:', error)
    if (showAlert) {
      alert('加载配置失败')
    }
    return false
  }
}

// 组件挂载时自动加载配置（静默加载，不显示提示）
onMounted(() => {
  handleLoadConfig(false)
})
</script>

<style scoped>
.config-panel {
  width: 420px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-left: 1px solid #e0e0e0;
  overflow: hidden;
}

/* Tab 导航样式 */
.tab-header {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.tab-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-button:hover {
  color: #007bff;
  background: #f0f0f0;
}

.tab-button.active {
  color: #007bff;
  border-bottom-color: #007bff;
  background: #ffffff;
}

/* Tab 内容区域 */
.tab-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 对话页面样式 */
.chat-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  background: #f9f9f9;
  min-height: 0;
  display: block;
}

.chat-history-header {
  position: sticky;
  top: 0;
  z-index: 10;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
  background: #f9f9f9;
}

.btn-clear-history {
  padding: 6px 12px;
  border: 1px solid #dc3545;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #ffffff;
  color: #dc3545;
}

.btn-clear-history:hover {
  background: #dc3545;
  color: #ffffff;
}

.message-item {
  display: block;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  width: 100%;
  box-sizing: border-box;
  min-height: 50px;
}

.message-item:last-child {
  margin-bottom: 16px;
}

.message-item.user {
  background: #e3f2fd;
}

.message-item.assistant {
  background: #f5f5f5;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 6px;
}

.message-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 6px;
  text-align: right;
}

.empty-history {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-size: 14px;
}

.chat-input-area {
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  background: #ffffff;
}

/* 配置页面样式 */
.config-tab {
  overflow-y: auto;
  padding: 16px;
  height: 100%;
}

.config-section,
.control-section {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  margin-bottom: 16px;
}

.config-section:last-child,
.control-section:last-child {
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 8px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
  font-style: italic;
}

input,
select,
textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.input-with-toggle {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-toggle input {
  padding-right: 40px;
}

.toggle-visibility {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 16px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.toggle-visibility:hover {
  color: #007bff;
}

.toggle-visibility:active {
  transform: scale(0.95);
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

textarea {
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
}

.button-group {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-voice {
  background: #28a745;
  color: white;
}

.btn-voice:hover:not(:disabled) {
  background: #1e7e34;
}

/* 滚动条美化 */
.chat-history::-webkit-scrollbar,
.config-tab::-webkit-scrollbar {
  width: 6px;
}

.chat-history::-webkit-scrollbar-track,
.config-tab::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.chat-history::-webkit-scrollbar-thumb,
.config-tab::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-history::-webkit-scrollbar-thumb:hover,
.config-tab::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
