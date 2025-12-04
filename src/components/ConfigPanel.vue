<template>
  <div class="config-panel">
    <!-- 对话页面 - 全屏居中布局 -->
    <div class="chat-tab">
        <!-- 历史对话面板 -->
        <div v-show="showHistoryPanel && globalApiKey" class="history-panel-wrapper">
          <!-- 关闭按钮 - 放在面板外部 -->
                    <button 
            class="history-panel-close"
            @click="showHistoryPanel = false"
            title="关闭对话面板"
                    >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
                    </button>
          <div 
            class="history-panel" 
            :style="{ height: historyPanelHeight + 'px' }"
          >
            <!-- 拖动条 -->
          <div 
            class="history-panel-resize-handle"
            @mousedown="startResize"
          ></div>
          <div class="history-list" ref="historyListRef">
            <template v-if="appState.chatHistory.length === 0">
              <div class="history-empty">暂无对话记录</div>
            </template>
            <template v-else>
              <div 
                v-for="(message, index) in appState.chatHistory" 
                :key="`${message.timestamp || index}-${index}`"
                class="history-item"
                :class="message.role"
              >
                <div class="history-item-header">
                  <!-- 角色头像（仅当设置了头像时显示） -->
                  <div 
                    v-if="message.role !== 'system' && getRoleAvatar(message.role as 'user' | 'assistant')" 
                    class="history-role-avatar"
                    @click.stop="toggleIllustration(message.role as 'user' | 'assistant')"
                    :title="getToggleIllustrationTitle(message.role as 'user' | 'assistant')"
                  >
                    <img 
                      :src="getRoleAvatarUrl(message.role as 'user' | 'assistant')" 
                      :alt="getRoleName(message.role as 'user' | 'assistant')"
                      class="role-avatar-thumbnail"
                    />
                  </div>
                  <div class="history-role-label">
                    {{ message.role === 'system' ? '系统' : getRoleName(message.role as 'user' | 'assistant') }}
                </div>
                  <div class="history-item-actions">
                  <button 
                    v-if="canPlayMessage(message)"
                      class="history-action-btn"
                      @click.stop="toggleMessageAudio(message, index)"
                      :title="playingMessageId === index ? '停止播放' : '播放语音'"
                  >
                      <svg v-if="playingMessageId === index" width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <rect x="4" y="4" width="8" height="8" rx="1" fill="currentColor"/>
                      </svg>
                      <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M6 4L12 8L6 12V4Z" fill="currentColor"/>
                      </svg>
                  </button>
                  <button 
                      class="history-action-btn"
                      @click.stop="copyMessage(message.content)"
                    title="复制"
                  >
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <rect x="4" y="4" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.2" fill="none"/>
                        <path d="M4 8V4C4 2.89543 4.89543 2 6 2H10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                      </svg>
                  </button>
                  <button 
                      class="history-action-btn"
                      @click.stop="editMessage(message, index)"
                    title="编辑"
                  >
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M11.5 2.5L13.5 4.5L5.5 12.5H3.5V10.5L11.5 2.5Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <button 
                      class="history-action-btn"
                      @click.stop="deleteMessageItem(message, index)"
                      title="删除"
                    >
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                      </svg>
                  </button>
                </div>
                </div>
                <div 
                  v-if="editingMessageId === index"
                  class="history-edit-area"
                >
                  <textarea 
                    v-model="editingContent"
                    class="history-edit-textarea"
                    @keydown.enter.exact.prevent="saveEdit(index)"
                    @keydown.enter.shift.exact=""
                    @keydown.esc="cancelEdit"
                  ></textarea>
                  <div class="history-edit-actions">
                    <button class="history-edit-btn save" @click="saveEdit(index)">保存</button>
                    <button class="history-edit-btn cancel" @click="cancelEdit">取消</button>
                  </div>
                </div>
                <div v-else class="history-content" v-html="renderMarkdown(message.content)"></div>
              </div>
          </template>
          </div>
          </div>
        </div>

        <!-- 输入区域 - 大模型风格 -->
        <div class="chat-input-area">
          <div class="input-wrapper" ref="inputWrapperRef">
            <!-- 菜单按钮（最左侧） -->
            <button 
              @click="toggleMenu" 
              class="menu-btn"
              :class="{ active: showMenu }"
              title="菜单"
            >
              <span>☰</span>
            </button>
            
            <!-- 菜单弹出层 -->
            <div v-if="showMenu" class="menu-popup" @click.stop ref="menuPopupRef">
              <div class="menu-item" @click="handleOpenApiKeyLogin">
                {{ globalApiKey ? '退出登录' : 'APIKey登录' }}
              </div>
              <div class="menu-divider"></div>
              <div class="menu-item" @click="handleOpenUserRoleManagement">用户角色管理</div>
              <div 
                class="menu-item" 
                :class="{ disabled: !globalApiKey }"
                @click="globalApiKey ? handleOpenRoleManagement() : showToastMessage('请先登录', 'error')"
              >
                伙伴角色管理
                </div>
              <div class="menu-item" @click="handleOpenMofaInviteCode">获取魔珐数字人邀请码</div>
              <div class="menu-divider"></div>
              <div 
                class="menu-item" 
                :class="{ disabled: !globalApiKey }"
                @click="globalApiKey ? toggleHistorySubmenu() : showToastMessage('请先登录', 'error')"
              >
                <span>对话历史</span>
                <span class="menu-arrow" :class="{ expanded: showHistorySubmenu }">▶</span>
                </div>
              <!-- 对话历史子菜单 -->
              <div v-if="showHistorySubmenu && globalApiKey" class="submenu">
                <div class="submenu-item" @click="toggleHistoryPanel">显示/隐藏对话历史框</div>
                <div class="submenu-item" @click="exportChatHistory">导出聊天记录</div>
                <div class="submenu-item" @click="clearChatHistory">清空历史对话</div>
                </div>
              <div class="menu-divider"></div>
              <div 
                class="menu-item" 
                :class="{ disabled: !globalApiKey }"
                @click="globalApiKey ? toggleBackgroundSubmenu() : showToastMessage('请先登录', 'error')"
              >
                <span>背景管理</span>
                <span class="menu-arrow" :class="{ expanded: showBackgroundSubmenu }">▶</span>
              </div>
              <!-- 背景管理子菜单 -->
              <div v-if="showBackgroundSubmenu && globalApiKey" class="submenu">
                <div 
                  class="submenu-item submenu-item-checkbox" 
                  :class="{ checked: autoExtractMarkdownImage }"
                  @click="toggleAutoExtractMarkdownImage"
                >
                  <span v-if="autoExtractMarkdownImage" style="margin-right: 6px;">✓</span>
                  <span v-else style="width: 12px; display: inline-block; margin-right: 6px;"></span>
                  Markdown 图像提取
                </div>
                <div class="submenu-item" @click="handleOpenBackgroundManager">背景图像管理器</div>
                <div 
                  class="submenu-item" 
                  :class="{ disabled: !appState.ui.backgroundImage }"
                  @click="appState.ui.backgroundImage ? handleSaveCurrentBackground() : showToastMessage('当前没有背景图像', 'info')"
                >
                  保存当前背景
                </div>
              </div>
              <div class="menu-divider"></div>
              <div 
                class="menu-item" 
                :class="{ disabled: !globalApiKey }"
                @click="globalApiKey ? toggleConversationModeSubmenu() : showToastMessage('请先登录', 'error')"
              >
                <span>对话模式</span>
                <span class="menu-arrow" :class="{ expanded: showConversationModeSubmenu }">▶</span>
              </div>
              <!-- 对话模式子菜单 -->
              <div v-if="showConversationModeSubmenu && globalApiKey" class="submenu">
                <div 
                  class="submenu-item submenu-item-checkbox" 
                  :class="{ checked: appState.conversationMode === 'ai' }"
                  @click="setConversationMode('ai')"
                >
                  <span v-if="appState.conversationMode === 'ai'" style="margin-right: 6px;">✓</span>
                  <span v-else style="width: 12px; display: inline-block; margin-right: 6px;"></span>
                  AI对话模式（默认）
                </div>
                <div 
                  class="submenu-item submenu-item-checkbox" 
                  :class="{ checked: appState.conversationMode === 'speech' }"
                  @click="setConversationMode('speech')"
                >
                  <span v-if="appState.conversationMode === 'speech'" style="margin-right: 6px;">✓</span>
                  <span v-else style="width: 12px; display: inline-block; margin-right: 6px;"></span>
                  演示对话模式
                </div>
              </div>
              <div class="menu-divider"></div>
              <div class="menu-item" @click="handleOpenTtsAsrSettings">TTS 和 ASR</div>
            </div>
            
            <!-- 语音输入按钮 -->
            <button 
              @click="handleVoiceInput" 
              :disabled="!appState.currentUserRole?.isConnected || appState.asr.isListening"
              class="voice-input-btn"
              :title="appState.asr.isListening ? '正在听...' : '语音输入'"
            >
              <span v-if="appState.asr.isListening" class="listening-indicator">🎤</span>
              <span v-else>🎤</span>
            </button>
            
            <!-- 演讲模式：说话人选择器 -->
            <div v-if="appState.conversationMode === 'speech'" class="speaker-selector-inline">
              <select 
                v-model="currentSpeaker" 
                class="speaker-select"
                :disabled="!appState.currentUserRole && !appState.currentPartnerRole"
              >
                <!-- 用户角色在前 -->
                <option value="user" :disabled="!appState.currentUserRole">
                  {{ appState.currentUserRole ? (appState.currentUserRole.name || appState.currentUserRole.user) : '用户角色' }}
                </option>
                <!-- 伙伴角色在后 -->
                <option value="partner" :disabled="!appState.currentPartnerRole">
                  {{ appState.currentPartnerRole ? (appState.currentPartnerRole.name || appState.currentPartnerRole.user) : '伙伴角色' }}
                </option>
              </select>
            </div>
            
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
              :disabled="!appState.ui.text.trim() || isSending || !(appState.currentPartnerRole?.user || appState.llm.user) || !globalApiKey"
              class="send-btn"
              :title="isSending ? '发送中...' : '发送 (Enter)'"
            >
              <span v-if="isSending" class="sending-spinner">⏳</span>
              <span v-else class="send-icon">➤</span>
            </button>
          </div>
        </div>
      </div>
    </div>


    <!-- TTS 和 ASR 设置模态框 -->
    <div v-if="showTtsAsrSettingsModal" class="modal-overlay" @click.self="showTtsAsrSettingsModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">TTS 和 ASR 设置</h3>
          <button class="modal-close" @click="showTtsAsrSettingsModal = false" title="关闭">×</button>
        </div>
        <div class="modal-body">
          <!-- 标签页 -->
          <div class="tabs">
            <button 
              class="tab-button" 
              :class="{ active: activeTtsAsrTab === 'tts' }"
              @click="activeTtsAsrTab = 'tts'"
            >
              TTS
            </button>
            <button 
              class="tab-button" 
              :class="{ active: activeTtsAsrTab === 'asr' }"
              @click="activeTtsAsrTab = 'asr'"
            >
              ASR
            </button>
          </div>

          <!-- TTS 标签页内容 -->
          <div v-if="activeTtsAsrTab === 'tts'" class="tab-content">
            <div class="form-group">
              <label for="tts-provider">TTS 服务商:</label>
              <select id="tts-provider" v-model="appState.tts.provider">
                <option value="doubao">豆包 TTS</option>
              </select>
            </div>
            <div class="form-group">
              <label for="tts-api-key">API Key:</label>
              <div class="input-with-toggle">
                <input 
                  id="tts-api-key"
                  :type="showTtsApiKey ? 'text' : 'password'"
                  v-model="appState.tts.apiKey"
                  placeholder="格式: AppID:AccessToken"
                />
                <button 
                  class="toggle-visibility" 
                  @click="showTtsApiKey = !showTtsApiKey"
                  :title="showTtsApiKey ? '隐藏' : '显示'"
                >
                  {{ showTtsApiKey ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
              <small class="form-hint">格式: AppID:AccessToken，例如: 1234567890:your-access-token-here</small>
            </div>
            
            <!-- 音色试听 -->
            <div class="form-group">
              <label for="tts-voice-preview">音色试听:</label>
              <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                <select id="tts-voice-preview" v-model="ttsPreviewVoice" style="flex: 1;">
                  <option value="">请选择音色</option>
                  <option v-for="voice in doubaoVoices" :key="voice.id" :value="voice.id">
                    {{ voice.name }}
                  </option>
                </select>
                <button 
                  class="btn btn-small" 
                  @click="previewTtsVoice" 
                  :disabled="!ttsPreviewVoice || !appState.tts.apiKey || !ttsPreviewText?.trim()"
                >
                  {{ isTtsPreviewPlaying ? '停止' : '试听' }}
                </button>
              </div>
              <textarea 
                id="tts-preview-text"
                v-model="ttsPreviewText"
                placeholder="请输入试听文本，或使用预设文本"
                rows="3"
                style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; resize: vertical;"
              ></textarea>
              <small class="form-hint">用于试听音色效果的文本内容</small>
            </div>
            
            <div class="form-group">
              <label for="tts-speed">语速: {{ appState.tts.speed }}</label>
              <input 
                id="tts-speed"
                type="range" 
                v-model.number="appState.tts.speed"
                min="0.1" 
                max="2.0" 
                step="0.1"
              />
            </div>
            <div class="form-group">
              <label for="tts-volume">音量: {{ appState.tts.volume }}</label>
              <input 
                id="tts-volume"
                type="range" 
                v-model.number="appState.tts.volume"
                min="0.5" 
                max="2.0" 
                step="0.1"
              />
            </div>
          </div>

          <!-- ASR 标签页内容 -->
          <div v-if="activeTtsAsrTab === 'asr'" class="tab-content">
            <div class="form-group">
              <label for="asr-provider">ASR 服务商:</label>
              <select id="asr-provider" v-model="appState.asr.provider">
                <option value="tx">腾讯云</option>
              </select>
            </div>
            <div class="form-group">
              <label for="asr-app-id">ASR App ID:</label>
              <div class="input-with-toggle">
                <input 
                  id="asr-app-id"
                  :type="showAsrAppId ? 'text' : 'password'"
                  v-model="appState.asr.appId"
                  placeholder="请输入 ASR App ID"
                />
                <button 
                  class="toggle-visibility" 
                  @click="showAsrAppId = !showAsrAppId"
                  :title="showAsrAppId ? '隐藏' : '显示'"
                >
                  {{ showAsrAppId ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
            </div>
            <div class="form-group">
              <label for="asr-secret-id">ASR Secret ID:</label>
              <div class="input-with-toggle">
                <input 
                  id="asr-secret-id"
                  :type="showAsrSecretId ? 'text' : 'password'"
                  v-model="appState.asr.secretId"
                  placeholder="请输入 ASR Secret ID"
                />
                <button 
                  class="toggle-visibility" 
                  @click="showAsrSecretId = !showAsrSecretId"
                  :title="showAsrSecretId ? '隐藏' : '显示'"
                >
                  {{ showAsrSecretId ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
            </div>
            <div class="form-group">
              <label for="asr-secret-key">ASR Secret Key:</label>
              <div class="input-with-toggle">
                <input 
                  id="asr-secret-key"
                  :type="showAsrSecretKey ? 'text' : 'password'"
                  v-model="appState.asr.secretKey"
                  placeholder="请输入 ASR Secret Key"
                />
                <button 
                  class="toggle-visibility" 
                  @click="showAsrSecretKey = !showAsrSecretKey"
                  :title="showAsrSecretKey ? '隐藏' : '显示'"
                >
                  {{ showAsrSecretKey ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="handleSaveTtsAsrSettings">保存配置</button>
        </div>
      </div>
    </div>

    <!-- 角色管理模态框 -->
    <div v-if="showRoleManagementModal" class="modal-overlay" @click.self="showRoleManagementModal = false">
      <div class="modal-content" style="max-width: 800px; max-height: 90vh; overflow-y: auto;">
        <div class="modal-header">
          <h3 class="modal-title">角色管理</h3>
          <button class="modal-close" @click="showRoleManagementModal = false" title="关闭">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 角色编辑表单 -->
          <div v-if="showRoleEditForm" class="role-edit-form">
            <h4 class="section-title">{{ editingRole ? '编辑角色' : '新建角色' }}</h4>
            <div class="form-group">
              <label for="role-user">user字段 <span style="color: red;">*</span>:</label>
              <input 
                id="role-user"
                type="text" 
                v-model="roleForm.user"
                placeholder="传给大模型的user字段值"
              />
              <small class="form-hint">此值将作为user参数传给大模型API</small>
            </div>
            <div class="form-group">
              <label for="role-type">角色类型 <span style="color: red;">*</span>:</label>
              <select id="role-type" v-model="roleForm.type">
                <option value="illustration">立绘</option>
                <option value="digital_human">数字人</option>
              </select>
            </div>
            <div class="form-group">
              <label for="role-name">角色名称:</label>
              <input 
                id="role-name"
                type="text" 
                v-model="roleForm.name"
                placeholder="请输入角色名称（可选）"
              />
            </div>
            <div class="form-group">
              <label for="role-description">角色描述:</label>
              <textarea 
                id="role-description"
                v-model="roleForm.description"
                placeholder="请输入角色描述（可选）"
                rows="3"
              ></textarea>
            </div>
            <div class="form-group">
              <label for="role-avatar">头像:</label>
              <div class="avatar-upload-area">
                <template v-if="roleForm.type === 'digital_human'">
                  <div class="avatar-preview-row">
                    <div class="avatar-preview-wrapper">
                      <!-- 图片预览 -->
                      <div v-if="roleForm.avatar" class="avatar-preview">
                        <img :src="roleForm.avatar.startsWith('http') || roleForm.avatar.startsWith('/') ? roleForm.avatar : `http://localhost:3001${roleForm.avatar}`" alt="头像预览" />
                        <button 
                          type="button"
                          class="avatar-remove-btn"
                          @click="roleForm.avatar = ''"
                          title="删除头像"
                        >
                          ×
                        </button>
                      </div>
                      <!-- 上传按钮 -->
                      <div v-else class="avatar-upload-placeholder">
                        <input 
                          id="role-avatar-file"
                          type="file"
                          accept="image/*"
                          @change="handleAvatarUpload"
                          style="display: none;"
                          ref="avatarFileInputRef"
                        />
                        <button 
                          type="button"
                          class="btn btn-secondary"
                          @click="() => avatarFileInputRef?.click()"
                        >
                          选择图片
                        </button>
                      </div>
                    </div>
                    <!-- 数字人预览容器（仅当角色类型为数字人时显示） -->
                    <div class="digital-human-preview-container">
                      <div :id="editContainerId" class="digital-human-preview"></div>
                      <div v-if="!editingRole?.isConnected" class="digital-human-placeholder">
                        <span>数字人容器</span>
                      </div>
                    </div>
                  </div>
                </template>
                <div v-else class="avatar-preview-wrapper">
                  <!-- 图片预览 -->
                  <div v-if="roleForm.avatar" class="avatar-preview">
                    <img :src="roleForm.avatar.startsWith('http') || roleForm.avatar.startsWith('/') ? roleForm.avatar : `http://localhost:3001${roleForm.avatar}`" alt="头像预览" />
                    <button 
                      type="button"
                      class="avatar-remove-btn"
                      @click="roleForm.avatar = ''"
                      title="删除头像"
                    >
                      ×
                    </button>
                  </div>
                  <!-- 上传按钮 -->
                  <div v-else class="avatar-upload-placeholder">
                    <input 
                      id="role-avatar-file"
                      type="file"
                      accept="image/*"
                      @change="handleAvatarUpload"
                      style="display: none;"
                      ref="avatarFileInputRef"
                    />
                    <button 
                      type="button"
                      class="btn btn-secondary"
                      @click="() => avatarFileInputRef?.click()"
                    >
                      选择图片
                    </button>
                  </div>
                </div>
                <!-- URL输入（可选） -->
                <div class="avatar-url-input" style="margin-top: 12px;">
                  <input 
                    id="role-avatar-url"
                    type="text" 
                    v-model="roleForm.avatar"
                    placeholder="或输入图片URL"
                    @input="handleAvatarUrlInput"
                  />
                </div>
              </div>
            </div>
            <div class="form-group">
              <label for="role-scale">缩放比例: {{ roleForm.scale.toFixed(2) }}x ({{ Math.round(512 * roleForm.scale) }}x{{ Math.round(768 * roleForm.scale) }})</label>
              <input 
                id="role-scale"
                type="range" 
                v-model.number="roleForm.scale"
                min="0.5" 
                max="2.0" 
                step="0.1"
              />
            </div>
            
            <!-- 数字人 SDK 配置（仅当角色类型为数字人时显示） -->
            <div v-if="roleForm.type === 'digital_human'">
              <div class="config-divider"></div>
              <div class="config-section">
                <h4 class="section-title">数字人SDK配置(<a href="https://c.c1nd.cn/9C9WW" target="_blank" rel="noopener noreferrer" style="color: #007bff; text-decoration: none;">魔珐星云</a>)</h4>
                <div class="form-group">
                  <label for="role-avatar-app-id">应用 APP ID:</label>
                  <input 
                    id="role-avatar-app-id"
                    type="text" 
                    v-model="roleForm.avatarAppId"
                    placeholder="请输入应用 APP ID"
                  />
                </div>
                <div class="form-group">
                  <label for="role-avatar-app-secret">应用 APP Secret:</label>
                  <div class="input-with-toggle">
                    <input 
                      id="role-avatar-app-secret"
                      :type="showAppSecret ? 'text' : 'password'"
                      v-model="roleForm.avatarAppSecret"
                      placeholder="请输入应用 APP Secret"
                    />
                    <button 
                      class="toggle-visibility" 
                      @click="showAppSecret = !showAppSecret"
                      :title="showAppSecret ? '隐藏' : '显示'"
                    >
                      {{ showAppSecret ? '👁️' : '👁️‍🗨️' }}
                    </button>
                  </div>
                </div>
                <div class="form-group">
                  <div class="connection-status">
                    <span class="status-label">连接状态:</span>
                    <span class="status-indicator" :class="{ connected: editingRole?.isConnected }">
                      {{ editingRole?.isConnected ? '● 已连接' : '○ 未连接' }}
                    </span>
                  </div>
                </div>
                <div class="form-group">
                  <div class="button-group">
                    <button 
                      class="btn btn-primary" 
                      @click="handleConnectPartnerRole"
                      :disabled="(editingRole && editingRole.isConnecting) || editingRole?.isConnected"
                    >
                      {{ (editingRole && editingRole.isConnecting) ? '连接中...' : '连接' }}
                    </button>
                    <button 
                      class="btn btn-secondary" 
                      @click="handleDisconnect"
                      :disabled="!editingRole?.isConnected"
                    >
                      断开
                    </button>
                    <button 
                      class="btn btn-secondary" 
                      @click="handleCaptureDigitalHuman"
                      :disabled="!editingRole?.isConnected"
                      title="从数字人容器中截图并设置为角色头像"
                    >
                      截图
                    </button>
                  </div>
                </div>
                
                <!-- 数字人语音选项和TTS配置 -->
                <div class="config-divider" style="margin-top: 12px;"></div>
                <div class="config-section" style="margin-top: 12px;">
                  <h4 class="section-title">语音设置</h4>
                  
                  <!-- 语音选项 -->
                  <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 8px;">
                      <input 
                        type="radio" 
                        :value="true"
                        v-model="roleForm.useDigitalHumanVoice"
                      />
                      <span>使用数字人语音</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                      <input 
                        type="radio" 
                        :value="false"
                        v-model="roleForm.useDigitalHumanVoice"
                      />
                      <span>使用TTS语音</span>
                    </label>
                  </div>
                  
                  <!-- TTS配置（仅当选择TTS时显示） -->
                  <div v-if="roleForm.useDigitalHumanVoice === false">
                    <!-- TTS引擎选择 -->
                    <div class="form-group">
                      <label for="role-digital-tts-provider">TTS 引擎:</label>
                      <select id="role-digital-tts-provider" v-model="roleForm.ttsProvider">
                        <option value="doubao">豆包 TTS</option>
                      </select>
                    </div>
                    
                    <!-- 试听文本 -->
                    <div class="form-group">
                      <label for="role-digital-tts-preview-text">试听文本:</label>
                      <textarea 
                        id="role-digital-tts-preview-text"
                        v-model="roleForm.ttsPreviewText"
                        placeholder="请输入试听文本"
                        rows="3"
                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; resize: vertical;"
                      ></textarea>
                      <small class="form-hint">用于试听音色效果的文本内容</small>
                    </div>
                    
                    <!-- 音色选择 -->
                    <div class="form-group">
                      <label for="role-digital-tts-voice">音色:</label>
                      <select id="role-digital-tts-voice" v-model="roleForm.ttsVoice">
                        <option value="">请选择音色</option>
                        <option v-for="voice in doubaoVoices" :key="voice.id" :value="voice.id">
                          {{ voice.name }} ({{ voice.id }})
                        </option>
                      </select>
                      <button 
                        class="btn btn-small" 
                        @click="previewPartnerVoice"
                        :disabled="!roleForm.ttsVoice || !roleForm.ttsPreviewText"
                        style="margin-top: 8px;"
                      >
                        {{ isPartnerPreviewPlaying ? '停止试听' : '试听' }}
                      </button>
                    </div>
                    
                    <!-- 语速 -->
                    <div class="form-group">
                      <label for="role-digital-tts-speed">语速: {{ (roleForm.ttsSpeed ?? appState.tts.speed ?? 1.0).toFixed(1) }}</label>
                      <input 
                        id="role-digital-tts-speed"
                        type="range" 
                        v-model.number="roleForm.ttsSpeed"
                        min="0.1" 
                        max="2.0" 
                        step="0.1"
                      />
                      <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.speed ?? 1.0 }}</small>
                    </div>
                    
                    <!-- 音量 -->
                    <div class="form-group">
                      <label for="role-digital-tts-volume">音量: {{ (roleForm.ttsVolume ?? appState.tts.volume ?? 1.0).toFixed(1) }}</label>
                      <input 
                        id="role-digital-tts-volume"
                        type="range" 
                        v-model.number="roleForm.ttsVolume"
                        min="0.5" 
                        max="2.0" 
                        step="0.1"
                      />
                      <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.volume ?? 1.0 }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 立绘TTS配置（仅当角色类型为立绘时显示） -->
            <div v-if="roleForm.type === 'illustration'">
              <div class="config-divider"></div>
              <div class="config-section">
                <h4 class="section-title">语音合成设置</h4>
                
                <!-- TTS引擎选择 -->
                <div class="form-group">
                  <label for="role-tts-provider">TTS 引擎:</label>
                  <select id="role-tts-provider" v-model="roleForm.ttsProvider">
                    <option value="doubao">豆包 TTS</option>
                  </select>
                </div>
                
                <!-- 试听文本 -->
                <div class="form-group">
                  <label for="role-tts-preview-text">试听文本:</label>
                  <textarea 
                    id="role-tts-preview-text"
                    v-model="roleForm.ttsPreviewText"
                    placeholder="请输入试听文本"
                    rows="3"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; resize: vertical;"
                  ></textarea>
                  <small class="form-hint">用于试听音色效果的文本内容</small>
                </div>
                
                <!-- 音色选择 -->
                <div class="form-group">
                  <label for="role-tts-voice">音色:</label>
                  <div style="display: flex; gap: 8px; align-items: center;">
                    <select id="role-tts-voice" v-model="roleForm.ttsVoice" style="flex: 1;">
                      <option value="">请选择音色</option>
                      <option v-for="voice in doubaoVoices" :key="voice.id" :value="voice.id">
                        {{ voice.name }}
                      </option>
                    </select>
                    <button class="btn btn-small" @click="previewPartnerVoice" :disabled="!roleForm.ttsVoice || !appState.tts.apiKey || !roleForm.ttsPreviewText?.trim()">
                      {{ isPartnerPreviewPlaying ? '停止' : '试听' }}
                    </button>
                  </div>
                </div>
                
                <!-- 语速 -->
                <div class="form-group">
                  <label for="role-tts-speed">语速: {{ (roleForm.ttsSpeed ?? appState.tts.speed ?? 1.0).toFixed(1) }}</label>
                  <input 
                    id="role-tts-speed"
                    type="range" 
                    v-model.number="roleForm.ttsSpeed"
                    min="0.1" 
                    max="2.0" 
                    step="0.1"
                  />
                  <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.speed ?? 1.0 }}</small>
                </div>
                
                <!-- 音量 -->
                <div class="form-group">
                  <label for="role-tts-volume">音量: {{ (roleForm.ttsVolume ?? appState.tts.volume ?? 1.0).toFixed(1) }}</label>
                  <input 
                    id="role-tts-volume"
                    type="range" 
                    v-model.number="roleForm.ttsVolume"
                    min="0.5" 
                    max="2.0" 
                    step="0.1"
                  />
                  <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.volume ?? 1.0 }}</small>
                </div>
              </div>
            </div>
            
            <!-- 语音播放控制（所有角色类型都显示） -->
            <div>
              <div class="config-divider"></div>
              <div class="config-section">
                <h4 class="section-title">语音播放控制</h4>
                
                <!-- 启用语音播放 -->
                <div class="form-group">
                  <label style="display: flex; align-items: center; gap: 8px;">
                    <input 
                      type="checkbox" 
                      v-model="roleForm.enableVoicePlay"
                    />
                    <span>启用语音播放</span>
                  </label>
                  <small class="form-hint">禁用后，点击播放按钮时不会播放该角色的语音</small>
                </div>
                
                <!-- 启用自动播放 -->
                <div class="form-group">
                  <label style="display: flex; align-items: center; gap: 8px;">
                    <input 
                      type="checkbox" 
                      v-model="roleForm.enableAutoPlay"
                    />
                    <span>启用自动播放</span>
                  </label>
                  <small class="form-hint">启用后，收到新消息时自动播放语音（需要同时启用"启用语音播放"）</small>
                </div>
                
                <!-- 自动切换角色 -->
                <div class="form-group">
                  <label style="display: flex; align-items: center; gap: 8px;">
                    <input 
                      type="checkbox" 
                      v-model="roleForm.enableAutoSwitch"
                    />
                    <span>自动切换角色</span>
                  </label>
                  <small class="form-hint">启用后，根据当前说话人自动显示/隐藏角色</small>
                </div>
              </div>
            </div>
            
            <div class="config-divider"></div>
            
            <!-- 大模型设置 -->
            <div class="config-section">
              <h4 class="section-title">大模型设置</h4>
              <div class="form-group">
                <label for="role-api-key">API Key:</label>
                <div class="input-with-toggle">
                  <input 
                    id="role-api-key"
                    :type="showRoleApiKey ? 'text' : 'password'"
                    :value="roleForm.apiKey || ''"
                    disabled
                    placeholder="伙伴角色的 API Key"
                  />
                  <button 
                    class="toggle-visibility" 
                    @click="showRoleApiKey = !showRoleApiKey"
                    :title="showRoleApiKey ? '隐藏' : '显示'"
                  >
                    {{ showRoleApiKey ? '👁️' : '👁️‍🗨️' }}
                  </button>
                </div>
                <small class="form-hint">伙伴角色的 API Key（只读）</small>
              </div>
              <div class="form-group">
                <label for="role-model">模型名称 <span style="color: red;">*</span>:</label>
                <input 
                  id="role-model"
                  type="text" 
                  v-model="roleForm.model"
                  placeholder="请输入模型名称（必填）"
                  required
                />
                <small class="form-hint">伙伴角色的模型名称（必填，可编辑）</small>
              </div>
            </div>
            
            <div class="form-actions">
              <button class="btn btn-primary" @click="handleSaveRole">保存</button>
              <button class="btn btn-secondary" @click="handleCancelRoleEdit">取消</button>
            </div>
          </div>
          
          <!-- 角色列表 -->
          <div v-else>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <h4 class="section-title">角色列表</h4>
              <button class="btn btn-primary" @click="handleCreateRole">新建角色</button>
            </div>
            
            <div v-if="roles.length === 0" class="history-empty">
              暂无角色，点击"新建角色"创建
            </div>
            
            <div v-else class="role-list">
              <div 
                v-for="role in roles" 
                :key="role.id"
                class="role-item"
                :class="{ 'current-role': appState.llm.user === role.user }"
              >
                <div class="role-item-content">
                  <div class="role-item-header">
                    <div class="role-item-name">
                      {{ role.name || role.user || '(未命名)' }}
                      <span class="role-type-badge" :class="role.type">{{ role.type === 'digital_human' ? '数字人' : '立绘' }}</span>
                      <span v-if="appState.llm.user === role.user" class="current-badge">当前</span>
                    </div>
                    <div class="role-item-user">user: {{ role.user }}</div>
                  </div>
                  <div v-if="role.description" class="role-item-description">{{ role.description }}</div>
                  <div v-if="role.avatar" class="role-item-avatar">
                    <img :src="role.avatar.startsWith('http') || role.avatar.startsWith('/') ? role.avatar : `http://localhost:3001${role.avatar}`" :alt="role.name || '角色头像'" style="max-width: 100px; max-height: 100px; border-radius: 4px;" />
                  </div>
                </div>
                <div class="role-item-actions">
                  <template v-if="role.type === 'digital_human'">
                    <div class="role-connection-status" style="display: flex; align-items: center; gap: 8px; margin-right: 8px;">
                      <span class="status-indicator" :class="{ connected: role.isConnected && appState.llm.user === role.user }">
                        {{ role.isConnected && appState.llm.user === role.user ? '● 已连接' : '○ 未连接' }}
                      </span>
                    </div>
                    <button 
                      class="btn btn-small btn-primary" 
                      @click="handleConnectRoleFromList(role)"
                      :disabled="role.isConnecting || role.isConnected || !appState.currentPartnerRole || appState.currentPartnerRole.user !== role.user"
                      :title="!appState.currentPartnerRole || appState.currentPartnerRole.user !== role.user ? '只有当前角色可以连接' : ''"
                    >
                      {{ role.isConnecting ? '连接中...' : '连接' }}
                    </button>
                    <button 
                      class="btn btn-small btn-secondary" 
                      @click="handleDisconnectRoleFromList(role)"
                      :disabled="!role.isConnected"
                    >
                      断开
                    </button>
                  </template>
                  <button class="btn btn-small btn-primary" @click="handleSetCurrentRole(role)">设为当前</button>
                  <button class="btn btn-small" @click="handleEditRole(role)">编辑</button>
                  <button class="btn btn-small btn-danger" @click="handleDeleteRole(role)">删除</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- APIKey登录模态框 -->
    <div v-if="showApiKeyLoginModal" class="modal-overlay" @click.self="showApiKeyLoginModal = false">
      <div class="modal-content" style="max-width: 500px;">
        <div class="modal-header">
          <h3 class="modal-title">{{ globalApiKey ? '退出登录' : 'APIKey登录' }}</h3>
          <button class="modal-close" @click="showApiKeyLoginModal = false" title="关闭">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 如果已登录，显示退出登录界面 -->
          <div v-if="globalApiKey" class="login-section">
            <div class="form-group">
              <p style="margin: 0 0 16px 0; color: #666;">当前已登录，点击下方按钮退出登录</p>
            </div>
            <div class="form-actions">
              <button class="btn btn-secondary" @click="handleLogoutAndClose">退出登录</button>
              <button class="btn btn-primary" @click="showApiKeyLoginModal = false">取消</button>
            </div>
          </div>
          
          <!-- 如果未登录，显示登录界面 -->
          <div v-else class="login-section">
            <div class="form-group">
              <label for="api-key-login-input">API Key <span style="color: red;">*</span>:</label>
              <div class="input-with-toggle">
                <input 
                  id="api-key-login-input"
                  :type="showApiKeyLoginInput ? 'text' : 'password'"
                  v-model="loginApiKeyInput"
                  placeholder="请输入 API Key"
                  @keyup.enter="handleApiKeyLogin"
                />
                <button 
                  class="toggle-visibility" 
                  @click="showApiKeyLoginInput = !showApiKeyLoginInput"
                  :title="showApiKeyLoginInput ? '隐藏' : '显示'"
                >
                  {{ showApiKeyLoginInput ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
              <small class="form-hint">输入 API Key 以登录您的账号</small>
            </div>
            <div class="form-actions">
              <button class="btn btn-primary" @click="handleApiKeyLogin">确认登录</button>
              <button class="btn btn-secondary" @click="showApiKeyLoginModal = false">取消</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户角色管理模态框 -->
    <div v-if="showUserRoleManagementModal" class="modal-overlay" @click.self="showUserRoleManagementModal = false">
      <div class="modal-content" :style="!globalApiKey ? 'max-width: 500px;' : 'max-width: 800px; max-height: 90vh; overflow-y: auto;'">
        <div class="modal-header">
          <h3 class="modal-title">{{ !globalApiKey ? 'APIKey登录' : '用户角色管理' }}</h3>
          <button class="modal-close" @click="showUserRoleManagementModal = false" title="关闭">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 登录界面（如果未登录） -->
          <div v-if="!globalApiKey" class="login-section">
            <div class="form-group">
              <label for="login-api-key">API Key <span style="color: red;">*</span>:</label>
              <div class="input-with-toggle">
                <input 
                  id="login-api-key"
                  :type="showUserRoleApiKey ? 'text' : 'password'"
                  v-model="loginApiKeyInput"
                  placeholder="请输入 API Key"
                  @keyup.enter="handleLogin"
                />
                <button 
                  class="toggle-visibility" 
                  @click="showUserRoleApiKey = !showUserRoleApiKey"
                  :title="showUserRoleApiKey ? '隐藏' : '显示'"
                >
                  {{ showUserRoleApiKey ? '👁️' : '👁️‍🗨️' }}
                </button>
              </div>
              <small class="form-hint">输入 API Key 以登录您的账号</small>
            </div>
            <div class="form-actions">
              <button class="btn btn-primary" @click="handleLogin">确认登录</button>
              <button class="btn btn-secondary" @click="showUserRoleManagementModal = false">取消</button>
            </div>
          </div>
          
          <!-- 用户角色编辑表单 -->
          <div v-else-if="showUserRoleEditForm" class="user-role-edit-form">
            <h4 class="section-title">{{ editingUserRole ? '编辑用户角色' : '新建用户角色' }}</h4>
            
            <!-- 大模型设置 -->
            <div class="config-section">
              <h4 class="section-title">大模型设置</h4>
              <div class="form-group">
                <label for="user-role-base-url">API Base URL:</label>
                <input 
                  id="user-role-base-url"
                  type="text" 
                  v-model="userRoleForm.baseURL"
                  placeholder="请输入 API Base URL（可选）"
                />
              </div>
              <div class="form-group">
                <label for="user-role-model">模型名称:</label>
                <input 
                  id="user-role-model"
                  type="text" 
                  v-model="userRoleForm.model"
                  placeholder="请输入模型名称（可选）"
                />
              </div>
              <div class="form-group">
                <label for="user-role-api-key">API Key:</label>
                <div class="input-with-toggle">
                  <input 
                    id="user-role-api-key"
                    :type="showUserRoleApiKey ? 'text' : 'password'"
                    :value="globalApiKey"
                    disabled
                    placeholder="使用登录的 API Key"
                  />
                  <button 
                    class="toggle-visibility" 
                    @click="showUserRoleApiKey = !showUserRoleApiKey"
                    :title="showUserRoleApiKey ? '隐藏' : '显示'"
                  >
                    {{ showUserRoleApiKey ? '👁️' : '👁️‍🗨️' }}
                  </button>
                </div>
                <small class="form-hint">固定使用登录的 API Key，不可编辑</small>
              </div>
            </div>
            
            <div class="config-divider"></div>
            
            <!-- 角色信息 -->
            <div class="config-section">
              <h4 class="section-title">角色信息</h4>
              <div class="form-group">
                <label for="user-role-type">角色类型:</label>
                <select id="user-role-type" v-model="userRoleForm.type">
                  <option value="illustration">立绘</option>
                  <option value="digital_human">数字人</option>
                </select>
              </div>
              <div class="form-group">
                <label for="user-role-user">user字段 <span style="color: red;">*</span>:</label>
                <input 
                  id="user-role-user"
                  type="text" 
                  v-model="userRoleForm.user"
                  placeholder="传给大模型的user字段值"
                />
                <small class="form-hint">此值仅用于和伙伴角色形式一致，调用大模型时以伙伴角色的user为准</small>
              </div>
              <div class="form-group">
                <label for="user-role-name">角色名称:</label>
                <input 
                  id="user-role-name"
                  type="text" 
                  v-model="userRoleForm.name"
                  placeholder="请输入角色名称（可选）"
                />
                <small class="form-hint">如果未设置，对话历史中显示user字段的值</small>
              </div>
              <div class="form-group">
                <label for="user-role-avatar">头像:</label>
                <div class="avatar-upload-area">
                  <template v-if="userRoleForm.type === 'digital_human'">
                    <div class="avatar-preview-row">
                      <div class="avatar-preview-wrapper">
                        <!-- 图片预览 -->
                        <div v-if="userRoleForm.avatar" class="avatar-preview">
                          <img :src="userRoleForm.avatar.startsWith('http') || userRoleForm.avatar.startsWith('/') ? userRoleForm.avatar : `http://localhost:3001${userRoleForm.avatar}`" alt="头像预览" />
                          <button 
                            type="button"
                            class="avatar-remove-btn"
                            @click="userRoleForm.avatar = ''"
                            title="删除头像"
                          >
                            ×
                          </button>
                        </div>
                        <!-- 上传按钮 -->
                        <div v-else class="avatar-upload-placeholder">
                          <input 
                            id="user-role-avatar-file"
                            type="file"
                            accept="image/*"
                            @change="handleUserRoleAvatarUpload"
                            style="display: none;"
                            ref="userRoleAvatarFileInputRef"
                          />
                          <button 
                            type="button"
                            class="btn btn-secondary"
                            @click="() => userRoleAvatarFileInputRef?.click()"
                          >
                            选择图片
                          </button>
                        </div>
                      </div>
                      <!-- 数字人预览容器 -->
                      <div class="digital-human-preview-container">
                        <div :id="userRoleEditContainerId" class="digital-human-preview"></div>
                        <div v-if="!editingUserRole?.isConnected" class="digital-human-placeholder">
                          <span>数字人容器</span>
                        </div>
                      </div>
                    </div>
                    <!-- URL输入（可选） -->
                    <div class="avatar-url-input" style="margin-top: 12px;">
                      <input 
                        id="user-role-avatar-url"
                        type="text" 
                        v-model="userRoleForm.avatar"
                        placeholder="或输入图片URL"
                      />
                    </div>
                    <!-- 缩放比例 -->
                    <div class="form-group" style="margin-top: 12px;">
                      <label for="user-role-scale">缩放比例: {{ userRoleForm.scale.toFixed(2) }}x</label>
                      <input 
                        id="user-role-scale"
                        type="range" 
                        v-model.number="userRoleForm.scale"
                        min="0.5" 
                        max="2.0" 
                        step="0.1"
                      />
                    </div>
                    <!-- 数字人 SDK 配置 -->
                    <div class="config-divider" style="margin-top: 12px;"></div>
                    <div class="config-section" style="margin-top: 12px;">
                      <h4 class="section-title">数字人SDK配置(<a href="https://c.c1nd.cn/9C9WW" target="_blank" rel="noopener noreferrer" style="color: #007bff; text-decoration: none;">魔珐星云</a>)</h4>
                      <div class="form-group">
                        <label>应用 APP ID</label>
                        <input 
                          v-model="userRoleForm.avatarAppId" 
                          type="text" 
                          placeholder="请输入应用 APP ID"
                        />
                      </div>
                      <div class="form-group">
                        <label>应用 APP Secret</label>
                        <div class="input-with-toggle">
                          <input 
                            :type="showAppSecret ? 'text' : 'password'"
                            v-model="userRoleForm.avatarAppSecret" 
                            placeholder="请输入应用 APP Secret"
                          />
                          <button 
                            class="toggle-visibility" 
                            @click="showAppSecret = !showAppSecret"
                            :title="showAppSecret ? '隐藏' : '显示'"
                          >
                            {{ showAppSecret ? '👁️' : '👁️‍🗨️' }}
                          </button>
                        </div>
                      </div>
                      <div class="button-group" style="margin-top: 12px;">
                        <button 
                          class="btn btn-primary"
                          @click="handleConnectUserRole"
                          :disabled="(editingUserRole && editingUserRole.isConnecting) || editingUserRole?.isConnected"
                        >
                          {{ (editingUserRole && editingUserRole.isConnecting) ? '连接中...' : editingUserRole?.isConnected ? '已连接' : '连接' }}
                        </button>
                        <button 
                          class="btn btn-secondary"
                          @click="handleDisconnect"
                          :disabled="!editingUserRole?.isConnected"
                        >
                          断开
                        </button>
                        <button 
                          class="btn btn-secondary" 
                          @click="handleCaptureDigitalHuman"
                          :disabled="!editingUserRole?.isConnected"
                          title="从数字人容器中截图并设置为角色头像"
                        >
                          截图
                        </button>
                      </div>
                      
                      <!-- 数字人语音选项和TTS配置 -->
                      <div class="config-divider" style="margin-top: 12px;"></div>
                      <div class="config-section" style="margin-top: 12px;">
                        <h4 class="section-title">语音设置</h4>
                        
                        <!-- 语音选项 -->
                        <div class="form-group">
                          <label style="display: flex; align-items: center; gap: 8px;">
                            <input 
                              type="radio" 
                              :value="true"
                              v-model="userRoleForm.useDigitalHumanVoice"
                            />
                            <span>使用数字人语音</span>
                          </label>
                          <label style="display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                            <input 
                              type="radio" 
                              :value="false"
                              v-model="userRoleForm.useDigitalHumanVoice"
                            />
                            <span>使用TTS语音</span>
                          </label>
                        </div>
                        
                        <!-- TTS配置（仅当选择TTS时显示） -->
                        <div v-if="userRoleForm.useDigitalHumanVoice === false">
                          <!-- TTS引擎选择 -->
                          <div class="form-group">
                            <label for="user-role-digital-tts-provider">TTS 引擎:</label>
                            <select id="user-role-digital-tts-provider" v-model="userRoleForm.ttsProvider">
                              <option value="doubao">豆包 TTS</option>
                            </select>
                          </div>
                          
                          <!-- 试听文本 -->
                          <div class="form-group">
                            <label for="user-role-digital-tts-preview-text">试听文本:</label>
                            <textarea 
                              id="user-role-digital-tts-preview-text"
                              v-model="userRoleForm.ttsPreviewText"
                              placeholder="请输入试听文本"
                              rows="3"
                              style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; resize: vertical;"
                            ></textarea>
                            <small class="form-hint">用于试听音色效果的文本内容</small>
                          </div>
                          
                          <!-- 音色选择 -->
                          <div class="form-group">
                            <label for="user-role-digital-tts-voice">音色:</label>
                            <select id="user-role-digital-tts-voice" v-model="userRoleForm.ttsVoice">
                              <option value="">请选择音色</option>
                              <option v-for="voice in doubaoVoices" :key="voice.id" :value="voice.id">
                                {{ voice.name }} ({{ voice.id }})
                              </option>
                            </select>
                            <button 
                              class="btn btn-small" 
                              @click="previewUserVoice"
                              :disabled="!userRoleForm.ttsVoice || !userRoleForm.ttsPreviewText"
                              style="margin-top: 8px;"
                            >
                              {{ isUserPreviewPlaying ? '停止试听' : '试听' }}
                            </button>
                          </div>
                          
                          <!-- 语速 -->
                          <div class="form-group">
                            <label for="user-role-digital-tts-speed">语速: {{ (userRoleForm.ttsSpeed ?? appState.tts.speed ?? 1.0).toFixed(1) }}</label>
                            <input 
                              id="user-role-digital-tts-speed"
                              type="range" 
                              v-model.number="userRoleForm.ttsSpeed"
                              min="0.1" 
                              max="2.0" 
                              step="0.1"
                            />
                            <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.speed ?? 1.0 }}</small>
                          </div>
                          
                          <!-- 音量 -->
                          <div class="form-group">
                            <label for="user-role-digital-tts-volume">音量: {{ (userRoleForm.ttsVolume ?? appState.tts.volume ?? 1.0).toFixed(1) }}</label>
                            <input 
                              id="user-role-digital-tts-volume"
                              type="range" 
                              v-model.number="userRoleForm.ttsVolume"
                              min="0.5" 
                              max="2.0" 
                              step="0.1"
                            />
                            <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.volume ?? 1.0 }}</small>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                  <div v-else class="avatar-preview-wrapper">
                    <!-- 图片预览 -->
                    <div v-if="userRoleForm.avatar" class="avatar-preview">
                      <img :src="userRoleForm.avatar.startsWith('http') || userRoleForm.avatar.startsWith('/') ? userRoleForm.avatar : `http://localhost:3001${userRoleForm.avatar}`" alt="头像预览" />
                      <button 
                        type="button"
                        class="avatar-remove-btn"
                        @click="userRoleForm.avatar = ''"
                        title="删除头像"
                      >
                        ×
                      </button>
                    </div>
                    <!-- 上传按钮 -->
                    <div v-else class="avatar-upload-placeholder">
                      <input 
                        id="user-role-avatar-file"
                        type="file"
                        accept="image/*"
                        @change="handleUserRoleAvatarUpload"
                        style="display: none;"
                        ref="userRoleAvatarFileInputRef"
                      />
                      <button 
                        type="button"
                        class="btn btn-secondary"
                        @click="() => userRoleAvatarFileInputRef?.click()"
                      >
                        选择图片
                      </button>
                    </div>
                  <!-- URL输入（可选） -->
                  <div class="avatar-url-input" style="margin-top: 12px;">
                    <input 
                      id="user-role-avatar-url"
                      type="text" 
                      v-model="userRoleForm.avatar"
                      placeholder="或输入图片URL"
                    />
                  </div>
                  <!-- 缩放比例 -->
                  <div class="form-group" style="margin-top: 12px;">
                    <label for="user-role-scale">缩放比例: {{ userRoleForm.scale.toFixed(2) }}x</label>
                    <input 
                      id="user-role-scale"
                      type="range" 
                      v-model.number="userRoleForm.scale"
                      min="0.5" 
                      max="2.0" 
                      step="0.1"
                    />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 立绘TTS配置（仅当角色类型为立绘时显示） -->
            <div v-if="userRoleForm.type === 'illustration'">
              <div class="config-divider"></div>
              <div class="config-section">
                <h4 class="section-title">语音合成设置</h4>
                
                <!-- TTS引擎选择 -->
                <div class="form-group">
                  <label for="user-role-tts-provider">TTS 引擎:</label>
                  <select id="user-role-tts-provider" v-model="userRoleForm.ttsProvider">
                    <option value="doubao">豆包 TTS</option>
                  </select>
                </div>
                
                <!-- 试听文本 -->
                <div class="form-group">
                  <label for="user-role-tts-preview-text">试听文本:</label>
                  <textarea 
                    id="user-role-tts-preview-text"
                    v-model="userRoleForm.ttsPreviewText"
                    placeholder="请输入试听文本"
                    rows="3"
                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; resize: vertical;"
                  ></textarea>
                  <small class="form-hint">用于试听音色效果的文本内容</small>
                </div>
                
                <!-- 音色选择 -->
                <div class="form-group">
                  <label for="user-role-tts-voice">音色:</label>
                  <div style="display: flex; gap: 8px; align-items: center;">
                    <select id="user-role-tts-voice" v-model="userRoleForm.ttsVoice" style="flex: 1;">
                      <option value="">请选择音色</option>
                      <option v-for="voice in doubaoVoices" :key="voice.id" :value="voice.id">
                        {{ voice.name }}
                      </option>
                    </select>
                    <button class="btn btn-small" @click="previewUserVoice" :disabled="!userRoleForm.ttsVoice || !appState.tts.apiKey || !userRoleForm.ttsPreviewText?.trim()">
                      {{ isUserPreviewPlaying ? '停止' : '试听' }}
                    </button>
                  </div>
                </div>
                
                <!-- 语速 -->
                <div class="form-group">
                  <label for="user-role-tts-speed">语速: {{ (userRoleForm.ttsSpeed ?? appState.tts.speed ?? 1.0).toFixed(1) }}</label>
                  <input 
                    id="user-role-tts-speed"
                    type="range" 
                    v-model.number="userRoleForm.ttsSpeed"
                    min="0.1" 
                    max="2.0" 
                    step="0.1"
                  />
                  <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.speed ?? 1.0 }}</small>
                </div>
                
                <!-- 音量 -->
                <div class="form-group">
                  <label for="user-role-tts-volume">音量: {{ (userRoleForm.ttsVolume ?? appState.tts.volume ?? 1.0).toFixed(1) }}</label>
                  <input 
                    id="user-role-tts-volume"
                    type="range" 
                    v-model.number="userRoleForm.ttsVolume"
                    min="0.5" 
                    max="2.0" 
                    step="0.1"
                  />
                  <small class="form-hint">默认使用TTS面板设置: {{ appState.tts.volume ?? 1.0 }}</small>
                </div>
              </div>
            </div>
            
            <!-- 语音播放控制（所有角色类型都显示） -->
            <div>
              <div class="config-divider"></div>
              <div class="config-section">
                <h4 class="section-title">语音播放控制</h4>
                
                <!-- 启用语音播放 -->
                <div class="form-group">
                  <label style="display: flex; align-items: center; gap: 8px;">
                    <input 
                      type="checkbox" 
                      v-model="userRoleForm.enableVoicePlay"
                    />
                    <span>启用语音播放</span>
                  </label>
                  <small class="form-hint">禁用后，点击播放按钮时不会播放该角色的语音</small>
                </div>
                
                <!-- 启用自动播放 -->
                <div class="form-group">
                  <label style="display: flex; align-items: center; gap: 8px;">
                    <input 
                      type="checkbox" 
                      v-model="userRoleForm.enableAutoPlay"
                    />
                    <span>启用自动播放</span>
                  </label>
                  <small class="form-hint">启用后，收到新消息时自动播放语音（需要同时启用"启用语音播放"）</small>
                </div>
                
                <!-- 自动切换角色 -->
                <div class="form-group">
                  <label style="display: flex; align-items: center; gap: 8px;">
                    <input 
                      type="checkbox" 
                      v-model="userRoleForm.enableAutoSwitch"
                    />
                    <span>自动切换角色</span>
                  </label>
                  <small class="form-hint">启用后，根据当前说话人自动显示/隐藏角色</small>
                </div>
              </div>
            </div>
            
            <div class="config-divider"></div>
            
            <div class="form-actions">
              <button class="btn btn-primary" @click="handleSaveUserRole">保存</button>
              <button class="btn btn-secondary" @click="handleCancelUserRoleEdit">取消</button>
            </div>
          </div>
          
          <!-- 用户角色列表 -->
          <div v-else>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <h4 class="section-title">用户角色列表</h4>
              <div style="display: flex; gap: 8px;">
                <button class="btn btn-secondary" @click="handleLogout">退出登录</button>
                <button class="btn btn-primary" @click="handleCreateUserRole">新建角色</button>
              </div>
            </div>
            
            <div v-if="userRoles.length === 0" class="history-empty">
              暂无用户角色，点击"新建角色"创建
            </div>
            
            <div v-else class="role-list">
              <div 
                v-for="role in userRoles" 
                :key="role.id"
                class="role-item"
                :class="{ 'current-role': role.isCurrent }"
              >
                <div class="role-item-content">
                  <div class="role-item-header">
                    <div class="role-item-name">
                      {{ role.name || role.user || '(未命名)' }}
                      <span class="role-type-badge" :class="role.type || 'illustration'">{{ (role.type || 'illustration') === 'digital_human' ? '数字人' : '立绘' }}</span>
                      <span v-if="role.isCurrent" class="current-badge">当前</span>
                    </div>
                  </div>
                  <div v-if="role.avatar" class="role-item-avatar">
                    <img :src="role.avatar.startsWith('http') || role.avatar.startsWith('/') ? role.avatar : `http://localhost:3001${role.avatar}`" :alt="role.name || '用户角色头像'" style="max-width: 100px; max-height: 100px; border-radius: 4px;" />
                  </div>
                </div>
                <div class="role-item-actions">
                  <template v-if="(role.type || 'illustration') === 'digital_human'">
                    <div class="role-connection-status" style="display: flex; align-items: center; gap: 8px; margin-right: 8px;">
                      <span class="status-indicator" :class="{ connected: role.isConnected && role.isCurrent }">
                        {{ role.isConnected && role.isCurrent ? '● 已连接' : '○ 未连接' }}
                      </span>
                    </div>
                    <button 
                      class="btn btn-small btn-primary" 
                      @click="handleConnectUserRoleFromList(role)"
                      :disabled="role.isConnecting || role.isConnected || !role.isCurrent"
                      :title="!role.isCurrent ? '只有当前角色可以连接' : ''"
                    >
                      {{ role.isConnecting ? '连接中...' : '连接' }}
                    </button>
                    <button 
                      class="btn btn-small btn-secondary" 
                      @click="handleDisconnectUserRoleFromList(role)"
                      :disabled="!role.isConnected"
                    >
                      断开
                    </button>
                  </template>
                  <button class="btn btn-small btn-primary" @click="handleSetCurrentUserRole(role)" :disabled="role.isCurrent">设为当前</button>
                  <button class="btn btn-small" @click="handleEditUserRole(role)">编辑</button>
                  <button class="btn btn-small btn-danger" @click="handleDeleteUserRole(role)">删除</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast 提示框 -->
    <Transition name="toast">
      <div v-if="showToast" class="toast" :class="toastType">
        <div class="toast-content">
          <svg v-if="toastType === 'success'" class="toast-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M13.3333 4L6 11.3333L2.66667 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else-if="toastType === 'error'" class="toast-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else class="toast-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 10.6667V8M8 5.33333H8.00667" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="toast-text">{{ toastMessage }}</span>
        </div>
      </div>
    </Transition>
    
    <!-- 背景管理器模态框 -->
    <div v-if="showBackgroundManagerModal" class="modal-overlay" @click.self="showBackgroundManagerModal = false">
      <div class="modal-content" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
      <div class="modal-header">
        <h3 class="modal-title">背景图像管理器</h3>
        <button class="modal-close" @click="showBackgroundManagerModal = false" title="关闭">×</button>
      </div>
      
      <div class="modal-body">
        <!-- 工具栏 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px;">
          <div style="display: flex; gap: 8px;">
            <label class="btn btn-primary" style="cursor: pointer; margin: 0;">
              上传背景
              <input 
                ref="backgroundFileInputRef"
                type="file" 
                accept="image/*" 
                @change="handleUploadBackground"
                style="display: none;"
              />
            </label>
            <button class="btn btn-secondary" @click="handleClearBackground">清空当前背景</button>
          </div>
        </div>
        
        <!-- 背景列表 -->
        <div v-if="backgrounds.length === 0" class="history-empty">
          暂无背景图像，点击"上传背景"添加
        </div>
        
        <div v-else class="background-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px;">
          <div 
            v-for="background in backgrounds" 
            :key="background.id"
            class="background-item"
            :title="background.name || '未命名背景'"
          >
            <div class="background-thumbnail">
              <img 
                :src="getBackgroundUrl(background.url)" 
                :alt="background.name || '背景'"
                @error="handleBackgroundImageError"
              />
              <div class="background-overlay">
                <div class="background-name">{{ background.name || '(未命名)' }}</div>
                <div class="background-actions">
                  <button 
                    class="btn-icon" 
                    @click.stop="handleSetBackground(background)"
                    title="设置为当前背景"
                  >
                    ⚙️
                  </button>
                  <button 
                    class="btn-icon" 
                    @click.stop="handleRenameBackground(background)"
                    title="重命名"
                  >
                    ✏️
                  </button>
                  <button 
                    class="btn-icon" 
                    @click.stop="handleDownloadBackground(background)"
                    title="下载"
                  >
                    ⬇️
                  </button>
                  <button 
                    class="btn-icon btn-icon-danger" 
                    @click.stop="handleDeleteBackground(background)"
                    title="删除"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
  </div>
  
  <!-- 裁剪弹窗 - 使用 Teleport 传送到 body，避免层级限制 -->
  <Teleport to="body">
    <div v-if="showCropModal" class="crop-modal-overlay" @click.self="closeCropModal">
      <div class="crop-modal">
      <div class="crop-modal-header">
        <h3>裁剪头像</h3>
        <button class="crop-modal-close" @click="closeCropModal" title="关闭">×</button>
      </div>
      <div class="crop-modal-body">
        <div class="crop-container">
          <img ref="cropImageRef" :src="cropImageSrc" alt="裁剪图片" />
        </div>
      </div>
        <div class="crop-modal-footer">
          <button class="btn btn-primary" @click="confirmCrop">确认裁剪</button>
          <button class="btn btn-secondary" @click="closeCropModal">取消</button>
        </div>
      </div>
    </div>
  </Teleport>
  
  <!-- 魔珐数字人邀请码模态框 -->
  <div v-if="showMofaInviteCodeModal" class="modal-overlay" @click.self="showMofaInviteCodeModal = false">
    <div class="modal-content" style="max-width: 500px; max-height: 90vh; overflow-y: auto;">
      <div class="modal-header">
        <h3 class="modal-title">获取魔珐数字人邀请码</h3>
        <button class="modal-close" @click="showMofaInviteCodeModal = false" title="关闭">×</button>
      </div>
      
      <div class="modal-body" style="text-align: center; padding: 20px;">
        <p style="font-size: 16px; color: #333; margin-bottom: 10px;">微信扫码添加好友获取魔珐邀请码：AI小世界</p>
        <p style="font-size: 14px; color: #666; margin-bottom: 20px;">微信号：wxid_flv5k4r9ya0n</p>
        <img 
          src="/wechatgroup.png" 
          alt="魔珐数字人邀请码二维码" 
          style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;"
          @error="handleQrCodeImageError"
        />
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { inject, ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import type { Ref } from 'vue'
import { useAsr } from '../composables/useAsr'
import type { AppState, AppStore, ChatMessage, Role } from '../types'
import { getChatHistory, updateChatMessage, deleteChatMessage, saveChatMessage, clearChatHistory as clearChatHistoryService } from '../services/chatHistory'
import { getRoles, createRole, updateRole, deleteRole } from '../services/roleManagement'
import { getUserRoles, createUserRole, updateUserRole, deleteUserRole, setCurrentUserRole } from '../services/userRoleManagement'
import { getBackgrounds, uploadBackground, createBackgroundFromUrl, updateBackground, deleteBackground } from '../services/backgroundManagement'
import type { UserRole, Background } from '../types'
import { marked } from 'marked'
import removeMarkdown from 'remove-markdown'
import { extractMarkdownImages, removeMarkdownImages, generateSSML, delay } from '../utils'
import { avatarState } from '../stores/app'
import { avatarService } from '../services/avatar'
import { generateContainerId } from '../utils'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import { rendererManager } from '../renderers'
import { DigitalHumanRenderer } from '../renderers/digital-human'
import { DOUBAO_VOICES } from '../constants/tts'
import { TtsServiceFactory } from '../services/tts'

// 配置存储的 key
const CONFIG_STORAGE_KEY = 'xmov_avatar_config'

// 编辑界面的数字人容器ID
const editContainerId = ref(generateContainerId())

// 注入全局状态和方法
const appState = inject<AppState>('appState')!
const appStore = inject<AppStore>('appStore')!

// 组件状态
const isSending = ref(false)
const showMenu = ref(false)
const showHistorySubmenu = ref(false)
const showHistoryPanel = ref(true)
const showBackgroundSubmenu = ref(false)
const showConversationModeSubmenu = ref(false)
const currentSpeaker = ref<'user' | 'partner'>('user') // 当前选择的说话人（演讲模式）
const historyPanelHeight = ref(400) // 默认高度400px
const isResizing = ref(false)
const playingMessageId = ref<number | null>(null) // 当前播放的消息ID
const editingMessageId = ref<number | null>(null) // 当前编辑的消息ID
const editingContent = ref<string>('') // 编辑中的内容
const showTtsAsrSettingsModal = ref(false)
const showMofaInviteCodeModal = ref(false) // 魔珐数字人邀请码模态框
const showRoleManagementModal = ref(false)
const showUserRoleManagementModal = ref(false)
const showApiKeyLoginModal = ref(false)
const activeTtsAsrTab = ref<'tts' | 'asr'>('tts')
const roles = ref<Role[]>([])
const showRoleEditForm = ref(false)
const editingRole = ref<Role | null>(null)
// 用户角色管理相关状态
const globalApiKey = ref<string>('') // 全局 apiKey（登录后设置）
const userRoles = ref<UserRole[]>([])
const showUserRoleEditForm = ref(false)
const editingUserRole = ref<UserRole | null>(null)
const backgrounds = ref<Background[]>([]) // 背景列表
const showBackgroundManagerModal = ref(false) // 背景管理器模态框
const autoExtractMarkdownImage = ref(true) // Markdown图像提取开关（默认开启）
const backgroundFileInputRef = ref<HTMLInputElement | null>(null) // 背景文件上传input引用
const userRoleForm = ref({
  user: '',
  name: '',
  type: 'illustration' as 'digital_human' | 'illustration',
  avatar: '',
  positionX: 20,
  positionY: 50,
  scale: 0.7,
  baseURL: '',
  model: '',
  avatarAppId: '',
  avatarAppSecret: '',
  useDigitalHumanVoice: true,
  ttsProvider: 'doubao',
  ttsVoice: '',
  ttsSpeed: 1.0,
  ttsVolume: 1.0,
  ttsPreviewText: '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
  enableVoicePlay: false,
  enableAutoPlay: false,
  enableAutoSwitch: false
})
// 编辑界面的用户角色数字人容器ID
const userRoleEditContainerId = ref(generateContainerId())
const showUserRoleApiKey = ref(false) // 用于显示/隐藏 apiKey（只读显示）

// 音色列表
const doubaoVoices = DOUBAO_VOICES
const showApiKeyLoginInput = ref(false) // 用于显示/隐藏登录输入框的 apiKey
// 使用全局状态，不再需要本地 ref
// const currentUserRole = ref<UserRole | null>(null) // 当前用户角色
const loginApiKeyInput = ref<string>('') // 登录输入的 apiKey
const userRoleAvatarFileInputRef = ref<HTMLInputElement | null>(null)
// 立绘显示状态（从 App.vue inject）
const showUserIllustration = inject<Ref<boolean>>('showUserIllustration')!
const showPartnerIllustration = inject<Ref<boolean>>('showPartnerIllustration')!
const roleForm = ref({
  name: '',
  user: '',
  type: 'illustration' as 'digital_human' | 'illustration',
  description: '',
  avatar: '',
  positionX: 80,
  positionY: 50,
  scale: 0.7,
  baseURL: '',
  model: '',
  apiKey: '',
  avatarAppId: '',
  avatarAppSecret: '',
  useDigitalHumanVoice: true,
  ttsProvider: 'doubao',
  ttsVoice: '',
  ttsSpeed: 1.0,
  ttsVolume: 1.0,
  ttsPreviewText: '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
  enableVoicePlay: false,
  enableAutoPlay: false,
  enableAutoSwitch: false
})
const avatarFileInputRef = ref<HTMLInputElement | null>(null)
const showCropModal = ref(false)
const cropImageSrc = ref('')
const cropImageRef = ref<HTMLImageElement | null>(null)
const cropperInstance = ref<Cropper | null>(null)
const pendingUploadFile = ref<File | null>(null)
const isUserRoleUpload = ref(false) // 标识当前上传是用户角色还是伙伴角色
const showTtsApiKey = ref(false)
const showAsrAppId = ref(false)
const showAsrSecretId = ref(false)
const showAsrSecretKey = ref(false)
const showAppSecret = ref(false)
const showRoleApiKey = ref(false) // 伙伴角色 API Key 显示/隐藏
// TTS设置页试听相关
const ttsPreviewVoice = ref<string>('')
const ttsPreviewText = ref<string>('欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。')
const ttsPreviewAudio = ref<HTMLAudioElement | null>(null) // TTS设置页试听音频
const isTtsPreviewPlaying = ref(false) // TTS设置页是否正在播放

// 角色试听相关
const partnerPreviewAudio = ref<HTMLAudioElement | null>(null) // 伙伴角色试听音频
const isPartnerPreviewPlaying = ref(false) // 伙伴角色是否正在播放
const userPreviewAudio = ref<HTMLAudioElement | null>(null) // 用户角色试听音频
const isUserPreviewPlaying = ref(false) // 用户角色是否正在播放
const textareaRef = ref<HTMLTextAreaElement | null>(null) // 输入框引用
const inputWrapperRef = ref<HTMLElement | null>(null) // 输入框容器引用
const menuPopupRef = ref<HTMLElement | null>(null) // 菜单弹出层引用
const historyListRef = ref<HTMLElement | null>(null) // 历史列表引用
const toastMessage = ref<string>('') // Toast 提示消息
const toastType = ref<'success' | 'error' | 'info'>('info') // Toast 类型
const showToast = ref(false) // 是否显示 Toast

// 显示 Toast 提示
function showToastMessage(message: string, type: 'success' | 'error' | 'info' = 'info') {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 2000) // 2秒后自动消失
}

