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
              <div class="message-header">
                <div class="message-role">
                  {{ message.role === 'user' ? '我' : 'AI' }}
                </div>
                <button 
                  v-if="message.role === 'assistant'"
                  class="audio-toggle-btn" 
                  @click="toggleMessageAudio(message, index)"
                  :disabled="!appState.avatar.connected"
                  :title="appState.avatar.connected ? (isPlayingAudio(index) ? '停止播放' : '播放') : '数字人未连接'"
                >
                  <span v-if="isPlayingAudio(index)" class="playing-indicator">⏹️</span>
                  <span v-else>▶️</span>
                </button>
              </div>
              <div class="message-content">{{ message.content || '(空消息)' }}</div>
              <div class="message-time" v-if="message.timestamp">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </template>
        </div>

        <!-- 输入区域 - 大模型风格 -->
        <div class="chat-input-area">
          <div class="input-wrapper">
            <!-- 语音输入按钮（左侧） -->
            <button 
              @click="handleVoiceInput" 
              :disabled="!appState.avatar.connected || appState.asr.isListening"
              class="voice-input-btn"
              :title="appState.asr.isListening ? '正在听...' : '语音输入'"
            >
              <span v-if="appState.asr.isListening" class="listening-indicator">🎤</span>
              <span v-else>🎤</span>
            </button>
            
            <!-- 输入框 -->
            <textarea 
              v-model="appState.ui.text" 
              rows="1"
              placeholder="输入消息..."
              @keydown.enter.exact.prevent="handleSendMessage"
              @keydown.enter.shift.exact="handleShiftEnter"
              @input="handleTextareaInput"
              class="chat-textarea"
              ref="textareaRef"
            />
            
            <!-- 发送按钮（右侧） -->
            <button 
              @click="handleSendMessage" 
              :disabled="!appState.avatar.connected || !appState.ui.text.trim() || isSending"
              class="send-btn"
              :title="isSending ? '发送中...' : '发送 (Enter)'"
            >
              <span v-if="isSending" class="sending-spinner">⏳</span>
              <span v-else class="send-icon">➤</span>
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
            <div class="input-with-toggle">
              <input 
                v-model="appState.avatar.appId" 
                :type="showAppId ? 'text' : 'password'"
                placeholder="请输入 APP ID"
              />
              <button 
                type="button"
                class="toggle-visibility"
                @click="showAppId = !showAppId"
                :title="showAppId ? '隐藏' : '显示'"
              >
                {{ showAppId ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>应用 APP Secret</label>
            <div class="input-with-toggle">
              <input 
                v-model="appState.avatar.appSecret" 
                :type="showAppSecret ? 'text' : 'password'"
                placeholder="请输入 APP Secret"
              />
              <button 
                type="button"
                class="toggle-visibility"
                @click="showAppSecret = !showAppSecret"
                :title="showAppSecret ? '隐藏' : '显示'"
              >
                {{ showAppSecret ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
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
            <div class="input-with-toggle">
              <input 
                v-model="appState.asr.appId" 
                :type="showAsrAppId ? 'text' : 'password'"
                placeholder="请输入 ASR App ID"
              />
              <button 
                type="button"
                class="toggle-visibility"
                @click="showAsrAppId = !showAsrAppId"
                :title="showAsrAppId ? '隐藏' : '显示'"
              >
                {{ showAsrAppId ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>ASR Secret ID</label>
            <div class="input-with-toggle">
              <input 
                v-model="appState.asr.secretId" 
                :type="showAsrSecretId ? 'text' : 'password'"
                placeholder="请输入 Secret ID"
              />
              <button 
                type="button"
                class="toggle-visibility"
                @click="showAsrSecretId = !showAsrSecretId"
                :title="showAsrSecretId ? '隐藏' : '显示'"
              >
                {{ showAsrSecretId ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>ASR Secret Key</label>
            <div class="input-with-toggle">
              <input 
                v-model="appState.asr.secretKey" 
                :type="showAsrSecretKey ? 'text' : 'password'"
                placeholder="请输入 Secret Key"
              />
              <button 
                type="button"
                class="toggle-visibility"
                @click="showAsrSecretKey = !showAsrSecretKey"
                :title="showAsrSecretKey ? '隐藏' : '显示'"
              >
                {{ showAsrSecretKey ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
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
          
          <div class="form-group">
            <label>角色（用于设置user字段）</label>
            <input 
              v-model="appState.llm.user" 
              type="text" 
              placeholder="请输入角色"
            />
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
import type { AppState, AppStore, ChatMessage } from '../types'
import { generateSSML, delay } from '../utils'
import { avatarState } from '../stores/app'

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
const showAppId = ref(false)
const showAppSecret = ref(false)
const showAsrAppId = ref(false)
const showAsrSecretId = ref(false)
const showAsrSecretKey = ref(false)
const chatHistoryRef = ref<HTMLElement | null>(null)
const playingMessageId = ref<number | null>(null) // 当前正在播放的消息索引
const textareaRef = ref<HTMLTextAreaElement | null>(null) // 输入框引用

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

// 处理输入框输入，自动调整高度
function handleTextareaInput(event: Event) {
  const textarea = event.target as HTMLTextAreaElement
  // 重置高度以获取正确的 scrollHeight
  textarea.style.height = 'auto'
  // 设置新高度，最大 6 行
  const maxHeight = parseInt(getComputedStyle(textarea).lineHeight) * 6
  const newHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = `${newHeight}px`
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
    // 停止当前播放
    if (playingMessageId.value !== null) {
      stopMessageAudio(playingMessageId.value)
    }
    appState.chatHistory = []
    playingMessageId.value = null // 清空播放状态
  }
}

// 检查消息是否正在播放
function isPlayingAudio(index: number): boolean {
  return playingMessageId.value === index
}

// 切换播放/停止
async function toggleMessageAudio(message: ChatMessage, index: number) {
  // 如果正在播放，则停止
  if (isPlayingAudio(index)) {
    await stopMessageAudio(index)
    return
  }
  
  // 否则开始播放
  await playMessageAudio(message, index)
}

// 播放消息音频
async function playMessageAudio(message: ChatMessage, index: number) {
  console.log('开始播放消息音频:', { message, index })
  
  // 检查数字人是否已连接
  if (!appState.avatar.connected) {
    console.warn('数字人未连接 (connected=false)')
    alert('数字人未连接，请先连接数字人')
    return
  }
  
  if (!appState.avatar.instance) {
    console.warn('数字人实例不存在 (instance=null)')
    alert('数字人实例不存在，请重新连接')
    return
  }

  try {
    console.log('数字人状态:', avatarState.value)
    
    // 如果数字人正在播放其他消息，先停止
    if (playingMessageId.value !== null && playingMessageId.value !== index) {
      console.log('停止其他消息的播放...')
      await stopMessageAudio(playingMessageId.value)
      await delay(300)
    }

    // 设置正在播放的消息索引
    playingMessageId.value = index

    // 生成 SSML 格式文本
    const ssml = generateSSML(message.content)
    console.log('生成的 SSML:', ssml)
    
    // 调用数字人 SDK 的 speak 方法
    // 参数说明：speak(ssml, isStream, isEnd)
    console.log('调用 speak 方法...')
    appState.avatar.instance.speak(ssml, true, true)
    console.log('speak 方法调用完成')
    
    // 监听数字人状态变化，当停止说话时清除播放状态
    const stopWatcher = watch(() => avatarState.value, (newState) => {
      console.log('数字人状态变化:', newState)
      if (newState !== 'speak' && playingMessageId.value === index) {
        console.log('数字人停止说话，清除播放状态')
        playingMessageId.value = null
        stopWatcher() // 停止监听
      }
    })
    
    // 设置超时，防止状态监听失效
    setTimeout(() => {
      if (playingMessageId.value === index) {
        console.log('播放超时，清除播放状态')
        playingMessageId.value = null
        stopWatcher()
      }
    }, 60000) // 60秒超时
  } catch (error) {
    console.error('播放音频失败:', error)
    console.error('错误详情:', {
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    })
    playingMessageId.value = null
    alert(`播放音频失败: ${error instanceof Error ? error.message : String(error)}`)
  }
}

// 停止播放
async function stopMessageAudio(index: number) {
  console.log('停止播放消息:', index)
  
  if (!appState.avatar.connected || !appState.avatar.instance) {
    return
  }

  try {
    // 如果正在播放，停止播放
    if (playingMessageId.value === index) {
      if (avatarState.value === 'speak') {
        appState.avatar.instance.think() // 停止说话
      }
      playingMessageId.value = null
      console.log('已停止播放')
    }
  } catch (error) {
    console.error('停止播放失败:', error)
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
        baseURL: appState.llm.baseURL,
        user: appState.llm.user
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
      appState.llm.user = config.llm.user || ''
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
  // 初始化输入框高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = `${textareaRef.value.scrollHeight}px`
  }
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

/* 对话页面样式 - SillyTavern 风格 */
.chat-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  /* 毛玻璃效果 */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background-color: rgba(255, 255, 255, 0.8);
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  /* 毛玻璃效果和半透明背景 */
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  background-color: rgba(249, 249, 249, 0.6);
  min-height: 0;
  display: block;
  /* 平滑滚动 */
  scroll-behavior: smooth;
}

.chat-history-header {
  position: sticky;
  top: 0;
  z-index: 10;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  /* 毛玻璃效果 */
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  background-color: rgba(249, 249, 249, 0.8);
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
  border-radius: 10px;
  /* 毛玻璃效果和半透明背景 */
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  width: 100%;
  box-sizing: border-box;
  min-height: 50px;
  /* 边框 */
  border: 1px solid rgba(0, 0, 0, 0.05);
  /* 过渡效果 */
  transition: all 0.2s ease;
}

.message-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.message-item:last-child {
  margin-bottom: 16px;
}

.message-item.user {
  background: rgba(227, 242, 253, 0.7);
  border-color: rgba(33, 150, 243, 0.2);
}

.message-item.assistant {
  background: rgba(245, 245, 245, 0.7);
  border-color: rgba(0, 0, 0, 0.1);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: #666;
}

.audio-toggle-btn {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  min-width: 28px;
  height: 28px;
}

.audio-toggle-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(0, 123, 255, 0.3);
  transform: scale(1.05);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.audio-toggle-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.audio-toggle-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.playing-indicator {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
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
  color: rgba(153, 153, 153, 0.8);
  padding: 40px 20px;
  font-size: 14px;
  /* 毛玻璃效果 */
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  background: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  margin: 20px;
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  /* 毛玻璃效果和半透明背景 */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.9);
  /* 固定在底部 */
  flex-shrink: 0;
  /* 圆角（仅顶部） */
  border-radius: 10px 10px 0 0;
  /* 阴影 */
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

/* 大模型风格输入框 */
.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 24px;
  padding: 8px 12px;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: rgba(0, 123, 255, 0.3);
  box-shadow: 0 2px 12px rgba(0, 123, 255, 0.15);
}

.voice-input-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  font-size: 18px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  flex-shrink: 0;
  opacity: 0.7;
}

.voice-input-btn:hover:not(:disabled) {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
  transform: scale(1.1);
}

.voice-input-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.listening-indicator {
  animation: pulse 1s ease-in-out infinite;
}

.chat-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  padding: 8px 4px;
  background: transparent;
  color: #333;
  font-family: inherit;
  min-height: 24px;
  max-height: 144px; /* 约 6 行 */
  overflow-y: auto;
}

.chat-textarea::placeholder {
  color: rgba(0, 0, 0, 0.4);
}

.send-btn {
  background: rgba(0, 123, 255, 0.9);
  border: none;
  cursor: pointer;
  padding: 0;
  border-radius: 50%;
  font-size: 16px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  flex-shrink: 0;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.send-btn:hover:not(:disabled) {
  background: rgba(0, 123, 255, 1);
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.3);
}

.send-icon {
  display: inline-block;
  transform: rotate(-90deg);
  font-size: 14px;
}

.sending-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
  box-sizing: border-box;
  /* 半透明背景 */
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
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
  border-color: rgba(0, 123, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
  background: rgba(255, 255, 255, 0.95);
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
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
  /* 毛玻璃效果 */
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-primary {
  background: rgba(0, 123, 255, 0.9);
  color: white;
  border-color: rgba(0, 123, 255, 0.3);
}

.btn-primary:hover:not(:disabled) {
  background: rgba(0, 86, 179, 0.95);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(108, 117, 125, 0.9);
  color: white;
  border-color: rgba(108, 117, 125, 0.3);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(84, 91, 98, 0.95);
  box-shadow: 0 4px 8px rgba(108, 117, 125, 0.3);
  transform: translateY(-1px);
}

.btn-voice {
  background: rgba(40, 167, 69, 0.9);
  color: white;
  border-color: rgba(40, 167, 69, 0.3);
}

.btn-voice:hover:not(:disabled) {
  background: rgba(30, 126, 52, 0.95);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
  transform: translateY(-1px);
}

/* 滚动条美化 - SillyTavern 风格 */
.chat-history::-webkit-scrollbar,
.config-tab::-webkit-scrollbar {
  width: 8px;
}

.chat-history::-webkit-scrollbar-track,
.config-tab::-webkit-scrollbar-track {
  background: rgba(241, 241, 241, 0.3);
  border-radius: 4px;
}

.chat-history::-webkit-scrollbar-thumb,
.config-tab::-webkit-scrollbar-thumb {
  background: rgba(193, 193, 193, 0.6);
  border-radius: 4px;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.chat-history::-webkit-scrollbar-thumb:hover,
.config-tab::-webkit-scrollbar-thumb:hover {
  background: rgba(168, 168, 168, 0.8);
}
</style>