// 加载对话历史
async function loadHistory() {
  if (!appState.llm.apiKey) {
    console.warn('API Key未配置，无法加载历史记录')
    appState.chatHistory = []
    return
  }
  
  // 如果当前伙伴角色为空，历史记录也为空
  if (!appState.llm.user) {
    appState.chatHistory = []
    return
  }
  
  try {
    // 确保伙伴角色列表已加载（用于显示头像）
    if (roles.value.length === 0) {
      await loadRoles()
    }
    
    // 验证当前伙伴角色是否存在
    const partnerRole = roles.value.find(r => r.user === appState.llm.user)
    if (!partnerRole) {
      console.warn('当前伙伴角色不存在, appState.llm.user:', appState.llm.user, '可用角色:', roles.value.map(r => r.user))
      appState.chatHistory = []
      return
    }
    
    // 只加载当前伙伴角色的历史记录
    const history = await getChatHistory(
      appState.llm.apiKey,
      appState.llm.user,
      100
    )
    appState.chatHistory = history || []
  } catch (error) {
    console.error('加载对话历史失败:', error)
    appState.chatHistory = []
  }
}

// ASR Hook - 使用computed确保配置更新时重新创建
const asrConfig = computed(() => ({
  provider: 'tx' as const,
  appId: appState.asr.appId,
  secretId: appState.asr.secretId,
  secretKey: appState.asr.secretKey
}))

// 初始化ASR hook（用于停止功能）
const { stop: stopAsr } = useAsr(asrConfig.value)

// Markdown渲染配置
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true, // GitHub风格Markdown
  headerIds: false,
  mangle: false
})

// 渲染Markdown为HTML
function renderMarkdown(content: string): string {
  if (!content) return ''
  try {
    // 如果启用了Markdown图像提取，提取markdown图片并设置背景
    if (autoExtractMarkdownImage.value) {
      const images = extractMarkdownImages(content)
      if (images.length > 0) {
        // 获取最后一个图像的地址作为背景
        const lastImage = images[images.length - 1]
        appState.ui.backgroundImage = lastImage.imageUrl
        
        // 从内容中移除所有图像标记
        content = removeMarkdownImages(content)
      }
    }
    
    const html = marked.parse(content)
    // 直接返回HTML，不进行过滤，以换取最佳用户体验
    return html
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return content
  }
}



// 组件卸载时清理裁剪器
onUnmounted(() => {
  if (cropperInstance.value) {
    cropperInstance.value.destroy()
    cropperInstance.value = null
  }
})

// 监听伙伴角色类型变化，自动更新播放语音勾选项
watch([() => roleForm.value.type, () => roleForm.value.useDigitalHumanVoice], ([newType, newUseDigitalHumanVoice], [oldType, oldUseDigitalHumanVoice]) => {
  // 只在值发生变化时才检测
  if (oldType !== undefined && oldUseDigitalHumanVoice !== undefined) {
    // 仅当角色是数字人且使用数字人自带的语音播放时设置为勾选
    roleForm.value.enableVoicePlay = newType === 'digital_human' && newUseDigitalHumanVoice === true
  }
})

// 监听用户角色类型变化，自动更新播放语音勾选项
watch([() => userRoleForm.value.type, () => userRoleForm.value.useDigitalHumanVoice], ([newType, newUseDigitalHumanVoice], [oldType, oldUseDigitalHumanVoice]) => {
  // 只在值发生变化时才检测
  if (oldType !== undefined && oldUseDigitalHumanVoice !== undefined) {
    // 仅当角色是数字人且使用数字人自带的语音播放时设置为勾选
    userRoleForm.value.enableVoicePlay = newType === 'digital_human' && newUseDigitalHumanVoice === true
  }
})

// 监听对话历史变化，自动滚动到底部
watch(() => appState.chatHistory.length, (newLength, oldLength) => {
  nextTick(() => {
    if (historyListRef.value) {
      historyListRef.value.scrollTop = historyListRef.value.scrollHeight
    }
  })
  
  // 检查是否有新消息（长度增加）
  if (newLength > (oldLength || 0) && newLength > 0) {
    const newMessage = appState.chatHistory[newLength - 1]
    if (newMessage) {
      const role = newMessage.role === 'user' 
        ? appState.currentUserRole 
        : appState.currentPartnerRole
      
      if (role) {
        // 自动切换角色（如果启用）
        if (role.enableAutoSwitch) {
          switchRoleDisplay(newMessage.role as 'user' | 'assistant')
        }
        
        // 自动播放（如果启用且允许播放）
        if (role.enableAutoPlay && role.enableVoicePlay !== false) {
          playMessageAudio(newMessage, newLength - 1).catch(error => {
            console.error('自动播放失败:', error)
          })
        }
      }
    }
  }
}, { immediate: false })

// 监听自动切换角色事件（从 appStore.sendMessage 触发）
window.addEventListener('autoSwitchRole', ((event: CustomEvent<{ role: 'user' | 'assistant' }>) => {
  switchRoleDisplay(event.detail.role)
}) as EventListener)

// 监听自动播放消息事件（从 appStore.sendMessage 触发）
window.addEventListener('autoPlayMessage', ((event: CustomEvent<{ messageIndex: number }>) => {
  const message = appState.chatHistory[event.detail.messageIndex]
  if (message) {
    playMessageAudio(message, event.detail.messageIndex).catch(error => {
      console.error('自动播放失败:', error)
    })
  }
}) as EventListener)

// 判断消息是否可以播放语音
function canPlayMessage(message: ChatMessage): boolean {
  const role = message.role === 'user' 
    ? appState.currentUserRole 
    : appState.currentPartnerRole
  
  if (!role) {
    return false
  }
  
  // 检查是否启用语音播放
  if (role.enableVoicePlay === false) {
    return false
  }
  
  // 数字人类型
  if (role.type === 'digital_human') {
    // 如果使用数字人语音，需要连接状态
    if (role.useDigitalHumanVoice === true) {
      return role.isConnected === true && role.digitalHumanInstance !== null
    }
    // 如果使用TTS语音，需要TTS配置（和立绘类型一样）
    else {
      const hasTtsConfig = !!(role.ttsVoice && appState.tts.apiKey) || 
                           !!(appState.tts.apiKey && role.ttsProvider)
      return hasTtsConfig
    }
  }
  
  // 立绘类型：需要配置TTS（有音色配置或全局TTS配置）
  if (role.type === 'illustration') {
    // 检查是否有TTS配置（角色配置或全局配置）
    const hasTtsConfig = !!(role.ttsVoice && appState.tts.apiKey) || 
                         !!(appState.tts.apiKey && role.ttsProvider)
    return hasTtsConfig
  }
  
  return false
}

// 播放/停止消息音频
async function toggleMessageAudio(message: ChatMessage, index: number) {
  // 如果正在播放当前消息，则停止
  if (playingMessageId.value === index) {
    stopMessageAudio()
    return
  }
  
  // 如果正在播放其他消息，先停止
  if (playingMessageId.value !== null) {
    stopMessageAudio()
    await delay(300)
  }
  
  // 播放当前消息
  await playMessageAudio(message, index)
}

// 当前播放的音频对象
let currentAudio: HTMLAudioElement | null = null
// 当前播放的角色实例（用于数字人停止）
let currentPlayingRole: (Role | UserRole) | null = null

// 播放消息音频
async function playMessageAudio(message: ChatMessage, index: number) {
  // 判断消息角色
  const role = message.role === 'user' 
    ? appState.currentUserRole 
    : appState.currentPartnerRole
  
  if (!role) {
    showToastMessage('角色不存在', 'error')
    return
  }
  
  // 检查是否启用语音播放
  if (role.enableVoicePlay === false) {
    console.log('角色已禁用语音播放，跳过播放')
    return
  }
  
  // 检查消息内容
  if (!message.content || message.content.trim() === '') {
    console.warn('消息内容为空，无法播放')
    showToastMessage('消息内容为空', 'error')
    return
  }
  
  // 自动切换角色（如果启用）
  if (role.enableAutoSwitch) {
    await switchRoleDisplay(message.role as 'user' | 'assistant')
  }
  
  // 处理消息内容：清理所有markdown语法
  let content = message.content
  // 使用 remove-markdown 清理所有 markdown 语法，获取纯文本用于 TTS
  content = removeMarkdown(content)
  
  // 如果内容为空，提示用户
  if (!content || content.trim() === '') {
    console.warn('处理后的消息内容为空')
    showToastMessage('消息内容为空，无法播放', 'error')
    return
  }
  
  try {
    // 根据角色类型选择TTS引擎
    if (role.type === 'digital_human') {
      // 数字人：根据语音选项选择播放方式
      if (role.useDigitalHumanVoice === true) {
        // 使用数字人SDK的TTS：需要连接
        if (!role.isConnected || !role.digitalHumanInstance) {
          showToastMessage('数字人未连接，请先连接数字人', 'error')
          return
        }
        
        // 如果正在说话，先停止
        if (avatarState.value === 'speak' && role.digitalHumanInstance) {
          role.digitalHumanInstance.think()
          await delay(500) // 等待停止完成
        }
        
        // 设置播放状态
        playingMessageId.value = index
        currentPlayingRole = role // 记录当前播放的角色
        
        // 生成 SSML 格式文本
        const ssml = generateSSML(content.trim())
        console.log('生成的 SSML:', ssml)
        
        // 调用数字人 SDK 的 speak 方法
        console.log('调用 speak 方法...')
        role.digitalHumanInstance.speak(ssml, true, true)
        console.log('speak 方法调用完成')
        
        // 监听数字人状态变化，当停止说话时清除播放状态
        const stopWatcher = watch(() => avatarState.value, (newState) => {
          console.log('数字人状态变化:', newState)
          if (newState !== 'speak' && playingMessageId.value === index) {
            console.log('数字人停止说话，清除播放状态')
            playingMessageId.value = null
            currentPlayingRole = null // 清除当前播放角色
            stopWatcher() // 停止监听
          }
        })
        
        // 设置超时，防止状态监听失效
        setTimeout(() => {
          if (playingMessageId.value === index) {
            console.log('播放超时，清除播放状态')
            playingMessageId.value = null
            currentPlayingRole = null // 清除当前播放角色
            stopWatcher()
          }
        }, 60000) // 60秒超时
      } else {
        // 使用TTS语音：不需要连接，使用TTS播放逻辑（和立绘一样）
        if (!appState.tts.apiKey) {
          showToastMessage('请先在TTS设置中配置API Key', 'error')
          return
        }
        
        // 停止当前播放的音频
        if (currentAudio) {
          currentAudio.pause()
          currentAudio = null
        }
        
        // 获取角色TTS配置（使用角色配置或全局配置作为默认值）
        const ttsConfig = {
          provider: role.ttsProvider || appState.tts.provider || 'doubao',
          apiKey: appState.tts.apiKey,
          voice: role.ttsVoice || 'BV700_streaming', // 默认音色（灿灿）
          speed: role.ttsSpeed ?? appState.tts.speed ?? 1.0,
          volume: role.ttsVolume ?? appState.tts.volume ?? 1.0
        }
        
        // 确认使用对应角色的设置
        console.log('使用角色TTS配置:', {
          角色: role.name || role.user,
          角色类型: role.type,
          消息角色: message.role,
          音色: ttsConfig.voice,
          语速: ttsConfig.speed,
          音量: ttsConfig.volume,
          角色音色配置: role.ttsVoice || '(使用默认)',
          角色语速配置: role.ttsSpeed !== undefined ? role.ttsSpeed : '(使用全局)',
          角色音量配置: role.ttsVolume !== undefined ? role.ttsVolume : '(使用全局)'
        })
        
        // 调用TTS服务
        const ttsService = TtsServiceFactory.create(ttsConfig.provider)
        const audioData = await ttsService.synthesize(content.trim(), ttsConfig)
        
        // 播放音频
        await playAudio(audioData, index, ttsConfig.volume)
      }
    } else if (role.type === 'illustration') {
      // 立绘：使用豆包TTS
      if (!appState.tts.apiKey) {
        showToastMessage('请先在TTS设置中配置API Key', 'error')
        return
      }
      
      // 停止当前播放的音频
      if (currentAudio) {
        currentAudio.pause()
        currentAudio = null
      }
      
      // 获取角色TTS配置（使用角色配置或全局配置作为默认值）
      const ttsConfig = {
        provider: role.ttsProvider || appState.tts.provider || 'doubao',
        apiKey: appState.tts.apiKey,
        voice: role.ttsVoice || 'BV700_streaming', // 默认音色（灿灿）
        speed: role.ttsSpeed ?? appState.tts.speed ?? 1.0,
        volume: role.ttsVolume ?? appState.tts.volume ?? 1.0
      }
      
      // 确认使用对应角色的设置
      console.log('使用角色TTS配置:', {
        角色: role.name || role.user,
        角色类型: role.type,
        消息角色: message.role,
        音色: ttsConfig.voice,
        语速: ttsConfig.speed,
        音量: ttsConfig.volume,
        角色音色配置: role.ttsVoice || '(使用默认)',
        角色语速配置: role.ttsSpeed !== undefined ? role.ttsSpeed : '(使用全局)',
        角色音量配置: role.ttsVolume !== undefined ? role.ttsVolume : '(使用全局)'
      })
      
      // 调用TTS服务
      const ttsService = TtsServiceFactory.create(ttsConfig.provider)
      const audioData = await ttsService.synthesize(content.trim(), ttsConfig)
      
      // 播放音频
      await playAudio(audioData, index, ttsConfig.volume)
    } else {
      showToastMessage('未知的角色类型', 'error')
      return
    }
  } catch (error) {
    console.error('播放音频失败:', error)
    playingMessageId.value = null
    showToastMessage('播放音频失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
  }
}

// 播放音频（用于立绘TTS）
async function playAudio(audioData: ArrayBuffer, messageIndex: number, volume?: number) {
  // 停止当前播放
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  
  // 创建音频对象
  const blob = new Blob([audioData], { type: 'audio/mpeg' })
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  
  // 设置音量（如果提供）
  if (volume !== undefined) {
    audio.volume = volume
  }
  
  // 设置播放状态
  playingMessageId.value = messageIndex
  currentAudio = audio
  
  // 播放完成处理
  audio.onended = () => {
    playingMessageId.value = null
    URL.revokeObjectURL(url)
    currentAudio = null
  }
  
  // 播放错误处理
  audio.onerror = () => {
    playingMessageId.value = null
    URL.revokeObjectURL(url)
    currentAudio = null
    showToastMessage('音频播放失败', 'error')
  }
  
  // 开始播放
  try {
    await audio.play()
  } catch (error) {
    console.error('播放音频失败:', error)
    playingMessageId.value = null
    URL.revokeObjectURL(url)
    currentAudio = null
    showToastMessage('音频播放失败', 'error')
  }
}

// 停止消息音频
function stopMessageAudio() {
  // 停止数字人音频（优先停止当前播放的角色）
  if (currentPlayingRole && currentPlayingRole.digitalHumanInstance) {
    try {
      currentPlayingRole.digitalHumanInstance.think()
      console.log('已停止当前播放的数字人')
      currentPlayingRole = null
    } catch (error) {
      console.error('停止数字人音频失败:', error)
      // 如果失败，尝试停止所有数字人
      if (appState.currentUserRole?.digitalHumanInstance && avatarState.value === 'speak') {
        try {
          appState.currentUserRole.digitalHumanInstance.think()
        } catch (e) {
          console.error('停止用户角色数字人失败:', e)
        }
      }
      if (appState.currentPartnerRole?.digitalHumanInstance && avatarState.value === 'speak') {
        try {
          appState.currentPartnerRole.digitalHumanInstance.think()
        } catch (e) {
          console.error('停止伙伴角色数字人失败:', e)
        }
      }
    }
  } else if (avatarState.value === 'speak') {
    // 如果没有记录当前播放角色，但状态显示正在说话，尝试停止所有数字人
    if (appState.currentUserRole?.digitalHumanInstance) {
      try {
        appState.currentUserRole.digitalHumanInstance.think()
        console.log('已停止用户角色数字人播放')
      } catch (error) {
        console.error('停止用户角色数字人音频失败:', error)
      }
    }
    if (appState.currentPartnerRole?.digitalHumanInstance) {
      try {
        appState.currentPartnerRole.digitalHumanInstance.think()
        console.log('已停止伙伴角色数字人播放')
      } catch (error) {
        console.error('停止伙伴角色数字人音频失败:', error)
      }
    }
  }
  
  // 停止立绘音频
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0 // 重置播放位置
    currentAudio = null
  }
  
  playingMessageId.value = null
}

// 试听伙伴角色音色（toggle播放/停止）
async function previewPartnerVoice() {
  // 如果正在播放，则停止
  if (isPartnerPreviewPlaying.value && partnerPreviewAudio.value) {
    partnerPreviewAudio.value.pause()
    partnerPreviewAudio.value = null
    isPartnerPreviewPlaying.value = false
    return
  }
  
  if (!appState.tts.apiKey) {
    showToastMessage('请先在TTS设置中配置API Key', 'error')
    return
  }
  
  if (!roleForm.value.ttsVoice) {
    showToastMessage('请先选择音色', 'error')
    return
  }
  
  const previewText = roleForm.value.ttsPreviewText?.trim() || 'AI小世界简介'
  if (!previewText) {
    showToastMessage('请输入试听文本', 'error')
    return
  }
  
  try {
    const ttsConfig = {
      provider: roleForm.value.ttsProvider || 'doubao',
      apiKey: appState.tts.apiKey,
      voice: roleForm.value.ttsVoice,
      speed: roleForm.value.ttsSpeed ?? appState.tts.speed ?? 1.0,
      volume: roleForm.value.ttsVolume ?? appState.tts.volume ?? 1.0
    }
    
    const ttsService = TtsServiceFactory.create(ttsConfig.provider)
    const audioData = await ttsService.synthesize(previewText, ttsConfig)
    
    // 播放试听音频
    const blob = new Blob([audioData], { type: 'audio/mpeg' })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    partnerPreviewAudio.value = audio
    
    // 设置播放完成和错误处理
    audio.onended = () => {
      URL.revokeObjectURL(url)
      partnerPreviewAudio.value = null
      isPartnerPreviewPlaying.value = false
    }
    
    audio.onerror = (error) => {
      console.error('试听音频播放失败:', error)
      URL.revokeObjectURL(url)
      partnerPreviewAudio.value = null
      isPartnerPreviewPlaying.value = false
      showToastMessage('音频播放失败', 'error')
    }
    
    // 开始播放
    try {
      await audio.play()
      isPartnerPreviewPlaying.value = true
    } catch (error) {
      console.error('试听播放失败:', error)
      URL.revokeObjectURL(url)
      partnerPreviewAudio.value = null
      isPartnerPreviewPlaying.value = false
      showToastMessage('播放失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
    }
  } catch (error) {
    console.error('试听失败:', error)
    showToastMessage('试听失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
  }
}

// 试听用户角色音色（toggle播放/停止）
async function previewUserVoice() {
  // 如果正在播放，则停止
  if (isUserPreviewPlaying.value && userPreviewAudio.value) {
    userPreviewAudio.value.pause()
    userPreviewAudio.value = null
    isUserPreviewPlaying.value = false
    return
  }
  
  if (!appState.tts.apiKey) {
    showToastMessage('请先在TTS设置中配置API Key', 'error')
    return
  }
  
  if (!userRoleForm.value.ttsVoice) {
    showToastMessage('请先选择音色', 'error')
    return
  }
  
  const previewText = userRoleForm.value.ttsPreviewText?.trim() || 'AI小世界简介'
  if (!previewText) {
    showToastMessage('请输入试听文本', 'error')
    return
  }
  
  try {
    const ttsConfig = {
      provider: userRoleForm.value.ttsProvider || 'doubao',
      apiKey: appState.tts.apiKey,
      voice: userRoleForm.value.ttsVoice,
      speed: userRoleForm.value.ttsSpeed ?? appState.tts.speed ?? 1.0,
      volume: userRoleForm.value.ttsVolume ?? appState.tts.volume ?? 1.0
    }
    
    const ttsService = TtsServiceFactory.create(ttsConfig.provider)
    const audioData = await ttsService.synthesize(previewText, ttsConfig)
    
    // 播放试听音频
    const blob = new Blob([audioData], { type: 'audio/mpeg' })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    userPreviewAudio.value = audio
    
    // 设置播放完成和错误处理
    audio.onended = () => {
      URL.revokeObjectURL(url)
      userPreviewAudio.value = null
      isUserPreviewPlaying.value = false
    }
    
    audio.onerror = (error) => {
      console.error('试听音频播放失败:', error)
      URL.revokeObjectURL(url)
      userPreviewAudio.value = null
      isUserPreviewPlaying.value = false
      showToastMessage('音频播放失败', 'error')
    }
    
    // 开始播放
    try {
      await audio.play()
      isUserPreviewPlaying.value = true
    } catch (error) {
      console.error('试听播放失败:', error)
      URL.revokeObjectURL(url)
      userPreviewAudio.value = null
      isUserPreviewPlaying.value = false
      showToastMessage('播放失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
    }
  } catch (error) {
    console.error('试听失败:', error)
    showToastMessage('试听失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
  }
}

// 复制消息内容
async function copyMessage(content: string) {
  try {
    // 复制到剪贴板
    await navigator.clipboard.writeText(content.trim())
    showToastMessage('已复制到剪贴板', 'success')
  } catch (error) {
    console.error('复制失败:', error)
    // 降级方案：使用传统方法
    const textarea = document.createElement('textarea')
    textarea.value = content
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      showToastMessage('已复制到剪贴板', 'success')
    } catch (err) {
      showToastMessage('复制失败', 'error')
    }
    document.body.removeChild(textarea)
  }
}

// 编辑消息
function editMessage(message: ChatMessage, index: number) {
  editingMessageId.value = index
  editingContent.value = message.content
}

// 保存编辑
async function saveEdit(index: number) {
  if (editingContent.value.trim() === '') {
    showToastMessage('内容不能为空', 'error')
    return
  }
  
  const message = appState.chatHistory[index]
  if (!message) {
    showToastMessage('消息不存在', 'error')
    return
  }
  
  try {
    // 如果有ID，调用更新API
    if ((message as any).id) {
      await updateChatMessage((message as any).id, editingContent.value.trim())
    }
    
    // 更新本地状态
    message.content = editingContent.value.trim()
    
    // 取消编辑状态
    cancelEdit()
    showToastMessage('消息已更新', 'success')
  } catch (error) {
    console.error('更新消息失败:', error)
    showToastMessage('更新消息失败', 'error')
  }
}

// 取消编辑
function cancelEdit() {
  editingMessageId.value = null
  editingContent.value = ''
}

// 删除消息
async function deleteMessageItem(message: ChatMessage, index: number) {
  if (!confirm('确定要删除这条消息吗？')) {
    return
  }
  
  try {
    // 如果有ID，调用删除API删除数据库中的消息
    if ((message as any).id) {
      // 统一使用伙伴角色的user字段（与AI模式保持一致，数据记录以伙伴为准）
      const partnerUser = appState.currentPartnerRole?.user || appState.llm.user || ''
      const apiKey = globalApiKey.value || ''
      
      if (!partnerUser || !apiKey) {
        throw new Error('伙伴角色user字段或API Key为空')
      }
      
      await deleteChatMessage((message as any).id, apiKey, partnerUser)
    }
    
    // 从本地状态中删除
    appState.chatHistory.splice(index, 1)
    showToastMessage('消息已删除', 'success')
  } catch (error) {
    console.error('删除消息失败:', error)
    showToastMessage('删除消息失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
  }
}

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
// 用户角色编辑表单中的连接函数
async function handleConnectUserRole() {
  // 检查是否在编辑表单中
  if (!showUserRoleEditForm.value) {
    showToastMessage('请先打开角色编辑表单', 'error')
    return
  }
  // 如果是编辑已有角色，检查连接状态
  if (editingUserRole.value?.isConnecting) return
  
  // 检查SDK是否已加载
  if (!window.XmovAvatar) {
    showToastMessage('SDK未加载，请刷新页面重试', 'error')
    return
  }
  
  // 检查是否在编辑用户角色数字人
  if (!showUserRoleEditForm.value || userRoleForm.value.type !== 'digital_human') {
    showToastMessage('连接失败：当前不在编辑用户角色数字人', 'error')
    return
  }
  
  // 检查容器是否存在
  const containerId = userRoleEditContainerId.value
  const container = document.getElementById(containerId)
  if (!container) {
    showToastMessage(`容器不存在: #${containerId}，请确保数字人角色已创建`, 'error')
    return
  }
  
  // 检查角色是否配置了 appId 和 appSecret
  if (!userRoleForm.value.avatarAppId || !userRoleForm.value.avatarAppSecret) {
    showToastMessage('请先配置数字人的 App ID 和 App Secret', 'error')
    return
  }
  
  // 如果是创建新角色，创建一个临时的连接状态
  if (!editingUserRole.value) {
    editingUserRole.value = {
      id: 0,
      user: userRoleForm.value.user || '',
      name: userRoleForm.value.name || '',
      type: userRoleForm.value.type,
      avatar: userRoleForm.value.avatar || '',
      positionX: userRoleForm.value.positionX,
      positionY: userRoleForm.value.positionY,
      scale: userRoleForm.value.scale,
      baseURL: userRoleForm.value.baseURL || '',
      model: userRoleForm.value.model || '',
      apiKey: globalApiKey.value || '',
      avatarAppId: userRoleForm.value.avatarAppId || '',
      avatarAppSecret: userRoleForm.value.avatarAppSecret || '',
      useDigitalHumanVoice: userRoleForm.value.useDigitalHumanVoice !== undefined ? userRoleForm.value.useDigitalHumanVoice : true,
      ttsProvider: userRoleForm.value.ttsProvider || 'doubao',
      ttsVoice: userRoleForm.value.ttsVoice || '',
      ttsSpeed: userRoleForm.value.ttsSpeed || 1.0,
      ttsVolume: userRoleForm.value.ttsVolume || 1.0,
      ttsPreviewText: userRoleForm.value.ttsPreviewText || '',
      enableVoicePlay: userRoleForm.value.enableVoicePlay !== undefined ? userRoleForm.value.enableVoicePlay : false,
      enableAutoPlay: userRoleForm.value.enableAutoPlay !== undefined ? userRoleForm.value.enableAutoPlay : false,
      enableAutoSwitch: userRoleForm.value.enableAutoSwitch !== undefined ? userRoleForm.value.enableAutoSwitch : false,
      isCurrent: false,
      isConnecting: false,
      isConnected: false,
      showDigitalHuman: false,
      digitalHumanInstance: null
    } as UserRole
  }
  
  editingUserRole.value.isConnecting = true
  try {
    const avatar = await avatarService.connect(
      {
        appId: userRoleForm.value.avatarAppId,
        appSecret: userRoleForm.value.avatarAppSecret
      },
      {
        onSubtitleOn: (text: string) => {
          appState.ui.subTitleText = text
        },
        onSubtitleOff: () => {
          appState.ui.subTitleText = ''
        },
        onStateChange: (state: string) => {
          avatarState.value = state
        }
      },
      userRoleEditContainerId.value
    )
    // 保存实例到角色对象（如果正在编辑已有角色）
    if (editingUserRole.value) {
      editingUserRole.value.digitalHumanInstance = avatar
      editingUserRole.value.isConnected = true
    }
    // 注意：编辑界面中的连接是临时连接，用于测试，不保存到角色列表
    
    showToastMessage('连接成功', 'success')
  } catch (error) {
    console.error('连接失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    showToastMessage(`连接失败: ${errorMessage}`, 'error')
  } finally {
    if (editingUserRole.value) {
      editingUserRole.value.isConnecting = false
    }
  }
}

// 伙伴角色编辑表单中的连接函数
async function handleConnectPartnerRole() {
  // 检查是否在编辑表单中
  if (!showRoleEditForm.value) {
    showToastMessage('请先打开角色编辑表单', 'error')
    return
  }
  // 如果是编辑已有角色，检查连接状态
  if (editingRole.value?.isConnecting) return
  
  // 检查SDK是否已加载
  if (!window.XmovAvatar) {
    showToastMessage('SDK未加载，请刷新页面重试', 'error')
    return
  }
  
  // 检查是否在编辑伙伴角色数字人
  if (!showRoleEditForm.value || roleForm.value.type !== 'digital_human') {
    showToastMessage('连接失败：当前不在编辑伙伴角色数字人', 'error')
    return
  }
  
  // 检查容器是否存在
  const containerId = editContainerId.value
  const container = document.getElementById(containerId)
  if (!container) {
    showToastMessage(`容器不存在: #${containerId}，请确保数字人角色已创建`, 'error')
    return
  }
  
  // 检查角色是否配置了 appId 和 appSecret
  if (!roleForm.value.avatarAppId || !roleForm.value.avatarAppSecret) {
    showToastMessage('请先配置数字人的 App ID 和 App Secret', 'error')
    return
  }
  
  // 如果是创建新角色，创建一个临时的连接状态
  if (!editingRole.value) {
    editingRole.value = {
      id: 0,
      name: roleForm.value.name || '',
      user: roleForm.value.user || '',
      type: roleForm.value.type,
      description: roleForm.value.description || '',
      avatar: roleForm.value.avatar || '',
      positionX: roleForm.value.positionX,
      positionY: roleForm.value.positionY,
      scale: roleForm.value.scale,
      baseURL: roleForm.value.baseURL || '',
      model: roleForm.value.model || '',
      apiKey: globalApiKey.value || '',
      avatarAppId: roleForm.value.avatarAppId || '',
      avatarAppSecret: roleForm.value.avatarAppSecret || '',
      useDigitalHumanVoice: roleForm.value.useDigitalHumanVoice !== undefined ? roleForm.value.useDigitalHumanVoice : true,
      ttsProvider: roleForm.value.ttsProvider || 'doubao',
      ttsVoice: roleForm.value.ttsVoice || '',
      ttsSpeed: roleForm.value.ttsSpeed || 1.0,
      ttsVolume: roleForm.value.ttsVolume || 1.0,
      enableVoicePlay: roleForm.value.enableVoicePlay !== undefined ? roleForm.value.enableVoicePlay : false,
      enableAutoPlay: roleForm.value.enableAutoPlay !== undefined ? roleForm.value.enableAutoPlay : false,
      enableAutoSwitch: roleForm.value.enableAutoSwitch !== undefined ? roleForm.value.enableAutoSwitch : false,
      isConnecting: false,
      isConnected: false,
      showDigitalHuman: false,
      digitalHumanInstance: null
    } as Role
  }
  
  editingRole.value.isConnecting = true
  try {
    const avatar = await avatarService.connect(
      {
        appId: roleForm.value.avatarAppId,
        appSecret: roleForm.value.avatarAppSecret
      },
      {
        onSubtitleOn: (text: string) => {
          appState.ui.subTitleText = text
        },
        onSubtitleOff: () => {
          appState.ui.subTitleText = ''
        },
        onStateChange: (state: string) => {
          avatarState.value = state
        }
      },
      editContainerId.value
    )
    // 保存实例到角色对象（如果正在编辑已有角色）
    if (editingRole.value) {
      editingRole.value.digitalHumanInstance = avatar
      editingRole.value.isConnected = true
    }
    // 注意：编辑界面中的连接是临时连接，用于测试，不保存到角色列表
    
    showToastMessage('连接成功', 'success')
  } catch (error) {
    console.error('连接失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    showToastMessage(`连接失败: ${errorMessage}`, 'error')
  } finally {
    if (editingRole.value) {
      editingRole.value.isConnecting = false
    }
  }
}

function handleDisconnect() {
  try {
    // 根据编辑中的角色类型断开连接
    if (showUserRoleEditForm.value && editingUserRole.value) {
      // 编辑面板中的连接是临时连接，直接断开 digitalHumanInstance
      if (editingUserRole.value.digitalHumanInstance) {
        avatarService.disconnect(editingUserRole.value.digitalHumanInstance)
        editingUserRole.value.digitalHumanInstance = null
        editingUserRole.value.isConnected = false
        editingUserRole.value.isConnecting = false
        showToastMessage('已断开连接', 'success')
      } else {
        showToastMessage('该角色未连接', 'info')
      }
    } else if (showRoleEditForm.value && editingRole.value) {
      // 编辑面板中的连接是临时连接，直接断开 digitalHumanInstance
      if (editingRole.value.digitalHumanInstance) {
        avatarService.disconnect(editingRole.value.digitalHumanInstance)
        editingRole.value.digitalHumanInstance = null
        editingRole.value.isConnected = false
        editingRole.value.isConnecting = false
        showToastMessage('已断开连接', 'success')
      } else {
        showToastMessage('该角色未连接', 'info')
      }
    } else {
      showToastMessage('请先选择要断开的角色', 'error')
    }
  } catch (error) {
    console.error('断开连接失败:', error)
    showToastMessage('断开连接失败', 'error')
  }
}

// 从角色列表连接伙伴角色数字人
async function handleConnectRoleFromList(role: Role) {
  if (role.isConnecting) return
  
  // 检查SDK是否已加载
  if (!window.XmovAvatar) {
    showToastMessage('SDK未加载，请刷新页面重试', 'error')
    return
  }
  
  // 检查角色是否配置了 appId 和 appSecret
  if (!role.avatarAppId || !role.avatarAppSecret) {
    showToastMessage('请先配置数字人的 App ID 和 App Secret', 'error')
    return
  }
  
  // 检查该角色是否已连接
  if (role.isConnected) {
    showToastMessage('该角色已连接', 'info')
    return
  }
  
  // 检查 appState.currentPartnerRole 是否与传入的 role 一致（数据同步检查）
  if (!appState.currentPartnerRole || appState.currentPartnerRole.user !== role.user) {
    showToastMessage('当前角色数据不同步，请刷新页面重试', 'error')
    return
  }
  
  // 检查当前角色类型是否为数字人
  if (appState.currentPartnerRole.type !== 'digital_human') {
    showToastMessage('当前角色类型不是数字人', 'error')
    return
  }
  
  const partnerRoleId = `partner:${role.user}`
  // 获取或创建渲染器
  role.isConnecting = true
  try {
    // 先设置显示状态，确保容器出现在DOM中
    role.showDigitalHuman = true
      // 等待Vue更新DOM
      await nextTick()
      
      let renderer = rendererManager.getRenderer(partnerRoleId)
      if (!renderer) {
        // 创建渲染器
        const containerId = 'digital-human-partner' // 固定容器ID
        console.log('[伙伴角色连接] 创建渲染器, roleId:', partnerRoleId, 'containerId:', containerId, 'role.user:', role.user)
        renderer = await rendererManager.createRenderer(partnerRoleId, {
          roleId: partnerRoleId,
          roleType: 'digital_human',
          positionX: role.positionX !== undefined ? role.positionX : 80,
          positionY: role.positionY !== undefined ? role.positionY : 50,
          scale: role.scale !== undefined ? role.scale : (role.type === 'illustration' ? 0.7 : 1.0),
          avatarAppId: role.avatarAppId,
          avatarAppSecret: role.avatarAppSecret,
          containerId: containerId
        })
      } else {
        console.log('[伙伴角色连接] 使用已有渲染器, roleId:', partnerRoleId)
      }
      
      // 检查容器是否存在（使用固定ID）
      const containerId = 'digital-human-partner'
      const containerElement = document.getElementById(containerId)
      console.log('[伙伴角色连接] 查找容器, containerId:', containerId, '找到容器:', !!containerElement)
      if (!containerElement) {
        showToastMessage('数字人容器不存在，请确保当前角色是数字人类型', 'error')
        role.showDigitalHuman = false
        role.isConnecting = false
        return
      }
      console.log('[伙伴角色连接] 容器元素ID:', containerElement.id, '容器元素:', containerElement)
    
    // 设置回调函数
    if (renderer instanceof DigitalHumanRenderer) {
      renderer.setCallbacks({
        onSubtitleOn: (text: string) => {
          appState.ui.subTitleText = text
        },
        onSubtitleOff: () => {
          appState.ui.subTitleText = ''
        },
        onStateChange: (state: string) => {
          avatarState.value = state
        }
      })
    }
    
    // 连接SDK（先调用render设置容器，再调用connect连接）
    if (renderer.connect) {
      console.log('[伙伴角色连接] 调用 render, containerElement.id:', containerElement.id)
      // 先调用render设置容器
      await renderer.render(containerElement)
      console.log('[伙伴角色连接] 调用 connect')
      // 再调用connect连接SDK
      await renderer.connect()
      
      if (renderer instanceof DigitalHumanRenderer) {
        const instance = renderer.getInstance()
        if (instance) {
          role.digitalHumanInstance = instance
        }
      }
      role.isConnected = true
      
      // 显示状态已在连接前设置，这里不需要再次设置
      
      showToastMessage('连接成功', 'success')
    } else {
      showToastMessage('渲染器不支持连接操作', 'error')
      // 回滚状态
      role.showDigitalHuman = false
      role.isConnecting = false
    }
  } catch (error) {
    console.error('连接失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    showToastMessage(`连接失败: ${errorMessage}`, 'error')
    // 回滚状态
    role.isConnecting = false
    role.showDigitalHuman = false
  }
}

// 从角色列表断开伙伴角色数字人
async function handleDisconnectRoleFromList(role: Role) {
  const partnerRoleId = `partner:${role.user}`
  const renderer = rendererManager.getRenderer(partnerRoleId)
  
  if (!renderer) {
    showToastMessage('该角色未连接', 'info')
    return
  }
  
  try {
    // 断开连接
    if (renderer.disconnect) {
      await renderer.disconnect()
    }
    
    // 隐藏数字人
    renderer.hide()
    
    // 清理角色对象上的状态
    role.showDigitalHuman = false
    role.digitalHumanInstance = null
    role.isConnected = false
    role.isConnecting = false
    
    // 销毁渲染器（可选，也可以保留以便后续重新连接）
    // rendererManager.destroyRenderer(partnerRoleId)
    
    showToastMessage('已断开连接', 'success')
  } catch (error) {
    console.error('断开连接失败:', error)
    showToastMessage('断开连接失败', 'error')
  }
}

// 从角色列表连接用户角色数字人
async function handleConnectUserRoleFromList(role: UserRole) {
  if (role.isConnecting) return
  
  // 检查SDK是否已加载
  if (!window.XmovAvatar) {
    showToastMessage('SDK未加载，请刷新页面重试', 'error')
    return
  }
  
  // 检查角色是否配置了 appId 和 appSecret
  if (!role.avatarAppId || !role.avatarAppSecret) {
    showToastMessage('请先配置数字人的 App ID 和 App Secret', 'error')
    return
  }
  
  // 检查该角色是否已连接
  if (role.isConnected) {
    showToastMessage('该角色已连接', 'info')
    return
  }
  
  // 检查 appState.currentUserRole 是否与传入的 role 一致（数据同步检查）
  if (!appState.currentUserRole || appState.currentUserRole.id !== role.id) {
    showToastMessage('当前角色数据不同步，请刷新页面重试', 'error')
    return
  }
  
  // 检查当前角色类型是否为数字人
  if (appState.currentUserRole.type !== 'digital_human') {
    showToastMessage('当前角色类型不是数字人', 'error')
    return
  }
  
  const userRoleId = `user:${role.id}`
  // 获取或创建渲染器
  role.isConnecting = true
  // 同步更新 appState.currentUserRole 的状态
  if (appState.currentUserRole) {
    appState.currentUserRole.isConnecting = true
  }
  try {
    // 先设置显示状态，确保容器出现在DOM中
    role.showDigitalHuman = true
    // 同步更新 appState.currentUserRole 的显示状态
    if (appState.currentUserRole) {
      appState.currentUserRole.showDigitalHuman = true
    }
      // 等待Vue更新DOM
      await nextTick()
      
      let renderer = rendererManager.getRenderer(userRoleId)
      if (!renderer) {
        // 创建渲染器
        const containerId = 'digital-human-user' // 固定容器ID
        console.log('[用户角色连接] 创建渲染器, roleId:', userRoleId, 'containerId:', containerId, 'role.id:', role.id)
        renderer = await rendererManager.createRenderer(userRoleId, {
          roleId: userRoleId,
          roleType: 'digital_human',
          positionX: role.positionX !== undefined ? role.positionX : 20,
          positionY: role.positionY !== undefined ? role.positionY : 50,
          scale: role.scale !== undefined ? role.scale : (role.type === 'illustration' ? 0.7 : 1.0),
          avatarAppId: role.avatarAppId,
          avatarAppSecret: role.avatarAppSecret,
          containerId: containerId
        })
      } else {
        console.log('[用户角色连接] 使用已有渲染器, roleId:', userRoleId)
      }
      
      // 检查容器是否存在（使用固定ID）
      const containerId = 'digital-human-user'
      const containerElement = document.getElementById(containerId)
      console.log('[用户角色连接] 查找容器, containerId:', containerId, '找到容器:', !!containerElement)
      if (!containerElement) {
        showToastMessage('数字人容器不存在，请确保当前角色是数字人类型', 'error')
        role.showDigitalHuman = false
        role.isConnecting = false
        // 同步回滚 appState.currentUserRole 的状态
        if (appState.currentUserRole) {
          appState.currentUserRole.showDigitalHuman = false
          appState.currentUserRole.isConnecting = false
        }
        return
      }
      console.log('[用户角色连接] 容器元素ID:', containerElement.id, '容器元素:', containerElement)
    
    // 设置回调函数
    if (renderer instanceof DigitalHumanRenderer) {
      renderer.setCallbacks({
        onSubtitleOn: (text: string) => {
          appState.ui.subTitleText = text
        },
        onSubtitleOff: () => {
          appState.ui.subTitleText = ''
        },
        onStateChange: (state: string) => {
          avatarState.value = state
        }
      })
    }
    
    // 连接SDK（先调用render设置容器，再调用connect连接）
    if (renderer.connect) {
      console.log('[用户角色连接] 调用 render, containerElement.id:', containerElement.id)
      // 先调用render设置容器
      await renderer.render(containerElement)
      console.log('[用户角色连接] 调用 connect')
      // 再调用connect连接SDK
      await renderer.connect()
      
      if (renderer instanceof DigitalHumanRenderer) {
        const instance = renderer.getInstance()
        if (instance) {
          role.digitalHumanInstance = instance
          // 同步更新 appState.currentUserRole 的实例
          if (appState.currentUserRole) {
            appState.currentUserRole.digitalHumanInstance = instance
          }
        }
      }
      role.isConnected = true
      // 同步更新 appState.currentUserRole 的连接状态
      if (appState.currentUserRole) {
        appState.currentUserRole.isConnected = true
      }
      
      // 显示状态已在连接前设置，这里不需要再次设置
      
      showToastMessage('连接成功', 'success')
    } else {
      showToastMessage('渲染器不支持连接操作', 'error')
      // 回滚状态
      role.showDigitalHuman = false
      role.isConnecting = false
      // 同步回滚 appState.currentUserRole 的状态
      if (appState.currentUserRole) {
        appState.currentUserRole.showDigitalHuman = false
        appState.currentUserRole.isConnecting = false
      }
    }
  } catch (error) {
    console.error('连接失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    showToastMessage(`连接失败: ${errorMessage}`, 'error')
    // 回滚状态
    role.isConnecting = false
    role.showDigitalHuman = false
    // 同步回滚 appState.currentUserRole 的状态
    if (appState.currentUserRole) {
      appState.currentUserRole.isConnecting = false
      appState.currentUserRole.showDigitalHuman = false
    }
  }
}

// 从角色列表断开用户角色数字人
async function handleDisconnectUserRoleFromList(role: UserRole) {
  const userRoleId = `user:${role.id}`
  const renderer = rendererManager.getRenderer(userRoleId)
  
  if (!renderer) {
    showToastMessage('该角色未连接', 'info')
    return
  }
  
  try {
    // 断开连接
    if (renderer.disconnect) {
      await renderer.disconnect()
    }
    
    // 隐藏数字人
    renderer.hide()
    
    // 清理角色对象上的状态
    role.showDigitalHuman = false
    role.digitalHumanInstance = null
    role.isConnected = false
    role.isConnecting = false
    
    // 同步更新 appState.currentUserRole 的状态
    if (appState.currentUserRole && appState.currentUserRole.id === role.id) {
      appState.currentUserRole.showDigitalHuman = false
      appState.currentUserRole.digitalHumanInstance = null
      appState.currentUserRole.isConnected = false
      appState.currentUserRole.isConnecting = false
    }
    
    // 销毁渲染器（可选，也可以保留以便后续重新连接）
    // rendererManager.destroyRenderer(userRoleId)
    
    showToastMessage('已断开连接', 'success')
  } catch (error) {
    console.error('断开连接失败:', error)
    showToastMessage('断开连接失败', 'error')
  }
}

// 从数字人容器中截图并设置为角色头像
async function handleCaptureDigitalHuman() {
  // 检查连接状态：优先检查编辑中的角色，否则检查当前角色
  const isConnected = (showUserRoleEditForm.value && editingUserRole.value?.isConnected) ||
                      (showRoleEditForm.value && editingRole.value?.isConnected) ||
                      (appState.currentUserRole?.isConnected) ||
                      (appState.currentPartnerRole?.isConnected)
  
  if (!isConnected) {
    showToastMessage('请先连接数字人', 'error')
    return
  }
  
  try {
    // 获取容器ID（优先使用编辑界面的容器）
    let containerId: string
    if (showUserRoleEditForm.value && userRoleForm.value.type === 'digital_human') {
      containerId = userRoleEditContainerId.value
    } else if (showRoleEditForm.value && roleForm.value.type === 'digital_human') {
      containerId = editContainerId.value
    } else {
      // 主界面：根据当前角色类型选择容器
      const currentUserRole = currentUserRoleInfo.value
      const currentPartnerRole = currentPartnerRoleInfo.value
      if (currentUserRole?.type === 'digital_human') {
        containerId = 'user-digital-human-container'
      } else if (currentPartnerRole?.type === 'digital_human') {
        containerId = avatarService.getContainerId()
      } else {
        containerId = avatarService.getContainerId()
      }
    }
    
    const container = document.getElementById(containerId)
    
    if (!container) {
      showToastMessage('未找到数字人容器', 'error')
      return
    }
    
    // 在容器内查找canvas元素
    const canvas = container.querySelector('canvas') as HTMLCanvasElement
    
    if (!canvas) {
      showToastMessage('未找到canvas元素，数字人可能未完全加载', 'error')
      return
    }
    
    // 检查canvas是否有内容
    const width = canvas.width
    const height = canvas.height
    
    if (width === 0 || height === 0) {
      showToastMessage('canvas尺寸为0，数字人可能未完全加载，请稍候再试', 'error')
      return
    }
    
    console.log('准备截图，canvas尺寸:', width, 'x', height)
    
    // 从WebGL context读取像素数据（保障截图成功）
    const gl = (canvas.getContext('webgl', { preserveDrawingBuffer: true }) || 
                canvas.getContext('webgl2', { preserveDrawingBuffer: true }) || 
                canvas.getContext('experimental-webgl', { preserveDrawingBuffer: true })) as WebGLRenderingContext | null
    
    if (gl) {
      // 使用WebGL readPixels读取当前帧缓冲区的像素数据
      console.log('使用WebGL readPixels方法截图')
      
      // 等待下一帧渲染完成（确保读取的是最新渲染的内容）
      await new Promise(resolve => requestAnimationFrame(resolve))
      await new Promise(resolve => requestAnimationFrame(resolve))
      
      // 保存当前状态
      const currentFramebuffer = gl.getParameter(gl.FRAMEBUFFER_BINDING)
      const currentViewport = gl.getParameter(gl.VIEWPORT)
      
      // 确保绑定到默认framebuffer（屏幕）
      gl.bindFramebuffer(gl.FRAMEBUFFER, null)
      
      // 确保viewport正确
      gl.viewport(0, 0, width, height)
      
      const pixels = new Uint8Array(width * height * 4)
      gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels)
      
      // 恢复framebuffer和viewport
      gl.bindFramebuffer(gl.FRAMEBUFFER, currentFramebuffer)
      if (currentViewport && currentViewport.length === 4) {
        gl.viewport(currentViewport[0], currentViewport[1], currentViewport[2], currentViewport[3])
      }
      
      // 检查是否有非透明像素（确保不是空白图）
      let hasContent = false
      for (let i = 3; i < pixels.length; i += 4) {
        if (pixels[i] > 0) { // Alpha通道大于0表示有内容
          hasContent = true
          break
        }
      }
      
      if (!hasContent) {
        showToastMessage('截图失败：canvas内容为空', 'error')
        return
      }
      
      // 创建临时canvas来转换像素数据
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = width
      tempCanvas.height = height
      const tempCtx = tempCanvas.getContext('2d')
      
      if (!tempCtx) {
        showToastMessage('截图失败：无法创建临时canvas', 'error')
        return
      }
      
      // 创建ImageData并绘制到临时canvas（需要翻转Y轴，因为WebGL的坐标系是倒置的）
      const imageData = tempCtx.createImageData(width, height)
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const srcIndex = (y * width + x) * 4
          const dstIndex = ((height - 1 - y) * width + x) * 4
          imageData.data[dstIndex] = pixels[srcIndex]     // R
          imageData.data[dstIndex + 1] = pixels[srcIndex + 1] // G
          imageData.data[dstIndex + 2] = pixels[srcIndex + 2] // B
          imageData.data[dstIndex + 3] = pixels[srcIndex + 3] // A
        }
      }
      tempCtx.putImageData(imageData, 0, 0)
      
      // 转换为blob并上传
      tempCanvas.toBlob(async (blob) => {
        if (!blob) {
          showToastMessage('截图失败：无法生成图片', 'error')
          return
        }
        
        await uploadScreenshot(blob)
      }, 'image/png', 1.0)
    } else {
      // 不是WebGL canvas，使用标准方法（2D canvas）
      canvas.toBlob(async (blob) => {
        if (!blob) {
          showToastMessage('截图失败：无法生成图片', 'error')
          return
        }
        
        await uploadScreenshot(blob)
      }, 'image/png', 1.0)
    }
    
    // 上传截图的函数
    async function uploadScreenshot(blob: Blob) {
      // 创建FormData上传图片
      const formData = new FormData()
      formData.append('avatar', blob, 'digital-human-avatar.png')
      
      try {
        const response = await fetch('http://localhost:3001/api/upload/avatar', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          throw new Error('上传失败')
        }
        
        const data = await response.json()
        const avatarUrl = data.url || `/uploads/avatars/${data.filename}`
        
        // 更新角色表单的头像字段
        if (showUserRoleEditForm.value && userRoleForm.value.type === 'digital_human') {
          userRoleForm.value.avatar = avatarUrl
        } else if (showRoleEditForm.value && roleForm.value.type === 'digital_human') {
          roleForm.value.avatar = avatarUrl
        }
        
        showToastMessage('截图成功，已设置为角色头像', 'success')
      } catch (error) {
        console.error('上传头像失败:', error)
        showToastMessage('上传头像失败', 'error')
      }
    }
  } catch (error) {
    console.error('截图失败:', error)
    showToastMessage('截图失败: ' + (error as Error).message, 'error')
  }
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
    showToastMessage('请先配置ASR信息（App ID、Secret ID、Secret Key）', 'error')
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
  
  // 演讲模式：不调用大模型，直接使用输入内容作为消息
  if (appState.conversationMode === 'speech') {
    const content = appState.ui.text.trim()
    if (!content) return
    
    // 确定说话人角色
    const role = currentSpeaker.value === 'user' 
      ? appState.currentUserRole 
      : appState.currentPartnerRole
    
    if (!role) {
      showToastMessage('未设置说话人角色', 'error')
      return
    }
    
    // 创建消息
    const message: ChatMessage = {
      role: currentSpeaker.value === 'user' ? 'user' : 'assistant',
      content: content,
      timestamp: Date.now()
    }
    
    // 添加到对话历史
    appState.chatHistory.push(message)
    
    // 保存到数据库（演讲模式：每条消息单独保存，统一使用伙伴角色的user字段）
    try {
      // 统一使用伙伴角色的user字段（与AI模式保持一致，数据记录以伙伴为准）
      const partnerUser = appState.currentPartnerRole?.user || appState.llm.user || ''
      if (!partnerUser) {
        console.warn('伙伴角色user字段为空，无法保存消息到数据库')
        showToastMessage('伙伴角色user字段为空，消息未保存到数据库', 'error')
        return
      }
      
      const apiKey = globalApiKey.value || ''
      if (!apiKey) {
        console.warn('API Key为空，无法保存消息到数据库')
        showToastMessage('API Key为空，消息未保存到数据库', 'error')
        return
      }
      
      await saveChatMessage(
        message.role,
        content,
        apiKey,
        partnerUser,
        message.timestamp
      )
      console.log('演讲模式消息已保存到数据库:', { 
        role: message.role, 
        user: partnerUser, 
        apiKey: apiKey.substring(0, 10) + '...',
        content: content.substring(0, 50),
        timestamp: message.timestamp
      })
    } catch (error) {
      console.error('保存消息失败:', error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      showToastMessage('保存消息失败: ' + errorMessage, 'error')
    }
    
    // 注意：自动切换和自动播放由 watch 监听器统一处理，避免重复执行
    
    // 清空输入框
    appState.ui.text = ''
    return
  }
  
  // AI对话模式：调用大模型
  isSending.value = true
  try {
    await appStore.sendMessage()
  } catch (error) {
    console.error('发送消息失败:', error)
    showToastMessage('发送消息失败', 'error')
  } finally {
    isSending.value = false
  }
}

// 菜单相关方法
function toggleMenu() {
  showMenu.value = !showMenu.value
}

function toggleHistorySubmenu() {
  showHistorySubmenu.value = !showHistorySubmenu.value
}

async function clearChatHistory() {
  if (appState.chatHistory.length === 0) {
    showToastMessage('对话历史已为空', 'info')
    return
  }
  
  if (!confirm('确定要清空所有对话历史吗？此操作不可恢复。')) {
    return
  }
  
  try {
    // 统一使用伙伴角色的user字段（与AI模式保持一致，数据记录以伙伴为准）
    const partnerUser = appState.currentPartnerRole?.user || appState.llm.user || ''
    if (!partnerUser) {
      showToastMessage('伙伴角色user字段为空，无法清空对话历史', 'error')
      return
    }
    
    await clearChatHistoryService(globalApiKey.value || '', partnerUser)
    
    // 清空前端状态
    appState.chatHistory = []
    showToastMessage('对话历史已清空', 'success')
    
    // 关闭菜单
    showMenu.value = false
  } catch (error) {
    console.error('清空对话历史失败:', error)
    showToastMessage('清空对话历史失败', 'error')
  }
}

function toggleBackgroundSubmenu() {
  showBackgroundSubmenu.value = !showBackgroundSubmenu.value
}

function toggleConversationModeSubmenu() {
  showConversationModeSubmenu.value = !showConversationModeSubmenu.value
}

// 更新说话人列表（在登录、切换模式、切换角色时调用）
function updateSpeakerList() {
  // 如果当前是演讲模式，更新默认说话人选择
  if (appState.conversationMode === 'speech') {
    if (appState.currentUserRole) {
      currentSpeaker.value = 'user'
    } else if (appState.currentPartnerRole) {
      currentSpeaker.value = 'partner'
    }
  }
}

// 设置对话模式
function setConversationMode(mode: 'ai' | 'speech') {
  appState.conversationMode = mode
  showConversationModeSubmenu.value = false
  showMenu.value = false
  handleSaveConfig() // 保存配置
  const modeName = mode === 'ai' ? 'AI对话模式' : '演示对话模式'
  showToastMessage(`已切换到${modeName}`, 'success')
  
  // 时机2：切换对话模式时更新说话人列表
  updateSpeakerList()
}

function toggleHistoryPanel() {
  showHistoryPanel.value = !showHistoryPanel.value
  showMenu.value = false
  }

// 导出聊天记录（JSON格式）
function exportChatHistory() {
  if (appState.chatHistory.length === 0) {
    showToastMessage('暂无聊天记录可导出', 'info')
    return
  }

  // 生成文件名（包含时间戳）
  const now = new Date()
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '')
  const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, '')
  const filename = `chat_history_${dateStr}_${timeStr}.json`

  // 构建导出数据
  const exportData = {
    exportTime: now.toISOString(),
    exportTimeLocale: now.toLocaleString('zh-CN'),
    totalMessages: appState.chatHistory.length,
    messages: appState.chatHistory.map((message) => ({
      role: message.role,
      content: message.content,
      timestamp: message.timestamp || null
    }))
  }

  // 转换为JSON字符串（格式化，2空格缩进）
  const jsonContent = JSON.stringify(exportData, null, 2)

  // 创建Blob并下载
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  
  // 延迟清理，确保下载完成
  setTimeout(() => {
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, 100)

  showToastMessage(`聊天记录导出成功：${filename}`, 'success')
  showMenu.value = false
  }

function handleOpenTtsAsrSettings() {
  showTtsAsrSettingsModal.value = true
  showMenu.value = false
  activeTtsAsrTab.value = 'tts'
}

function handleOpenMofaInviteCode() {
  showMofaInviteCodeModal.value = true
  showMenu.value = false
}

function handleQrCodeImageError(event: Event) {
  console.error('二维码图片加载失败:', event)
  showToastMessage('二维码图片加载失败，请检查图片文件是否存在', 'error')
}


// ========== 背景管理相关函数 ==========

// 切换Markdown图像提取开关
function toggleAutoExtractMarkdownImage() {
  autoExtractMarkdownImage.value = !autoExtractMarkdownImage.value
  handleSaveConfig()
  showToastMessage(autoExtractMarkdownImage.value ? '已启用Markdown图像提取' : '已禁用Markdown图像提取', 'info')
}

// 打开背景管理器
async function handleOpenBackgroundManager() {
  if (!globalApiKey.value) {
    showToastMessage('请先登录', 'error')
    return
  }
  showBackgroundManagerModal.value = true
  showMenu.value = false
  await loadBackgrounds()
}

// 加载背景列表
async function loadBackgrounds() {
  if (!globalApiKey.value) {
    backgrounds.value = []
    return
  }
  
  try {
    const backgroundList = await getBackgrounds(globalApiKey.value)
    backgrounds.value = backgroundList
    console.log('背景列表加载成功:', backgroundList.length, '个背景')
  } catch (error) {
    const errorMessage = (error as Error).message
    if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
      showToastMessage('无法连接到后端服务，请确保后端服务已启动（npm run server）', 'error')
    } else {
      showToastMessage('加载背景列表失败: ' + errorMessage, 'error')
    }
    console.error('加载背景列表失败:', error)
    backgrounds.value = []
  }
}

// 保存当前背景到背景管理器
async function handleSaveCurrentBackground() {
  if (!globalApiKey.value) {
    showToastMessage('请先登录', 'error')
    return
  }
  
  if (!appState.ui.backgroundImage) {
    showToastMessage('当前没有背景图像', 'info')
    return
  }
  
  // 弹出输入框让用户输入背景名称
  const name = prompt('请输入背景名称（可选，直接回车跳过）:')
  if (name === null) {
    // 用户取消
    return
  }
  
  try {
    await createBackgroundFromUrl(
      globalApiKey.value,
      appState.ui.backgroundImage,
      name?.trim() || undefined
    )
    showToastMessage('背景已保存', 'success')
    // 如果背景管理器已打开，重新加载列表
    if (showBackgroundManagerModal.value) {
      await loadBackgrounds()
    }
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
    console.error('保存背景失败:', error)
  }
}

// 设置背景为当前背景
function handleSetBackground(background: Background) {
  // 处理URL（相对路径添加服务器地址）
  let url = background.url
  if (url && !url.startsWith('http') && url.startsWith('/')) {
    url = `http://localhost:3001${url}`
  }
  appState.ui.backgroundImage = url
  showToastMessage('背景已设置', 'success')
}

// 清空当前背景
function handleClearBackground() {
  appState.ui.backgroundImage = ''
  showToastMessage('背景已清空', 'success')
}

// 删除背景
async function handleDeleteBackground(background: Background) {
  if (!confirm(`确定要删除背景"${background.name || '(未命名)'}"吗？`)) {
    return
  }
  
  try {
    await deleteBackground(background.id, globalApiKey.value)
    showToastMessage('背景已删除', 'success')
    await loadBackgrounds()
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
  }
}

// 重命名背景
async function handleRenameBackground(background: Background) {
  const newName = prompt('请输入新的背景名称:', background.name || '')
  if (newName === null) {
    // 用户取消
    return
  }
  
  try {
    await updateBackground(background.id, globalApiKey.value, newName.trim() || undefined)
    showToastMessage('背景已重命名', 'success')
    await loadBackgrounds()
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
  }
}

// 下载背景
async function handleDownloadBackground(background: Background) {
  try {
    // 处理URL（相对路径添加服务器地址）
    let url = background.url
    if (url && !url.startsWith('http') && url.startsWith('/')) {
      url = `http://localhost:3001${url}`
    }
    
    // 如果是跨域URL，需要先fetch获取blob
    if (url.startsWith('http')) {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('下载失败')
      }
      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)
      
      // 创建下载链接
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = background.name || `background-${background.id}`
      // 确保触发下载而不是打开
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      
      // 清理
      setTimeout(() => {
        document.body.removeChild(link)
        URL.revokeObjectURL(blobUrl)
      }, 100)
  } else {
      // 同源URL直接下载
  const link = document.createElement('a')
  link.href = url
      link.download = background.name || `background-${background.id}`
      link.style.display = 'none'
      document.body.appendChild(link)
  link.click()
      setTimeout(() => {
        document.body.removeChild(link)
      }, 100)
    }
    
    showToastMessage('背景下载中', 'info')
  } catch (error) {
    showToastMessage('下载失败: ' + (error as Error).message, 'error')
    console.error('下载背景失败:', error)
  }
}

// 获取背景URL（处理相对路径和绝对路径）
function getBackgroundUrl(url: string): string {
  if (!url) return ''
  // 如果是完整URL或绝对路径，直接返回
  if (url.startsWith('http') || url.startsWith('/')) {
    if (url.startsWith('/')) {
      return `http://localhost:3001${url}`
    }
    return url
  }
  // 如果是相对路径，添加服务器地址
  return `http://localhost:3001${url}`
}

// 处理背景图片加载错误
function handleBackgroundImageError(event: Event) {
  const img = event.target as HTMLImageElement
  img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7lm77niYfliqDovb3lpLHotKU8L3RleHQ+PC9zdmc+'
}

// 上传背景图像
async function handleUploadBackground(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  
    if (!file) {
    return
  }
  
  if (!globalApiKey.value) {
    showToastMessage('请先登录', 'error')
    return
  }
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    showToastMessage('请选择图片文件', 'error')
    return
  }
  
  // 检查文件大小
  if (file.size > 50 * 1024 * 1024) {
    showToastMessage('图片大小不能超过50MB', 'error')
    return
  }
  
  try {
    await uploadBackground(globalApiKey.value, file)
    showToastMessage('背景上传成功', 'success')
    await loadBackgrounds()
    // 清空input，以便可以重复选择同一文件
    if (input) {
      input.value = ''
    }
    // 同时清空ref
    if (backgroundFileInputRef.value) {
      backgroundFileInputRef.value.value = ''
    }
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
    console.error('上传背景失败:', error)
  }
}


// 用户角色管理
// ========== 用户角色管理相关函数 ==========

// 打开用户角色管理
async function handleOpenUserRoleManagement() {
  showUserRoleManagementModal.value = true
  showMenu.value = false
  
  // 注意：不在这里加载用户角色列表，因为：
  // 1. 登录时已经加载过了（handleLogin）
  // 2. 保存/删除/切换角色时会重新加载
  // 3. 打开面板只是为了显示，不需要重新加载和初始化，避免丢失连接状态
}

// 打开APIKey登录模态框
function handleOpenApiKeyLogin() {
  showApiKeyLoginModal.value = true
      showMenu.value = false
  // 如果已登录，不需要重置输入框
  if (!globalApiKey.value) {
    loginApiKeyInput.value = ''
  }
}

// APIKey登录（从登录模态框调用）
async function handleApiKeyLogin() {
  if (!loginApiKeyInput.value || !loginApiKeyInput.value.trim()) {
    showToastMessage('请输入 API Key', 'error')
      return
    }
    
  try {
    // 先关闭登录模态框，避免标题闪烁
    showApiKeyLoginModal.value = false
    
    globalApiKey.value = loginApiKeyInput.value.trim()
    // 应用 apiKey 到 appState.llm.apiKey（用于后续的 API 调用）
    appState.llm.apiKey = globalApiKey.value
    // 加载用户角色列表
    await loadUserRoles()
    
    // 检查是否有当前用户角色
    if (!appState.currentUserRole) {
      // 没有当前用户角色，弹出角色创建面板
      showUserRoleManagementModal.value = true
      showUserRoleEditForm.value = true
      // 初始化表单
      userRoleForm.value = {
        user: '',
        name: '',
        type: 'illustration',
        avatar: '',
        positionX: 50,
        positionY: 50,
        scale: 0.7,
        baseURL: '',
        model: '',
        avatarAppId: '',
        avatarAppSecret: '',
        ttsProvider: 'doubao',
        ttsVoice: '',
        ttsSpeed: 1.0,
        ttsVolume: 1.0,
        ttsPreviewText: '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
        enableVoicePlay: false,
        enableAutoPlay: false,
        enableAutoSwitch: false,
        useDigitalHumanVoice: true
      }
      editingUserRole.value = null
      showToastMessage('请先创建用户角色', 'info')
    } else {
      // 有当前用户角色，只激活菜单和加载数据
      // 加载伙伴角色列表（使用 globalApiKey 过滤）
      await loadRoles()
      // 获取并设置当前伙伴角色（时机1：用户登录时）
      await getAndSetCurrentPartnerRole()
      // 加载对话历史（登录后才加载）
      await loadHistory()
      // 记录当前角色并更新连接按钮可用状态
      const event = new CustomEvent('roleUpdated')
      window.dispatchEvent(event)
      // 时机1：apikey登录后更新说话人列表
      updateSpeakerList()
      showToastMessage('登录成功', 'success')
    }
    
    loginApiKeyInput.value = ''
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
    globalApiKey.value = ''
    appState.llm.apiKey = ''
  }
}

// 登录（从用户角色管理模态框调用，保持原有逻辑）
async function handleLogin() {
  if (!loginApiKeyInput.value || !loginApiKeyInput.value.trim()) {
    showToastMessage('请输入 API Key', 'error')
          return
        }
        
  try {
    globalApiKey.value = loginApiKeyInput.value.trim()
    // 应用 apiKey 到 appState.llm.apiKey（用于后续的 API 调用）
    appState.llm.apiKey = globalApiKey.value
    // 加载用户角色列表
    await loadUserRoles()
    
    // 检查是否有当前用户角色
    if (!appState.currentUserRole) {
      // 没有当前用户角色，弹出角色创建面板
      showUserRoleEditForm.value = true
      // 初始化表单
      userRoleForm.value = {
        user: '',
        name: '',
        type: 'illustration',
        avatar: '',
        positionX: 50,
        positionY: 50,
        scale: 0.7,
        baseURL: '',
        model: '',
        avatarAppId: '',
        avatarAppSecret: '',
        ttsProvider: 'doubao',
        ttsVoice: '',
        ttsSpeed: 1.0,
        ttsVolume: 1.0,
        ttsPreviewText: '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
        enableVoicePlay: false,
        enableAutoPlay: false,
        enableAutoSwitch: false,
        useDigitalHumanVoice: true
      }
      editingUserRole.value = null
      showToastMessage('请先创建用户角色', 'info')
        } else {
      // 有当前用户角色，只激活菜单和加载数据
      // 加载伙伴角色列表（使用 globalApiKey 过滤）
      await loadRoles()
      // 获取并设置当前伙伴角色（时机1：用户登录时）
      await getAndSetCurrentPartnerRole()
      // 加载对话历史（登录后才加载）
      await loadHistory()
      // 时机1：apikey登录后更新说话人列表
      updateSpeakerList()
      showToastMessage('登录成功', 'success')
    }
    
    loginApiKeyInput.value = ''
      } catch (error) {
    showToastMessage((error as Error).message, 'error')
    globalApiKey.value = ''
    appState.llm.apiKey = ''
  }
}

// 退出登录并关闭模态框
function handleLogoutAndClose() {
  handleLogout()
  showApiKeyLoginModal.value = false
      }

// 退出登录
function handleLogout() {
  // 先失活当前角色并清理状态
  if (appState.currentUserRole) {
    deactivateUserRole(appState.currentUserRole)
  }
  if (appState.currentPartnerRole) {
    deactivatePartnerRole(appState.currentPartnerRole)
  }
  
  // 销毁所有数字人渲染器
  const allRenderers = rendererManager.getAllRenderers()
  for (const [roleId] of allRenderers) {
    if (roleId.startsWith('user:') || roleId.startsWith('partner:')) {
      rendererManager.destroyRenderer(roleId)
    }
  }
  
  // 清空数组和引用
  globalApiKey.value = ''
  userRoles.value = []
  appState.currentUserRole = null
  roles.value = [] // 清空伙伴角色列表
  appState.currentPartnerRole = null
  // 清空对话历史
  appState.chatHistory = []
  // 重置 LLM 配置
  appState.llm.apiKey = ''
  appState.llm.user = ''
  showToastMessage('已退出登录', 'info')
}

// 加载用户角色列表
async function loadUserRoles() {
  if (!globalApiKey.value) {
    userRoles.value = []
    appState.currentUserRole = null
    return
  }
  
  try {
    const roleList = await getUserRoles(globalApiKey.value)
    // 初始化每个角色的数字人相关属性
    roleList.forEach(role => {
      const userRoleId = `user:${role.id}`
      // 初始化内存状态属性
      role.isConnecting = false
      role.isConnected = false
      role.showDigitalHuman = false
      role.digitalHumanInstance = null
      
      // 状态恢复：检查 rendererManager 是否存在渲染器
      const renderer = rendererManager.getRenderer(userRoleId)
      if (renderer && renderer instanceof DigitalHumanRenderer) {
        // 恢复连接状态
        role.isConnected = true
        role.showDigitalHuman = true
        const instance = renderer.getInstance()
        if (instance) {
          role.digitalHumanInstance = instance
        }
      }
    })
    userRoles.value = roleList
    // 查找当前角色
    const currentRole = roleList.find(r => r.isCurrent) || null
    appState.currentUserRole = currentRole
    // 如果设置了当前角色，应用其配置
    if (currentRole) {
      if (currentRole.baseURL) {
        appState.llm.baseURL = currentRole.baseURL
      }
      if (currentRole.model) {
        appState.llm.model = currentRole.model
      }
      appState.llm.apiKey = globalApiKey.value
      // 激活用户角色
      await activateUserRole(currentRole)
    }
    console.log('用户角色列表加载成功:', roleList.length, '个角色, apiKey:', globalApiKey.value)
    // 验证隔离：检查所有角色的 apiKey 是否都等于当前 apiKey
    const invalidRoles = roleList.filter(r => r.apiKey !== globalApiKey.value)
    if (invalidRoles.length > 0) {
      console.error('用户角色隔离失败！发现不属于当前 apiKey 的角色:', invalidRoles)
    }
  } catch (error) {
    const errorMessage = (error as Error).message
    if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
      showToastMessage('无法连接到后端服务，请确保后端服务已启动（npm run server）', 'error')
    } else {
      showToastMessage('加载用户角色列表失败: ' + errorMessage, 'error')
    }
    console.error('加载用户角色列表失败:', error)
    userRoles.value = []
    appState.currentUserRole = null
  }
}

// 创建用户角色
function handleCreateUserRole() {
  editingUserRole.value = null
  const defaultType = 'illustration' as 'digital_human' | 'illustration'
  const defaultUseDigitalHumanVoice = true
  userRoleForm.value = {
    user: '',
    name: '',
    type: defaultType,
    avatar: '',
    positionX: 20,
    positionY: 50,
    scale: 0.7,
    baseURL: '',
    model: '',
    avatarAppId: '',
    avatarAppSecret: '',
    useDigitalHumanVoice: defaultUseDigitalHumanVoice,
        ttsProvider: 'doubao',
        ttsVoice: '',
        ttsSpeed: appState.tts.speed ?? 1.0,
        ttsVolume: appState.tts.volume ?? 1.0,
        ttsPreviewText: '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
        enableVoicePlay: false,
        enableAutoPlay: false,
        enableAutoSwitch: false
      }
      showUserRoleEditForm.value = true
}

// 编辑用户角色
function handleEditUserRole(role: UserRole) {
  editingUserRole.value = role
  userRoleForm.value = {
    user: role.user || '',
    name: role.name || '',
    type: role.type || 'illustration',
    avatar: role.avatar || '',
    positionX: role.positionX !== undefined ? role.positionX : 20,
    positionY: role.positionY !== undefined ? role.positionY : 50,
    scale: role.scale !== undefined ? role.scale : (role.type === 'illustration' ? 0.7 : 1.0),
    baseURL: role.baseURL || '',
    model: role.model || '',
    avatarAppId: role.avatarAppId || '',
    avatarAppSecret: role.avatarAppSecret || '',
    useDigitalHumanVoice: role.useDigitalHumanVoice !== undefined ? role.useDigitalHumanVoice : true,
    ttsProvider: role.ttsProvider || 'doubao',
    ttsVoice: role.ttsVoice || '',
    ttsSpeed: role.ttsSpeed !== undefined ? role.ttsSpeed : (appState.tts.speed ?? 1.0),
    ttsVolume: role.ttsVolume !== undefined ? role.ttsVolume : (appState.tts.volume ?? 1.0),
    ttsPreviewText: (role as any).ttsPreviewText || '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
    enableVoicePlay: role.enableVoicePlay !== undefined ? role.enableVoicePlay : false,
    enableAutoPlay: role.enableAutoPlay !== undefined ? role.enableAutoPlay : false,
    enableAutoSwitch: role.enableAutoSwitch !== undefined ? role.enableAutoSwitch : false
  }
  showUserRoleEditForm.value = true
}

// 取消编辑
function handleCancelUserRoleEdit() {
  showUserRoleEditForm.value = false
  editingUserRole.value = null
}

// 保存用户角色
async function handleSaveUserRole() {
  if (!globalApiKey.value) {
    showToastMessage('请先登录', 'error')
      return
    }
    
  // 验证user字段必填
  if (!userRoleForm.value.user || !userRoleForm.value.user.trim()) {
    showToastMessage('user字段不能为空', 'error')
    return
  }
    
  try {
    // 记录创建前是否有角色
    const hadRolesBefore = userRoles.value.length > 0
    let createdRoleId: number | null = null
    
    // 判断是创建还是编辑：如果 editingUserRole.value 存在且 id > 0，才是编辑模式
    // 如果 id === 0，说明是创建新角色时连接数字人创建的临时对象，应该按创建模式处理
    if (editingUserRole.value && editingUserRole.value.id > 0) {
      // 更新用户角色
      const oldRole = userRoles.value.find(r => r.id === editingUserRole.value!.id)
      const typeChanged = oldRole?.type !== userRoleForm.value.type
      
      // 如果类型从数字人改为立绘，需要清理数字人状态
      if (typeChanged && oldRole?.type === 'digital_human') {
        const userRoleId = `user:${oldRole.id}`
        const renderer = rendererManager.getRenderer(userRoleId)
        if (renderer) {
          if (renderer.disconnect) {
            await renderer.disconnect()
          }
          rendererManager.destroyRenderer(userRoleId)
        }
        // 清理内存状态属性
        oldRole.isConnected = false
        oldRole.showDigitalHuman = false
        oldRole.digitalHumanInstance = null
        oldRole.isConnecting = false
      }
      
      // 更新数据库
      const updatedRole = await updateUserRole(
        editingUserRole.value.id,
        globalApiKey.value,
        {
          user: userRoleForm.value.user.trim(),
          name: userRoleForm.value.name.trim() || undefined,
          type: userRoleForm.value.type,
          avatar: userRoleForm.value.avatar && userRoleForm.value.avatar.trim() ? userRoleForm.value.avatar.trim() : undefined,
          positionX: userRoleForm.value.positionX,
          positionY: userRoleForm.value.positionY,
          scale: userRoleForm.value.scale,
          baseURL: userRoleForm.value.baseURL.trim() || undefined,
          model: userRoleForm.value.model.trim() || undefined,
          avatarAppId: userRoleForm.value.avatarAppId && userRoleForm.value.avatarAppId.trim() ? userRoleForm.value.avatarAppId.trim() : undefined,
          avatarAppSecret: userRoleForm.value.avatarAppSecret && userRoleForm.value.avatarAppSecret.trim() ? userRoleForm.value.avatarAppSecret.trim() : undefined,
          useDigitalHumanVoice: userRoleForm.value.useDigitalHumanVoice !== undefined ? userRoleForm.value.useDigitalHumanVoice : undefined,
          ttsProvider: userRoleForm.value.ttsProvider !== undefined && userRoleForm.value.ttsProvider !== null && userRoleForm.value.ttsProvider !== '' ? userRoleForm.value.ttsProvider : undefined,
          ttsVoice: userRoleForm.value.ttsVoice !== undefined && userRoleForm.value.ttsVoice !== null && userRoleForm.value.ttsVoice !== '' ? userRoleForm.value.ttsVoice : undefined,
          ttsSpeed: userRoleForm.value.ttsSpeed !== undefined ? userRoleForm.value.ttsSpeed : undefined,
          ttsVolume: userRoleForm.value.ttsVolume !== undefined ? userRoleForm.value.ttsVolume : undefined,
          ttsPreviewText: userRoleForm.value.ttsPreviewText !== undefined && userRoleForm.value.ttsPreviewText !== null && userRoleForm.value.ttsPreviewText !== '' ? userRoleForm.value.ttsPreviewText : undefined,
          enableVoicePlay: userRoleForm.value.enableVoicePlay !== undefined ? userRoleForm.value.enableVoicePlay : undefined,
          enableAutoPlay: userRoleForm.value.enableAutoPlay !== undefined ? userRoleForm.value.enableAutoPlay : undefined,
          enableAutoSwitch: userRoleForm.value.enableAutoSwitch !== undefined ? userRoleForm.value.enableAutoSwitch : undefined
        }
      )
      
      // 只更新那个角色的属性，不重新加载所有角色
      const roleIndex = userRoles.value.findIndex(r => r.id === editingUserRole.value!.id)
      if (roleIndex !== -1) {
        // 更新数据库属性
        Object.assign(userRoles.value[roleIndex], updatedRole)
        // 如果类型未变更，保持内存状态属性；如果类型变更，已在上面清理
        if (!typeChanged && oldRole) {
          // 保持原有的内存状态属性
          userRoles.value[roleIndex].isConnecting = oldRole.isConnecting
          userRoles.value[roleIndex].isConnected = oldRole.isConnected
          userRoles.value[roleIndex].showDigitalHuman = oldRole.showDigitalHuman
          userRoles.value[roleIndex].digitalHumanInstance = oldRole.digitalHumanInstance
        } else if (typeChanged && userRoleForm.value.type === 'digital_human') {
          // 从立绘改为数字人：初始化数字人属性
          userRoles.value[roleIndex].isConnecting = false
          userRoles.value[roleIndex].isConnected = false
          userRoles.value[roleIndex].showDigitalHuman = false
          userRoles.value[roleIndex].digitalHumanInstance = null
        }
        
        // 如果更新的是当前角色，更新引用（保持引用不变，只更新属性）
        if (appState.currentUserRole?.id === editingUserRole.value.id) {
          appState.currentUserRole = userRoles.value[roleIndex]
        }
      }
      
      showToastMessage('用户角色已更新', 'success')
        } else {
      // 创建用户角色
      const newRole = await createUserRole(
        globalApiKey.value,
        {
          user: userRoleForm.value.user.trim(),
          name: userRoleForm.value.name.trim() || undefined,
          type: userRoleForm.value.type,
          avatar: userRoleForm.value.avatar && userRoleForm.value.avatar.trim() ? userRoleForm.value.avatar.trim() : undefined,
          positionX: userRoleForm.value.positionX,
          positionY: userRoleForm.value.positionY,
          scale: userRoleForm.value.scale,
          baseURL: userRoleForm.value.baseURL.trim() || undefined,
          model: userRoleForm.value.model.trim() || undefined,
          avatarAppId: userRoleForm.value.avatarAppId && userRoleForm.value.avatarAppId.trim() ? userRoleForm.value.avatarAppId.trim() : undefined,
          avatarAppSecret: userRoleForm.value.avatarAppSecret && userRoleForm.value.avatarAppSecret.trim() ? userRoleForm.value.avatarAppSecret.trim() : undefined,
          useDigitalHumanVoice: userRoleForm.value.useDigitalHumanVoice !== undefined ? userRoleForm.value.useDigitalHumanVoice : undefined,
          ttsProvider: userRoleForm.value.ttsProvider !== undefined && userRoleForm.value.ttsProvider !== null && userRoleForm.value.ttsProvider !== '' ? userRoleForm.value.ttsProvider : undefined,
          ttsVoice: userRoleForm.value.ttsVoice !== undefined && userRoleForm.value.ttsVoice !== null && userRoleForm.value.ttsVoice !== '' ? userRoleForm.value.ttsVoice : undefined,
          ttsSpeed: userRoleForm.value.ttsSpeed !== undefined ? userRoleForm.value.ttsSpeed : undefined,
          ttsVolume: userRoleForm.value.ttsVolume !== undefined ? userRoleForm.value.ttsVolume : undefined,
          ttsPreviewText: userRoleForm.value.ttsPreviewText !== undefined && userRoleForm.value.ttsPreviewText !== null && userRoleForm.value.ttsPreviewText !== '' ? userRoleForm.value.ttsPreviewText : undefined,
          enableVoicePlay: userRoleForm.value.enableVoicePlay !== undefined ? userRoleForm.value.enableVoicePlay : undefined,
          enableAutoPlay: userRoleForm.value.enableAutoPlay !== undefined ? userRoleForm.value.enableAutoPlay : undefined,
          enableAutoSwitch: userRoleForm.value.enableAutoSwitch !== undefined ? userRoleForm.value.enableAutoSwitch : undefined
        }
      )
      createdRoleId = newRole.id
      
      // 初始化内存状态属性
      newRole.isConnecting = false
      newRole.isConnected = false
      newRole.showDigitalHuman = false
      newRole.digitalHumanInstance = null
      
      // 只添加新角色到列表，不重新加载所有角色
      userRoles.value.push(newRole)
      
      showToastMessage('用户角色已创建', 'success')
      
      // 如果当前用户角色为空，自动设置为当前角色
      if (!appState.currentUserRole) {
        const updatedRole = await setCurrentUserRole(createdRoleId, globalApiKey.value)
        // 更新列表中的角色的 isCurrent 属性
        const roleInList = userRoles.value.find(r => r.id === updatedRole.id)
        if (roleInList) {
          roleInList.isCurrent = true
          // 将其他角色的 isCurrent 设为 false
          userRoles.value.forEach(r => {
            if (r.id !== updatedRole.id) {
              r.isCurrent = false
            }
          })
          appState.currentUserRole = roleInList
          // 激活新创建的角色（如果是数字人类型，会设置 showDigitalHuman = true）
          await activateUserRole(roleInList)
        } else {
          appState.currentUserRole = updatedRole
          // 激活新创建的角色（如果是数字人类型，会设置 showDigitalHuman = true）
          await activateUserRole(updatedRole)
        }
      }
    }
    
    // 清理临时对象（如果是创建新角色时连接数字人创建的临时对象）
    if (editingUserRole.value && editingUserRole.value.id === 0) {
      editingUserRole.value = null
    }
    
    showUserRoleEditForm.value = false
    
    // 如果保存的是当前用户角色，触发AvatarRender重新加载角色信息
    if (appState.currentUserRole && (editingUserRole.value?.id === appState.currentUserRole.id || createdRoleId === appState.currentUserRole.id)) {
      const event = new CustomEvent('roleUpdated')
      window.dispatchEvent(event)
    }
    
    // 如果刚创建了第一个用户角色并已设置为当前角色，加载数据
    if (!editingUserRole.value && !hadRolesBefore && appState.currentUserRole) {
      // 加载伙伴角色列表
      await loadRoles()
      // 加载对话历史
      await loadHistory()
    }
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
    console.error('保存用户角色失败:', error)
  }
}

// 删除用户角色
async function handleDeleteUserRole(role: UserRole) {
  if (!confirm(`确定要删除用户角色"${role.name || '(未命名)'}"吗？`)) {
          return
        }
        
  try {
    const userRoleId = `user:${role.id}`
    const renderer = rendererManager.getRenderer(userRoleId)
    
    // 如果角色已连接，先断开连接和销毁渲染器
    if (renderer) {
      if (renderer.disconnect) {
        await renderer.disconnect()
      }
      rendererManager.destroyRenderer(userRoleId)
    }
    
    // 如果删除的是当前角色，先失活
    if (appState.currentUserRole?.id === role.id) {
      await deactivateUserRole(role)
      appState.currentUserRole = null
    }
    
    // 删除数据库记录
    await deleteUserRole(role.id, globalApiKey.value)
    
    // 只从列表中移除那个角色，不重新加载所有角色
    userRoles.value = userRoles.value.filter(r => r.id !== role.id)
    
    showToastMessage('用户角色已删除', 'success')
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
  }
}

// 设置当前用户角色
async function handleSetCurrentUserRole(role: UserRole) {
  try {
    // 步骤3.1：失活旧角色（清理旧角色的所有状态）
    if (appState.currentUserRole) {
      await deactivateUserRole(appState.currentUserRole)
    }
    
    // 步骤3.2：设置当前用户角色（调用API）
    await setCurrentUserRole(role.id, globalApiKey.value)
    
    // 步骤3.3：只更新 isCurrent 属性，不重新加载所有角色
    userRoles.value.forEach(r => {
      r.isCurrent = (r.id === role.id)
    })
    
    // 步骤3.4：更新当前角色标识（记录当前角色）
    const roleInList = userRoles.value.find(r => r.id === role.id)
    if (roleInList) {
      appState.currentUserRole = roleInList
        } else {
      appState.currentUserRole = role
    }
    
    // 步骤3.4.1：激活新角色（设置新角色的状态）
    await activateUserRole(appState.currentUserRole)
    
    // 应用用户角色的大模型配置到全局状态
    if (role.baseURL) {
      appState.llm.baseURL = role.baseURL
    }
    if (role.model) {
      appState.llm.model = role.model
    }
    appState.llm.apiKey = globalApiKey.value
    // 保存配置
  handleSaveConfig()
    // 步骤3.5：更新连接按钮可用状态
    const event = new CustomEvent('roleUpdated')
    window.dispatchEvent(event)
    // 时机3：切换当前角色时更新说话人列表
    updateSpeakerList()
    showToastMessage(`已切换到用户角色"${role.name || '(未命名)'}"`, 'success')
      } catch (error) {
    showToastMessage((error as Error).message, 'error')
  }
}

// 处理用户角色头像上传
async function handleUserRoleAvatarUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  
  if (!file) {
    return
  }
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    showToastMessage('请选择图片文件', 'error')
    return
  }
  
  // 检查文件大小（限制为50MB，支持8K高清图）
  if (file.size > 50 * 1024 * 1024) {
    showToastMessage('图片大小不能超过50MB', 'error')
    return
  }
  
  // 保存文件，准备裁剪
  pendingUploadFile.value = file
  isUserRoleUpload.value = true // 标识这是用户角色上传
  
  // 读取文件并显示裁剪弹窗
  const reader = new FileReader()
  reader.onload = (e) => {
    const result = e.target?.result as string
    if (result) {
      cropImageSrc.value = result
      showCropModal.value = true
      // 等待DOM更新后初始化裁剪器
      nextTick(() => {
        initCropper()
      })
    }
  }
  reader.onerror = () => {
    showToastMessage('读取图片失败', 'error')
  }
  reader.readAsDataURL(file)
  
  // 清空input，以便可以重复选择同一文件
  input.value = ''
}

// ========== 对话历史显示逻辑相关函数 ==========

// 获取当前用户角色信息（computed）
const currentUserRoleInfo = computed(() => {
  return appState.currentUserRole
})

// 获取当前伙伴角色信息（computed）
const currentPartnerRoleInfo = computed(() => {
  if (!appState.llm.apiKey) {
    return null
  }
  // 从 roles 列表中查找当前伙伴角色
  // 如果appState.llm.user已设置，使用它查找；否则返回null（不显示头像）
  if (!appState.llm.user) {
    return null
  }
  const role = roles.value.find(r => r.user === appState.llm.user) || null
  // 调试日志（仅在找不到角色时打印，避免过多日志）
  if (!role && roles.value.length > 0) {
    console.warn('未找到当前伙伴角色, appState.llm.user:', appState.llm.user, 'roles数量:', roles.value.length, '可用角色user字段:', roles.value.map(r => r.user))
  }
  return role
})

// 获取角色名称（用于对话历史显示）
function getRoleName(role: 'user' | 'assistant'): string {
  if (role === 'user') {
    // 用户角色：有名称显示名称，无名称显示"我"
    return currentUserRoleInfo.value?.name || '我'
  } else {
    // 伙伴角色：有名称显示名称，无名称使用 user 字段，都没有则显示"AI"
    const partnerRole = currentPartnerRoleInfo.value
    return partnerRole?.name || partnerRole?.user || 'AI'
      }
}

// 获取角色头像（用于对话历史显示）
function getRoleAvatar(role: 'user' | 'assistant'): string | null {
  if (role === 'user') {
    // 用户角色头像
    return currentUserRoleInfo.value?.avatar || null
  } else {
    // 伙伴角色头像
    const avatar = currentPartnerRoleInfo.value?.avatar || null
    // 调试日志
    if (!avatar && appState.llm.user) {
      console.log('伙伴角色头像为空, currentPartnerRoleInfo:', currentPartnerRoleInfo.value, 'appState.llm.user:', appState.llm.user, 'roles数量:', roles.value.length, 'roles列表:', roles.value.map(r => ({ user: r.user, name: r.name, avatar: r.avatar })))
    }
    return avatar
  }
}

// 获取角色头像URL（处理相对路径和绝对路径）
function getRoleAvatarUrl(role: 'user' | 'assistant'): string {
  const avatar = getRoleAvatar(role)
  if (!avatar) return ''
  
  // 如果是完整URL或绝对路径，直接返回
  if (avatar.startsWith('http') || avatar.startsWith('/')) {
    return avatar
  }
  // 如果是相对路径，添加服务器地址
  return `http://localhost:3001${avatar}`
}

// 切换角色显示（用于自动切换功能）
async function switchRoleDisplay(messageRole: 'user' | 'assistant') {
  if (messageRole === 'user') {
    // 显示用户角色，隐藏伙伴角色
    if (appState.currentUserRole) {
      if (appState.currentUserRole.type === 'digital_human') {
        appState.currentUserRole.showDigitalHuman = true
      } else {
        // 立绘显示逻辑
        showUserIllustration.value = true
      }
    }
    
    if (appState.currentPartnerRole) {
      if (appState.currentPartnerRole.type === 'digital_human') {
        appState.currentPartnerRole.showDigitalHuman = false
      } else {
        showPartnerIllustration.value = false
      }
    }
  } else {
    // 显示伙伴角色，隐藏用户角色
    if (appState.currentPartnerRole) {
      if (appState.currentPartnerRole.type === 'digital_human') {
        appState.currentPartnerRole.showDigitalHuman = true
      } else {
        showPartnerIllustration.value = true
      }
    }
    
    if (appState.currentUserRole) {
      if (appState.currentUserRole.type === 'digital_human') {
        appState.currentUserRole.showDigitalHuman = false
      } else {
        showUserIllustration.value = false
      }
    }
  }
}

// Toggle 立绘显示/隐藏
function toggleIllustration(role: 'user' | 'assistant') {
  if (role === 'user') {
    // 用户角色：根据角色类型判断
    const currentUserRole = currentUserRoleInfo.value
    if (currentUserRole?.type === 'digital_human') {
      // 数字人：检查是否已连接
      if (!currentUserRole.isConnected) {
        // 未连接：提示在角色面板连接
        showToastMessage('数字人未连接，请先在角色列表面板中连接', 'info')
    return
      }
      // 已连接：toggle 容器显示/隐藏（通过切换状态，让 watch 监听器处理）
      if (currentUserRole) {
        currentUserRole.showDigitalHuman = !currentUserRole.showDigitalHuman
      }
    } else {
      // 立绘：显示/隐藏（不修改立绘代码）
      showUserIllustration.value = !showUserIllustration.value
    }
  } else {
    // 伙伴角色：根据角色类型判断
    const partnerRole = currentPartnerRoleInfo.value
    if (partnerRole?.type === 'digital_human') {
      // 数字人：检查是否已连接
      if (!partnerRole.isConnected) {
        // 未连接：提示在角色面板连接
        showToastMessage('数字人未连接，请先在角色列表面板中连接', 'info')
        return
      }
      // 已连接：toggle 容器显示/隐藏（通过切换状态，让 watch 监听器处理）
      if (partnerRole) {
        partnerRole.showDigitalHuman = !partnerRole.showDigitalHuman
      }
    } else {
      // 立绘：显示/隐藏（不修改立绘代码）
      showPartnerIllustration.value = !showPartnerIllustration.value
    }
  }
}

// 获取 toggle 提示文本
function getToggleIllustrationTitle(role: 'user' | 'assistant'): string {
  if (role === 'user') {
    // 用户角色：根据角色类型判断
    const currentUserRole = currentUserRoleInfo.value
    if (currentUserRole?.type === 'digital_human') {
      if (!currentUserRole.isConnected) {
        return '显示数字人（未连接）'
      }
      return currentUserRole.showDigitalHuman ? '隐藏数字人' : '显示数字人'
    } else {
      return showUserIllustration.value ? '隐藏用户立绘' : '显示用户立绘'
    }
  } else {
    // 伙伴角色：根据角色类型判断
    const partnerRole = currentPartnerRoleInfo.value
    if (partnerRole?.type === 'digital_human') {
      if (!partnerRole.isConnected) {
        return '显示数字人（未连接）'
      }
      return partnerRole.showDigitalHuman ? '隐藏数字人' : '显示数字人'
    } else {
      return showPartnerIllustration.value ? '隐藏伙伴立绘' : '显示伙伴立绘'
    }
  }
}

// ==================== 角色激活/失活函数 ====================

// 激活用户角色（立绘或数字人）
async function activateUserRole(role: UserRole | null) {
  if (!role) return
  
  if (role.type === 'illustration') {
    // 激活用户立绘
    activateUserIllustration(role)
  } else if (role.type === 'digital_human') {
    // 激活用户数字人（不连接，只设置状态）
    activateUserDigitalHuman(role)
  }
}

// 失活用户角色（立绘或数字人）
async function deactivateUserRole(role: UserRole | null) {
  if (!role) return
  
  if (role.type === 'illustration') {
    // 失活用户立绘
    deactivateUserIllustration(role)
  } else if (role.type === 'digital_human') {
    // 失活用户数字人（断开连接，清理状态）
    await deactivateUserDigitalHuman(role)
  }
}

// 激活用户立绘
function activateUserIllustration(_role: UserRole) {
  // 设置立绘显示状态
  showUserIllustration.value = true
  // 其他立绘相关初始化（如果需要）
}

// 失活用户立绘
function deactivateUserIllustration(_role: UserRole) {
  // 隐藏立绘
  showUserIllustration.value = false
  // 其他立绘相关清理（如果需要）
}

// 激活用户数字人
function activateUserDigitalHuman(role: UserRole) {
  // 设置数字人显示状态（不连接，只设置状态）
  // 注意：激活时不连接SDK，连接需要用户点击"连接"按钮
  role.showDigitalHuman = true
  // 其他数字人相关初始化（如果需要）
}

// 失活用户数字人
async function deactivateUserDigitalHuman(role: UserRole) {
  const userRoleId = `user:${role.id}`
  const renderer = rendererManager.getRenderer(userRoleId)
  
  if (renderer) {
    // 断开连接
    if (renderer.disconnect) {
      await renderer.disconnect()
    }
    // 隐藏数字人
    role.showDigitalHuman = false
    // 清理状态
    role.digitalHumanInstance = null
    role.isConnected = false
    // 销毁渲染器
    rendererManager.destroyRenderer(userRoleId)
  } else {
    // 如果渲染器不存在，只清理显示状态
    role.showDigitalHuman = false
    role.isConnected = false
  }
}

// 激活伙伴角色（立绘或数字人）
async function activatePartnerRole(role: Role | null) {
  if (!role) return
  
  if (role.type === 'illustration') {
    // 激活伙伴立绘
    activatePartnerIllustration(role)
  } else if (role.type === 'digital_human') {
    // 激活伙伴数字人（不连接，只设置状态）
    activatePartnerDigitalHuman(role)
  }
}

// 失活伙伴角色（立绘或数字人）
async function deactivatePartnerRole(role: Role | null) {
  if (!role) return
  
  if (role.type === 'illustration') {
    // 失活伙伴立绘
    deactivatePartnerIllustration(role)
  } else if (role.type === 'digital_human') {
    // 失活伙伴数字人（断开连接，清理状态）
    await deactivatePartnerDigitalHuman(role)
  }
}

// 激活伙伴立绘
function activatePartnerIllustration(_role: Role) {
  // 设置立绘显示状态
  showPartnerIllustration.value = true
  // 其他立绘相关初始化（如果需要）
}

// 失活伙伴立绘
function deactivatePartnerIllustration(_role: Role) {
  // 隐藏立绘
  showPartnerIllustration.value = false
  // 其他立绘相关清理（如果需要）
}

// 激活伙伴数字人
function activatePartnerDigitalHuman(role: Role) {
  // 设置数字人显示状态（不连接，只设置状态）
  // 注意：激活时不连接SDK，连接需要用户点击"连接"按钮
  role.showDigitalHuman = true
  // 其他数字人相关初始化（如果需要）
}

// 失活伙伴数字人
async function deactivatePartnerDigitalHuman(role: Role) {
  const partnerRoleId = `partner:${role.user}`
  const renderer = rendererManager.getRenderer(partnerRoleId)
  
  if (renderer) {
    // 断开连接
    if (renderer.disconnect) {
      await renderer.disconnect()
    }
    // 隐藏数字人
    role.showDigitalHuman = false
    // 清理状态
    role.digitalHumanInstance = null
    role.isConnected = false
    // 销毁渲染器
    rendererManager.destroyRenderer(partnerRoleId)
  } else {
    // 如果渲染器不存在，只清理显示状态
    role.showDigitalHuman = false
    role.isConnected = false
  }
}

// ==================== 角色激活/失活函数结束 ====================

// 保存 TTS 和 ASR 设置
function handleSaveTtsAsrSettings() {
  const success = handleSaveConfig(true)
  if (success) {
    showTtsAsrSettingsModal.value = false
  }
}

// TTS设置页试听音色（toggle播放/停止）
async function previewTtsVoice() {
  // 如果正在播放，则停止
  if (isTtsPreviewPlaying.value && ttsPreviewAudio.value) {
    ttsPreviewAudio.value.pause()
    ttsPreviewAudio.value = null
    isTtsPreviewPlaying.value = false
    return
  }
  
  if (!appState.tts.apiKey) {
    showToastMessage('请先配置API Key', 'error')
    return
  }
  
  if (!ttsPreviewVoice.value) {
    showToastMessage('请先选择音色', 'error')
    return
  }
  
  const previewText = ttsPreviewText.value?.trim() || '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。'
  if (!previewText) {
    showToastMessage('请输入试听文本', 'error')
    return
  }

  try {
    console.log('开始TTS试听:', {
      voice: ttsPreviewVoice.value,
      text: previewText.substring(0, 50) + '...',
      speed: appState.tts.speed,
      volume: appState.tts.volume
    })
    
    const ttsConfig = {
      provider: appState.tts.provider || 'doubao',
      apiKey: appState.tts.apiKey,
      voice: ttsPreviewVoice.value,
      speed: appState.tts.speed || 1.0,
      volume: appState.tts.volume || 1.0
    }
    
    const ttsService = TtsServiceFactory.create(ttsConfig.provider)
    console.log('调用TTS服务合成音频...')
    const audioData = await ttsService.synthesize(previewText, ttsConfig)
    console.log('TTS合成成功，音频数据大小:', audioData.byteLength, 'bytes')
    
    // 播放试听音频
    const blob = new Blob([audioData], { type: 'audio/mpeg' })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    ttsPreviewAudio.value = audio
    
    // 设置播放完成和错误处理
    audio.onended = () => {
      console.log('试听播放完成')
      URL.revokeObjectURL(url)
      ttsPreviewAudio.value = null
      isTtsPreviewPlaying.value = false
    }
    
    audio.onerror = (error) => {
      console.error('试听音频播放失败:', error)
      URL.revokeObjectURL(url)
      ttsPreviewAudio.value = null
      isTtsPreviewPlaying.value = false
      showToastMessage('音频播放失败', 'error')
    }
    
    // 开始播放
    try {
      console.log('开始播放音频...')
      await audio.play()
      isTtsPreviewPlaying.value = true
      console.log('音频播放成功')
  } catch (error) {
      console.error('试听播放失败:', error)
      URL.revokeObjectURL(url)
      ttsPreviewAudio.value = null
      isTtsPreviewPlaying.value = false
      showToastMessage('播放失败: ' + (error instanceof Error ? error.message : String(error)), 'error')
    }
  } catch (error) {
    console.error('试听失败:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    console.error('错误详情:', error)
    showToastMessage('试听失败: ' + errorMessage, 'error')
  }
}

// 保存配置到 localStorage
function handleSaveConfig(showToast = false) {
  try {
    const config = {
      // 不再保存数字人的全局配置，每个角色独立配置
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
      },
      tts: {
        provider: appState.tts.provider,
        apiKey: appState.tts.apiKey,
        speed: appState.tts.speed,
        volume: appState.tts.volume
      },
      conversationMode: appState.conversationMode,
      autoExtractMarkdownImage: autoExtractMarkdownImage.value
    }
    
    const configJson = JSON.stringify(config)
    localStorage.setItem(CONFIG_STORAGE_KEY, configJson)
    
    // 验证保存是否成功
    const saved = localStorage.getItem(CONFIG_STORAGE_KEY)
    if (saved === configJson) {
      console.log('配置保存成功')
      if (showToast) {
        showToastMessage('配置已保存', 'success')
      }
      return true
    } else {
      throw new Error('配置保存验证失败')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    if (showToast) {
      showToastMessage('保存配置失败: ' + (error as Error).message, 'error')
    }
    return false
  }
}

// 从 localStorage 加载配置
function handleLoadConfig(showAlert = true) {
  try {
    const savedConfig = localStorage.getItem(CONFIG_STORAGE_KEY)
    if (!savedConfig) {
      if (showAlert) {
        showToastMessage('没有找到保存的配置', 'info')
      }
      return false
    }
    
    const config = JSON.parse(savedConfig)
    console.log('加载配置:', config)
    
    // 不再加载数字人的全局配置，每个角色独立配置
    
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
    
    // 加载Markdown图像提取开关
    if (config.autoExtractMarkdownImage !== undefined) {
      autoExtractMarkdownImage.value = config.autoExtractMarkdownImage
    }
    
    if (config.tts) {
      appState.tts.provider = config.tts.provider || 'doubao'
      appState.tts.apiKey = config.tts.apiKey || ''
      appState.tts.speed = config.tts.speed || 1.0
      appState.tts.volume = config.tts.volume || 1.0
    }
    
    // 加载对话模式
    if (config.conversationMode) {
      appState.conversationMode = config.conversationMode === 'speech' ? 'speech' : 'ai'
    }
    
    if (showAlert) {
      showToastMessage('配置已加载', 'success')
    }
    return true
  } catch (error) {
    console.error('加载配置失败:', error)
    if (showAlert) {
      showToastMessage('加载配置失败', 'error')
    }
    return false
  }
}

// 角色管理相关函数
async function handleOpenRoleManagement() {
  showRoleManagementModal.value = true
  showMenu.value = false
  
  // 注意：不在这里加载伙伴角色列表，因为：
  // 1. 登录时已经加载过了（handleLogin）
  // 2. 保存/删除/切换角色时会重新加载
  // 3. 打开面板只是为了显示，不需要重新加载和初始化，避免丢失连接状态
}

async function loadRoles() {
  // 伙伴角色应该基于登录的 globalApiKey 过滤，而不是 appState.llm.apiKey
  // 因为用户登录后，globalApiKey 才是真正的用户标识
  if (!globalApiKey.value || !globalApiKey.value.trim()) {
    showToastMessage('请先登录', 'error')
    roles.value = []
    return
  }
  
  try {
    // 使用 globalApiKey 作为 apiKey 参数，确保只显示当前登录用户的伙伴角色
    const roleList = await getRoles(globalApiKey.value)
    // 初始化每个角色的数字人相关属性
    roleList.forEach(role => {
      const partnerRoleId = `partner:${role.user}`
      // 初始化内存状态属性
      role.isConnecting = false
      role.isConnected = false
      role.showDigitalHuman = false
      role.digitalHumanInstance = null
      
      // 状态恢复：检查 rendererManager 是否存在渲染器
      const renderer = rendererManager.getRenderer(partnerRoleId)
      if (renderer && renderer instanceof DigitalHumanRenderer) {
        // 恢复连接状态
        role.isConnected = true
        role.showDigitalHuman = true
        const instance = renderer.getInstance()
        if (instance) {
          role.digitalHumanInstance = instance
        }
      }
    })
    roles.value = roleList
    console.log('伙伴角色列表加载成功:', roleList.length, '个角色, apiKey:', globalApiKey.value)
    // 验证隔离：检查所有角色的 user_id 是否都等于当前 apiKey（通过检查返回的数据结构）
    // 注意：前端无法直接访问 user_id，但可以通过其他方式验证
    // 如果发现异常，会在控制台输出警告
    if (roleList.length > 0) {
      console.log('伙伴角色详情:', roleList.map(r => ({ id: r.id, name: r.name, user: r.user })))
    }
    // 触发重新计算 currentPartnerRoleInfo
  } catch (error) {
    const errorMessage = (error as Error).message
    // 检查是否是网络错误
    if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
      showToastMessage('无法连接到后端服务，请确保后端服务已启动（npm run server）', 'error')
    } else {
      showToastMessage('加载角色列表失败: ' + errorMessage, 'error')
    }
    console.error('加载角色列表失败:', error)
    roles.value = []
  }
}

// 获取并设置当前伙伴角色
async function getAndSetCurrentPartnerRole() {
  if (!globalApiKey.value || roles.value.length === 0) {
    return false
  }
  
  // 1. 从localStorage恢复appState.llm.user（如果localStorage中有保存，且对应的伙伴角色存在）
  const savedConfig = localStorage.getItem(CONFIG_STORAGE_KEY)
  if (savedConfig) {
    try {
      const config = JSON.parse(savedConfig)
      if (config.llm && config.llm.user) {
        // 验证该user对应的伙伴角色是否存在
        const roleExists = roles.value.some(r => r.user === config.llm.user)
        if (roleExists) {
          appState.llm.user = config.llm.user
          // 同时设置 appState.currentPartnerRole
          const partnerRole = roles.value.find(r => r.user === config.llm.user) || null
          appState.currentPartnerRole = partnerRole
          // 激活伙伴角色
          if (partnerRole) {
            await activatePartnerRole(partnerRole)
          }
          console.log('已恢复当前伙伴角色:', config.llm.user)
          return true
        }
      }
    } catch (error) {
      console.error('恢复配置失败:', error)
    }
  }
  
  return false
}

function handleCreateRole() {
  editingRole.value = null
  // 创建时默认使用当前用户角色的模型名称和 API Key
  const defaultType = 'illustration' as 'digital_human' | 'illustration'
  const defaultUseDigitalHumanVoice = true
  roleForm.value = {
    name: '',
    user: '',
    type: defaultType,
    description: '',
    avatar: '',
    positionX: 80,
    positionY: 50,
    scale: 0.7,
    baseURL: '', // 不显示在界面，后台自动使用用户角色的 baseURL
    model: appState.currentUserRole?.model || '', // 默认使用当前用户角色的模型名称
    apiKey: globalApiKey.value || '', // 默认使用当前登录的 API Key
    avatarAppId: '',
    avatarAppSecret: '',
    useDigitalHumanVoice: defaultUseDigitalHumanVoice,
    ttsProvider: 'doubao',
    ttsVoice: '',
    ttsSpeed: appState.tts.speed ?? 1.0,
    ttsVolume: appState.tts.volume ?? 1.0,
    ttsPreviewText: '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
    enableVoicePlay: false,
    enableAutoPlay: false,
    enableAutoSwitch: false
  }
  showRoleEditForm.value = true
}

function handleEditRole(role: Role) {
  editingRole.value = role
  roleForm.value = {
    name: role.name || '',
    user: role.user,
    type: role.type || 'illustration',
    description: role.description || '',
    avatar: role.avatar || '',
    positionX: role.positionX !== undefined ? role.positionX : 80,
    positionY: role.positionY !== undefined ? role.positionY : 50,
    scale: role.scale !== undefined ? role.scale : (role.type === 'illustration' ? 0.7 : 1.0),
    baseURL: role.baseURL || '',
    model: role.model || '',
    apiKey: role.apiKey || '',
    avatarAppId: role.avatarAppId || '',
    avatarAppSecret: role.avatarAppSecret || '',
    useDigitalHumanVoice: role.useDigitalHumanVoice !== undefined ? role.useDigitalHumanVoice : true,
    ttsProvider: role.ttsProvider || 'doubao',
    ttsVoice: role.ttsVoice || '',
    ttsSpeed: role.ttsSpeed !== undefined ? role.ttsSpeed : (appState.tts.speed ?? 1.0),
    ttsVolume: role.ttsVolume !== undefined ? role.ttsVolume : (appState.tts.volume ?? 1.0),
    ttsPreviewText: (role as any).ttsPreviewText || '欢迎来到AI伴侣小世界！这是一个智能对话平台，支持数字人和立绘两种角色类型，可以与AI进行自然流畅的对话交流。',
    enableVoicePlay: role.enableVoicePlay !== undefined ? role.enableVoicePlay : false,
    enableAutoPlay: role.enableAutoPlay !== undefined ? role.enableAutoPlay : false,
    enableAutoSwitch: role.enableAutoSwitch !== undefined ? role.enableAutoSwitch : false
  }
  showRoleEditForm.value = true
}

async function handleSaveRole() {
  if (!roleForm.value.user.trim()) {
    showToastMessage('user字段不能为空', 'error')
    return
  }
  
  // 模型名称为必填
  if (!roleForm.value.model || !roleForm.value.model.trim()) {
    showToastMessage('模型名称不能为空', 'error')
    return
  }
  
  try {
    // 创建时：baseURL 默认使用当前用户角色的 baseURL（不显示在界面，后台直接使用）
    // 更新时：使用伙伴角色自己的 baseURL（如果已设置）
    const baseURL = editingRole.value 
      ? (editingRole.value.baseURL || appState.currentUserRole?.baseURL || undefined)
      : (appState.currentUserRole?.baseURL || undefined)
    
    // 判断是创建还是编辑：如果 editingRole.value 存在且 id > 0，才是编辑模式
    // 如果 id === 0，说明是创建新角色时连接数字人创建的临时对象，应该按创建模式处理
    if (editingRole.value && editingRole.value.id > 0) {
      // 更新角色
      const oldRole = roles.value.find(r => r.id === editingRole.value!.id)
      const typeChanged = oldRole?.type !== roleForm.value.type
      
      // 如果类型从数字人改为立绘，需要清理数字人状态
      if (typeChanged && oldRole?.type === 'digital_human') {
        const partnerRoleId = `partner:${oldRole.user}`
        const renderer = rendererManager.getRenderer(partnerRoleId)
        if (renderer) {
          if (renderer.disconnect) {
            await renderer.disconnect()
          }
          rendererManager.destroyRenderer(partnerRoleId)
        }
        // 清理内存状态属性
        oldRole.isConnected = false
        oldRole.showDigitalHuman = false
        oldRole.digitalHumanInstance = null
        oldRole.isConnecting = false
      }
      
      // 更新数据库
      const updatedRole = await updateRole(
        editingRole.value.id,
        globalApiKey.value,
        {
          name: roleForm.value.name.trim() || undefined,
          user: roleForm.value.user.trim(), // 角色的user字段（传给大模型，必填）
          type: roleForm.value.type,
          description: roleForm.value.description.trim() || undefined,
          avatar: roleForm.value.avatar && roleForm.value.avatar.trim() ? roleForm.value.avatar.trim() : undefined,
          positionX: roleForm.value.positionX,
          positionY: roleForm.value.positionY,
          scale: roleForm.value.scale,
          baseURL: baseURL, // 使用伙伴角色自己的 baseURL（如果已设置，否则使用用户角色的）
          model: roleForm.value.model.trim(), // 模型名称必填
          apiKey: globalApiKey.value, // 使用当前登录的 API Key
          avatarAppId: roleForm.value.avatarAppId && roleForm.value.avatarAppId.trim() ? roleForm.value.avatarAppId.trim() : undefined,
          avatarAppSecret: roleForm.value.avatarAppSecret && roleForm.value.avatarAppSecret.trim() ? roleForm.value.avatarAppSecret.trim() : undefined,
          useDigitalHumanVoice: roleForm.value.useDigitalHumanVoice !== undefined ? roleForm.value.useDigitalHumanVoice : undefined,
          ttsProvider: roleForm.value.ttsProvider !== undefined && roleForm.value.ttsProvider !== null && roleForm.value.ttsProvider !== '' ? roleForm.value.ttsProvider : undefined,
          ttsVoice: roleForm.value.ttsVoice !== undefined && roleForm.value.ttsVoice !== null && roleForm.value.ttsVoice !== '' ? roleForm.value.ttsVoice : undefined,
          ttsSpeed: roleForm.value.ttsSpeed !== undefined ? roleForm.value.ttsSpeed : undefined,
          ttsVolume: roleForm.value.ttsVolume !== undefined ? roleForm.value.ttsVolume : undefined,
          ttsPreviewText: roleForm.value.ttsPreviewText !== undefined && roleForm.value.ttsPreviewText !== null && roleForm.value.ttsPreviewText !== '' ? roleForm.value.ttsPreviewText : undefined,
          enableVoicePlay: roleForm.value.enableVoicePlay !== undefined ? roleForm.value.enableVoicePlay : undefined,
          enableAutoPlay: roleForm.value.enableAutoPlay !== undefined ? roleForm.value.enableAutoPlay : undefined,
          enableAutoSwitch: roleForm.value.enableAutoSwitch !== undefined ? roleForm.value.enableAutoSwitch : undefined
        }
      )
      
      // 只更新那个角色的属性，不重新加载所有角色
      const roleIndex = roles.value.findIndex(r => r.id === editingRole.value!.id)
      if (roleIndex !== -1) {
        // 更新数据库属性
        Object.assign(roles.value[roleIndex], updatedRole)
        // 如果类型未变更，保持内存状态属性；如果类型变更，已在上面清理
        if (!typeChanged && oldRole) {
          // 保持原有的内存状态属性
          roles.value[roleIndex].isConnecting = oldRole.isConnecting
          roles.value[roleIndex].isConnected = oldRole.isConnected
          roles.value[roleIndex].showDigitalHuman = oldRole.showDigitalHuman
          roles.value[roleIndex].digitalHumanInstance = oldRole.digitalHumanInstance
        } else if (typeChanged && roleForm.value.type === 'digital_human') {
          // 从立绘改为数字人：初始化数字人属性
          roles.value[roleIndex].isConnecting = false
          roles.value[roleIndex].isConnected = false
          roles.value[roleIndex].showDigitalHuman = false
          roles.value[roleIndex].digitalHumanInstance = null
        }
        
        // 如果更新的是当前角色，更新引用（保持引用不变，只更新属性）
        if (appState.currentPartnerRole?.id === editingRole.value.id) {
          appState.currentPartnerRole = roles.value[roleIndex]
        }
      }
      
      showToastMessage('角色已更新', 'success')
    } else {
      // 创建角色：baseURL 默认使用用户角色的 baseURL
      const newRole = await createRole(
        globalApiKey.value,
        {
          name: roleForm.value.name.trim() || undefined,
          user: roleForm.value.user.trim(), // 角色的user字段（传给大模型，必填）
          type: roleForm.value.type,
          description: roleForm.value.description.trim() || undefined,
          avatar: roleForm.value.avatar && roleForm.value.avatar.trim() ? roleForm.value.avatar.trim() : undefined,
          positionX: roleForm.value.positionX,
          positionY: roleForm.value.positionY,
          scale: roleForm.value.scale,
          baseURL: baseURL, // 创建时默认使用用户角色的 baseURL
          model: roleForm.value.model.trim(), // 模型名称必填
          apiKey: globalApiKey.value, // 使用当前登录的 API Key
          avatarAppId: roleForm.value.avatarAppId && roleForm.value.avatarAppId.trim() ? roleForm.value.avatarAppId.trim() : undefined,
          avatarAppSecret: roleForm.value.avatarAppSecret && roleForm.value.avatarAppSecret.trim() ? roleForm.value.avatarAppSecret.trim() : undefined,
          useDigitalHumanVoice: roleForm.value.useDigitalHumanVoice !== undefined ? roleForm.value.useDigitalHumanVoice : undefined,
          ttsProvider: roleForm.value.ttsProvider !== undefined && roleForm.value.ttsProvider !== null && roleForm.value.ttsProvider !== '' ? roleForm.value.ttsProvider : undefined,
          ttsVoice: roleForm.value.ttsVoice !== undefined && roleForm.value.ttsVoice !== null && roleForm.value.ttsVoice !== '' ? roleForm.value.ttsVoice : undefined,
          ttsSpeed: roleForm.value.ttsSpeed !== undefined ? roleForm.value.ttsSpeed : undefined,
          ttsVolume: roleForm.value.ttsVolume !== undefined ? roleForm.value.ttsVolume : undefined,
          ttsPreviewText: roleForm.value.ttsPreviewText !== undefined && roleForm.value.ttsPreviewText !== null && roleForm.value.ttsPreviewText !== '' ? roleForm.value.ttsPreviewText : undefined,
          enableVoicePlay: roleForm.value.enableVoicePlay !== undefined ? roleForm.value.enableVoicePlay : undefined,
          enableAutoPlay: roleForm.value.enableAutoPlay !== undefined ? roleForm.value.enableAutoPlay : undefined,
          enableAutoSwitch: roleForm.value.enableAutoSwitch !== undefined ? roleForm.value.enableAutoSwitch : undefined
        }
      )
      
      // 初始化内存状态属性
      newRole.isConnecting = false
      newRole.isConnected = false
      newRole.showDigitalHuman = false
      newRole.digitalHumanInstance = null
      
      // 只添加新角色到列表，不重新加载所有角色
      roles.value.push(newRole)
      
      showToastMessage('角色已创建', 'success')
      
      // 如果当前伙伴角色为空，自动设置为当前角色
      if (!appState.llm.user) {
        appState.llm.user = roleForm.value.user.trim()
        appState.currentPartnerRole = newRole
        // 激活新创建的伙伴角色
        await activatePartnerRole(newRole)
        handleSaveConfig()
        // 触发角色更新事件
        const event = new CustomEvent('roleUpdated')
        window.dispatchEvent(event)
        // 更新说话人列表
        updateSpeakerList()
        console.log('自动设置第一个伙伴角色为当前:', appState.llm.user)
      }
    }
    
    // 清理临时对象（如果是创建新角色时连接数字人创建的临时对象）
    if (editingRole.value && editingRole.value.id === 0) {
      editingRole.value = null
    }
    
    showRoleEditForm.value = false
    
    // 如果创建了伙伴角色并设置为当前，加载对应的历史记录
    if (!editingRole.value && appState.llm.user) {
      await loadHistory()
    }
    
    // 如果保存的是当前使用的角色，重新加载当前角色信息以更新显示
    if (appState.llm.user === roleForm.value.user) {
      // 触发AvatarRender重新加载角色
      const event = new CustomEvent('roleUpdated')
      window.dispatchEvent(event)
    }
  } catch (error) {
    const errorMsg = (error as Error).message
    console.error('保存角色失败:', error)
    // 检查是否是图片数据过大
    if (roleForm.value.avatar && roleForm.value.avatar.length > 1000000) {
      showToastMessage('图片数据过大，请使用较小的图片或使用URL', 'error')
    } else {
      showToastMessage('保存失败: ' + errorMsg, 'error')
    }
  }
}

function handleCancelRoleEdit() {
  showRoleEditForm.value = false
  editingRole.value = null
}

async function handleDeleteRole(role: Role) {
  if (!confirm(`确定要删除角色"${role.name || role.user}"吗？`)) {
    return
  }
  
  try {
    const partnerRoleId = `partner:${role.user}`
    const renderer = rendererManager.getRenderer(partnerRoleId)
    
    // 如果角色已连接，先断开连接和销毁渲染器
    if (renderer) {
      if (renderer.disconnect) {
        await renderer.disconnect()
      }
      rendererManager.destroyRenderer(partnerRoleId)
    }
    
    // 如果删除的是当前角色，先失活
    if (appState.currentPartnerRole?.user === role.user) {
      await deactivatePartnerRole(role)
      appState.currentPartnerRole = null
      appState.llm.user = ''
      showToastMessage('已清空当前角色', 'info')
    }
    
    // 删除数据库记录
    await deleteRole(role.id, globalApiKey.value)
    
    // 只从列表中移除那个角色，不重新加载所有角色
    roles.value = roles.value.filter(r => r.id !== role.id)
    
    showToastMessage('角色已删除', 'success')
  } catch (error) {
    showToastMessage((error as Error).message, 'error')
  }
}

// 设置当前伙伴角色（时机2：伙伴角色设置或切换为当前时）
async function handleSetCurrentRole(role: Role) {
  // 步骤3.1：失活旧角色（清理旧角色的所有状态）
  if (appState.currentPartnerRole) {
    await deactivatePartnerRole(appState.currentPartnerRole)
  }
  
  // 步骤3.2：设置当前角色（直接设置，不需要调用API）
  appState.llm.user = role.user
  
  // 步骤3.3：不需要重新加载（伙伴角色没有 isCurrent 字段）
  // 更新当前角色标识（记录当前角色）
  const roleInList = roles.value.find(r => r.id === role.id)
  if (roleInList) {
    appState.currentPartnerRole = roleInList
  } else {
    appState.currentPartnerRole = role
  }
  
  // 步骤3.4.1：激活新角色（设置新角色的状态）
  await activatePartnerRole(appState.currentPartnerRole)
  
  // 应用角色的大模型配置（如果角色有配置则使用，否则保持当前配置）
  if (role.baseURL !== undefined && role.baseURL !== null && role.baseURL.trim()) {
    appState.llm.baseURL = role.baseURL
  }
  if (role.model !== undefined && role.model !== null && role.model.trim()) {
    appState.llm.model = role.model
  }
  if (role.apiKey !== undefined && role.apiKey !== null && role.apiKey.trim()) {
    appState.llm.apiKey = role.apiKey
  }
  
  // 保存配置，确保刷新页面后角色仍然生效
  handleSaveConfig()
  
  // 切换当前伙伴角色时，同时切换历史记录（历史记录与伙伴角色绑定）
  await loadHistory()
  
  // 步骤3.5：更新连接按钮可用状态
  const event = new CustomEvent('roleUpdated')
  window.dispatchEvent(event)
  
  // 时机3：切换当前角色时更新说话人列表
  updateSpeakerList()
  
  showToastMessage(`已切换到角色"${role.name || role.user}"`, 'success')
}

// 处理头像上传
async function handleAvatarUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  
  if (!file) {
    return
  }
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    showToastMessage('请选择图片文件', 'error')
    return
  }
  
  // 检查文件大小（限制为50MB，支持8K高清图）
  if (file.size > 50 * 1024 * 1024) {
    showToastMessage('图片大小不能超过50MB', 'error')
    return
  }
  
  // 保存文件，准备裁剪
  pendingUploadFile.value = file
  isUserRoleUpload.value = false // 标识这是伙伴角色上传
  
  // 读取文件并显示裁剪弹窗
  const reader = new FileReader()
  reader.onload = (e) => {
    const result = e.target?.result as string
    if (result) {
      cropImageSrc.value = result
      showCropModal.value = true
      // 等待DOM更新后初始化裁剪器
      nextTick(() => {
        initCropper()
      })
    }
  }
  reader.onerror = () => {
    showToastMessage('读取图片失败', 'error')
  }
  reader.readAsDataURL(file)
  
  // 清空input，以便可以重复选择同一文件
  input.value = ''
}

// 初始化裁剪器
function initCropper() {
  if (!cropImageRef.value) return
  
  // 如果已有实例，先销毁
  if (cropperInstance.value) {
    cropperInstance.value.destroy()
    cropperInstance.value = null
  }
  
  // 创建新的裁剪器实例（配置与 SillyTavern 一致）
  cropperInstance.value = new Cropper(cropImageRef.value, {
    aspectRatio: 2 / 3, // 宽高比 2:3（默认值，与 SillyTavern 一致）
    autoCropArea: 1, // 自动裁剪区域（与 SillyTavern 一致）
    viewMode: 2, // 限制裁剪框不能超出图片（与 SillyTavern 一致）
    rotatable: false, // 不允许旋转（与 SillyTavern 一致）
    scalable: true, // 允许缩放图片
    zoomable: true, // 允许缩放
    cropBoxMovable: true, // 允许移动裁剪框
    cropBoxResizable: true, // 允许调整裁剪框大小
  })
}

// 确认裁剪并上传
async function confirmCrop() {
  if (!cropperInstance.value || !pendingUploadFile.value) {
    return
  }
  
  try {
    // 获取裁剪后的canvas
    const canvas = cropperInstance.value.getCroppedCanvas({
      width: 512,
      height: 768,
      imageSmoothingEnabled: true,
      imageSmoothingQuality: 'high'
    })
    
    // 将canvas转换为blob（使用PNG格式以保留透明背景）
    canvas.toBlob(async (blob) => {
      if (!blob) {
        showToastMessage('裁剪失败', 'error')
        return
      }
      
      try {
        // 创建FormData并上传
        const formData = new FormData()
        // 使用PNG格式，保留原始文件名但改为.png扩展名
        const fileName = (pendingUploadFile.value?.name || 'avatar').replace(/\.[^/.]+$/, '') + '.png'
        formData.append('avatar', blob, fileName)
        
        const response = await fetch('http://localhost:3001/api/upload/avatar', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: '上传失败' }))
          throw new Error(error.error || '上传失败')
        }
        
        const result = await response.json()
        // 根据上传类型保存图片URL（相对路径，前端会自动转换为完整URL）
        if (isUserRoleUpload.value) {
          userRoleForm.value.avatar = result.url
        } else {
          roleForm.value.avatar = result.url
        }
        showToastMessage('图片上传成功', 'success')
        
        // 关闭裁剪弹窗
        closeCropModal()
      } catch (error) {
        console.error('上传图片失败:', error)
        showToastMessage('上传图片失败: ' + (error as Error).message, 'error')
      }
    }, 'image/png', 1.0)
  } catch (error) {
    console.error('裁剪失败:', error)
    showToastMessage('裁剪失败', 'error')
  }
}

// 关闭裁剪弹窗
function closeCropModal() {
  showCropModal.value = false
  if (cropperInstance.value) {
    cropperInstance.value.destroy()
    cropperInstance.value = null
  }
  cropImageSrc.value = ''
  pendingUploadFile.value = null
  isUserRoleUpload.value = false // 重置上传类型标识
}

// 处理头像URL输入
function handleAvatarUrlInput() {
  // URL输入时，如果已经有base64图片，清空base64（优先使用URL）
  // 这里不做处理，让用户自己选择
}

// 点击外部关闭菜单
function handleClickOutside(event: MouseEvent) {
  if (showMenu.value && menuPopupRef.value && inputWrapperRef.value) {
    const target = event.target as Node
    const menuBtn = inputWrapperRef.value.querySelector('.menu-btn')
    if (!menuPopupRef.value.contains(target) && 
        menuBtn && !menuBtn.contains(target)) {
      showMenu.value = false
    }
  }
}

// 开始拖动调整高度
function startResize(e: MouseEvent) {
  isResizing.value = true
  const startY = e.clientY
  const startHeight = historyPanelHeight.value
  
  function onMouseMove(e: MouseEvent) {
    if (!isResizing.value) return
    const deltaY = startY - e.clientY // 向上拖动增加高度
    const newHeight = Math.max(200, Math.min(800, startHeight + deltaY)) // 限制在200-800px之间
    historyPanelHeight.value = newHeight
    // 保存到localStorage
    localStorage.setItem('historyPanelHeight', newHeight.toString())
  }
  
  function onMouseUp() {
    isResizing.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  e.preventDefault()
}

// 组件挂载时自动加载配置（静默加载，不显示提示）
onMounted(() => {
  handleLoadConfig(false)
  // 加载面板高度
  const savedHeight = localStorage.getItem('historyPanelHeight')
  if (savedHeight) {
    historyPanelHeight.value = parseInt(savedHeight, 10)
  }
  // 如果没有配置autoExtractMarkdownImage，默认为true
  if (autoExtractMarkdownImage.value === undefined) {
    autoExtractMarkdownImage.value = true
  }
  // 只有在登录后才加载对话历史
  // loadHistory() 将在登录后调用
  // 初始化输入框高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = `${textareaRef.value.scrollHeight}px`
  }
  // 添加全局点击事件监听
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.config-panel {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  overflow: hidden;
  position: relative;
  z-index: 1;
}


/* 对话页面样式 - SillyTavern 风格，居中布局 */
.chat-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  width: 100%;
  position: relative;
}


/* 历史对话面板容器 */
.history-panel-wrapper {
  position: fixed;
  bottom: 65px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 800px;
  width: calc(100% - 40px);
  z-index: 999;
}

/* 历史对话面板 */
.history-panel {
  width: 100%;
  min-height: 200px;
  max-height: 800px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.history-panel-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.history-panel-close:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}

.history-panel-close:active {
  transform: scale(0.95);
}

.history-panel-close svg {
  width: 16px;
  height: 16px;
}

.history-panel-resize-handle {
  height: 8px;
  background: rgba(0, 0, 0, 0.1);
  cursor: ns-resize;
  flex-shrink: 0;
  position: relative;
  transition: background 0.2s;
}

.history-panel-resize-handle:hover {
  background: rgba(0, 123, 255, 0.3);
}

.history-panel-resize-handle::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 4px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 2px;
}

.history-list {
  overflow-y: auto;
  flex: 1;
  padding: 12px;
  min-height: 0;
}

.history-item {
  display: flex;
  flex-direction: column;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.history-item.user {
  align-self: flex-end;
  background: rgba(0, 123, 255, 0.1);
  border: 1px solid rgba(0, 123, 255, 0.2);
}

.history-item.assistant {
  align-self: flex-start;
  background: rgba(245, 245, 245, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.history-role-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  border: 2px solid rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.history-role-avatar:hover {
  border-color: rgba(0, 123, 255, 0.5);
  transform: scale(1.1);
}

.role-avatar-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  user-select: none;
  -webkit-user-drag: none;
}

.history-role-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  flex: 1;
}

.history-item-actions {
  display: flex;
  gap: 2px;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover .history-item-actions {
  opacity: 1;
}

.history-action-btn {
  width: 22px;
  height: 22px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0, 0, 0, 0.4);
  transition: all 0.15s;
  padding: 0;
  flex-shrink: 0;
}

.history-action-btn:hover {
  color: rgba(0, 0, 0, 0.7);
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.history-action-btn:active {
  transform: scale(0.9);
  color: rgba(0, 0, 0, 0.5);
}

.history-action-btn svg {
  width: 14px;
  height: 14px;
}

.history-edit-area {
  margin-top: 8px;
}

.history-edit-textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}

.history-edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.history-edit-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.history-edit-btn.save {
  background: #007bff;
  color: white;
}

.history-edit-btn.save:hover {
  background: #0056b3;
}

.history-edit-btn.cancel {
  background: rgba(0, 0, 0, 0.1);
  color: #666;
  }

.history-edit-btn.cancel:hover {
  background: rgba(0, 0, 0, 0.15);
}

.history-content {
  font-size: 13px;
  color: #333;
  line-height: 1.6;
  word-break: break-word;
}

.history-content :deep(p) {
  margin: 0.5em 0;
}

.history-content :deep(p:first-child) {
  margin-top: 0;
}

.history-content :deep(p:last-child) {
  margin-bottom: 0;
}

.history-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.history-content :deep(pre) {
  background: rgba(0, 0, 0, 0.05);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.history-content :deep(pre code) {
  background: none;
  padding: 0;
}

.history-content :deep(strong) {
  font-weight: 600;
}

.history-content :deep(em) {
  font-style: italic;
}

.history-content :deep(ul),
.history-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.history-content :deep(li) {
  margin: 0.25em 0;
}

.history-content :deep(blockquote) {
  border-left: 3px solid rgba(0, 0, 0, 0.2);
  padding-left: 1em;
  margin: 0.5em 0;
  color: #666;
}

.history-content :deep(a) {
  color: #007bff;
  text-decoration: none;
}

.history-content :deep(a:hover) {
  text-decoration: underline;
}

.history-content :deep(h1),
.history-content :deep(h2),
.history-content :deep(h3),
.history-content :deep(h4),
.history-content :deep(h5),
.history-content :deep(h6) {
  margin: 0.8em 0 0.4em 0;
  font-weight: 600;
}

.history-content :deep(h1) { font-size: 1.5em; }
.history-content :deep(h2) { font-size: 1.3em; }
.history-content :deep(h3) { font-size: 1.1em; }
.history-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin: 1em 0;
}

.history-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.history-content :deep(thead) {
  background: rgba(0, 0, 0, 0.05);
}

.history-content :deep(tbody) {
  background: rgba(255, 255, 255, 0.5);
}

.history-content :deep(tr) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.history-content :deep(tr:last-child) {
  border-bottom: none;
}

.history-content :deep(th),
.history-content :deep(td) {
  border: 1px solid rgba(0, 0, 0, 0.2);
  padding: 8px 12px;
  text-align: left;
}

.history-content :deep(th) {
  font-weight: 600;
  background: rgba(0, 0, 0, 0.05);
}

.history-empty {
  text-align: center;
  color: rgba(153, 153, 153, 0.8);
  padding: 40px 20px;
  font-size: 14px;
}

.chat-input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
  z-index: 1000;
  background: transparent;
}


/* 大模型风格输入框 - 居中布局，最小化遮挡 */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 20px;
  padding: 4px 8px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  max-width: 800px;
  width: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  z-index: 100;
}

.input-wrapper:focus-within {
  border-color: rgba(0, 123, 255, 0.3);
  box-shadow: 0 2px 12px rgba(0, 123, 255, 0.15);
}

/* 说话人选择器（演讲模式，内联显示） */
.speaker-selector-inline {
  flex-shrink: 0;
}

.speaker-select {
  padding: 4px 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  color: #333;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
  min-width: 100px;
  max-width: 150px;
}

.speaker-select:hover:not(:disabled) {
  border-color: rgba(0, 123, 255, 0.3);
  background: rgba(255, 255, 255, 1);
}

.speaker-select:focus {
  border-color: rgba(0, 123, 255, 0.5);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.speaker-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.05);
}

.menu-btn {
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
  color: #666;
}

.menu-btn:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
  transform: scale(1.1);
}

.menu-btn.active {
  opacity: 1;
  background: rgba(0, 123, 255, 0.1);
  color: #007bff;
}

.menu-popup {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  min-width: 200px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 3000;
  padding: 4px 0;
  max-height: 400px;
  overflow-y: auto;
}

.menu-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
}

.menu-item:hover:not(.disabled) {
  background: rgba(0, 0, 0, 0.05);
}

.menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  color: #999;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
}

.menu-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.menu-arrow {
  font-size: 10px;
  color: #999;
  transition: transform 0.2s;
}

.menu-arrow.expanded {
  transform: rotate(90deg);
}

.menu-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 4px 0;
}

.submenu {
  background: rgba(0, 0, 0, 0.02);
  padding-left: 8px;
}

.submenu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  transition: background 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submenu-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.submenu-level2 {
  background: rgba(0, 0, 0, 0.03);
  padding-left: 16px;
}

.submenu-level2 .submenu-item {
  padding-left: 24px;
  font-size: 12px;
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
  padding: 4px 2px;
  background: transparent;
  color: #333;
  font-family: inherit;
  min-height: 20px;
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

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.config-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.config-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 20px 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.8);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: rgba(0, 123, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.form-group input[type="range"] {
  padding: 0;
  height: 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
  -webkit-appearance: none;
  appearance: none;
}

.form-group input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: #007bff;
  border-radius: 50%;
  cursor: pointer;
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
  transition: color 0.2s;
}

.toggle-visibility:hover {
  color: #007bff;
}

.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
  font-style: italic;
}

/* 勾选项和单选框样式 */
.form-group label[style*="display: flex"] {
  display: flex !important;
  align-items: center;
  gap: 8px;
  margin-bottom: 0 !important;
  cursor: pointer;
  padding: 6px 0;
  font-weight: normal;
}

.form-group label[style*="display: flex"] input[type="checkbox"],
.form-group label[style*="display: flex"] input[type="radio"] {
  width: auto !important;
  margin: 0;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  height: auto;
  border: none;
  box-shadow: none;
  background: transparent;
}

.form-group label[style*="display: flex"] input[type="checkbox"]:focus,
.form-group label[style*="display: flex"] input[type="radio"]:focus {
  outline: 2px solid rgba(0, 123, 255, 0.5);
  outline-offset: 2px;
  box-shadow: none;
}

.form-group label[style*="display: flex"] span {
  flex: 1;
  user-select: none;
  line-height: 1.5;
}

/* 单选框组：第二个选项的间距 */
.form-group label[style*="display: flex"][style*="margin-top"] {
  margin-top: 8px;
}

/* 勾选项组：减少 form-group 的间距 */
.form-group:has(label[style*="display: flex"]) {
  margin-bottom: 8px;
}

/* 兼容性：如果没有 :has() 支持，使用更具体的选择器 */
.form-group > label[style*="display: flex"] {
  margin-bottom: 0;
}

.form-group > label[style*="display: flex"] + .form-hint {
  margin-top: 2px;
}

.text-warning {
  color: #ff6b6b !important;
  font-weight: 500;
}

.api-key-mismatch,
.model-mismatch {
  border-color: #ff6b6b !important;
  background-color: #fff5f5 !important;
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
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: rgba(0, 123, 255, 0.9);
  color: white;
  border-color: rgba(0, 123, 255, 0.3);
}

.btn-primary:hover:not(:disabled) {
  background: rgba(0, 86, 179, 0.95);
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(108, 117, 125, 0.9);
  color: white;
  border-color: rgba(108, 117, 125, 0.3);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(84, 91, 98, 0.95);
  transform: translateY(-1px);
}

.button-group {
  display: flex;
  gap: 12px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: #555;
}

.status-indicator {
  font-size: 14px;
  color: #999;
}

.status-indicator.connected {
  color: #28a745;
}

/* Toast 提示框 */
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  min-width: 200px;
  max-width: 400px;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  animation: toastSlideIn 0.3s ease-out;
}

.toast.success {
  background: rgba(40, 167, 69, 0.95);
  color: white;
}

.toast.error {
  background: rgba(220, 53, 69, 0.95);
  color: white;
}

.toast.info {
  background: rgba(0, 123, 255, 0.95);
  color: white;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.toast-icon {
  flex-shrink: 0;
  stroke: currentColor;
}

.toast-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
}

.toast-enter-active {
  animation: toastSlideIn 0.3s ease-out;
}

.toast-leave-active {
  animation: toastSlideOut 0.3s ease-in;
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

@keyframes toastSlideOut {
  from {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  to {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.tab-button {
  padding: 10px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -1px;
}

.tab-button:hover {
  color: #333;
}

.tab-button.active {
  color: #007bff;
  border-bottom-color: #007bff;
}

.tab-content {
  min-height: 200px;
}

/* 角色管理样式 */
.role-edit-form {
  padding: 20px 0;
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-item {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.9);
  transition: all 0.2s;
}

.role-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.role-item.current-role {
  border-color: rgba(0, 123, 255, 0.5);
  background: rgba(0, 123, 255, 0.05);
}

.role-item-content {
  margin-bottom: 12px;
}

.role-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.role-item-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-type-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: normal;
  margin-left: 8px;
}

.role-type-badge.digital_human {
  background: rgba(40, 167, 69, 0.2);
  color: rgba(40, 167, 69, 0.9);
}

.role-type-badge.illustration {
  background: rgba(255, 193, 7, 0.2);
  color: rgba(255, 193, 7, 0.9);
}

.current-badge {
  background: rgba(0, 123, 255, 0.9);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: normal;
}

.role-item-user {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.role-item-description {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
  line-height: 1.5;
}

.role-item-avatar {
  margin-top: 8px;
}

.role-item-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-small {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-danger {
  background: rgba(220, 53, 69, 0.9);
  color: white;
}

.btn-danger:hover {
  background: rgba(220, 53, 69, 1);
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 头像上传样式 */
.avatar-upload-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.avatar-preview-row {
  display: flex;
  flex-direction: row;
  gap: 12px;
  align-items: flex-start;
}

.avatar-preview-wrapper {
  flex-shrink: 0;
}

.avatar-preview {
  position: relative;
  display: inline-block;
  width: 120px;
  height: 120px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
  transition: background 0.2s;
}

.avatar-remove-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.avatar-upload-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  border: 2px dashed rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.02);
}

.avatar-url-input {
  width: 100%;
}

.avatar-url-input input {
  width: 100%;
}

/* 数字人预览容器 */
.digital-human-preview-container {
  position: relative;
  width: 120px;
  height: 120px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.digital-human-preview {
  width: 100%;
  height: 100%;
  position: relative;
}

.digital-human-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 12px;
  text-align: center;
  padding: 8px;
}

/* 裁剪弹窗样式 */
.crop-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.crop-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.crop-modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.crop-modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.crop-modal-close {
  background: none;
  border: none;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.crop-modal-close:hover {
  background: #f0f0f0;
}

.crop-modal-body {
  padding: 20px;
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
}

.crop-container {
  width: 100%;
  max-width: 600px;
  max-height: 70vh;
  overflow: hidden;
}

.crop-container img {
  max-width: 100%;
  max-height: 70vh;
  display: block;
}

.crop-modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 背景管理器样式 */
.background-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.background-item {
  position: relative;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.9);
}

.background-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.background-thumbnail {
  position: relative;
  width: 100%;
  padding-top: 75%; /* 4:3 比例 */
  overflow: hidden;
}

.background-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.background-item:hover .background-overlay {
  opacity: 1;
}

.background-name {
  color: white;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.background-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.background-actions .btn-icon {
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}

.background-actions .btn-icon:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.background-actions .btn-icon-danger:hover {
  background: rgba(220, 53, 69, 0.3);
}

.submenu-item.checked {
  color: rgba(0, 123, 255, 0.9);
  font-weight: 600;
}

.submenu-item-checkbox {
  justify-content: flex-start !important;
}

</style>
