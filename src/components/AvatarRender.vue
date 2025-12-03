<template>
  <div 
    ref="containerRef" 
    class="avatar-render"
    :class="{ connected: appState.currentUserRole?.isConnected || appState.currentPartnerRole?.isConnected }"
    :style="backgroundStyle"
  >
    <!-- 伙伴立绘图片显示 -->
    <div 
      v-if="showPartnerIllustration && currentPartnerRoleType === 'illustration' && currentPartnerRoleAvatar"
      class="illustration-container"
      :class="{ dragging: isDraggingPartner }"
      :style="partnerAvatarPositionStyle"
      @mousedown="startDragPartner($event)"
    >
      <img 
        :src="partnerIllustrationImageUrl" 
        :alt="currentPartnerRoleName || '伙伴立绘'"
        class="illustration-image"
      />
    </div>
    
    <!-- 用户立绘图片显示 -->
    <div 
      v-if="showUserIllustration && currentUserRoleType === 'illustration' && currentUserRoleAvatar"
      class="illustration-container user-illustration"
      :class="{ dragging: isDraggingUser }"
      :style="userAvatarPositionStyle"
      @mousedown="startDragUser($event)"
    >
      <img 
        :src="userIllustrationImageUrl" 
        :alt="currentUserRoleName || '用户立绘'"
        class="illustration-image"
      />
    </div>
    
    <!-- 伙伴数字人容器 -->
    <div
      v-show="appState.currentPartnerRole && appState.currentPartnerRole.showDigitalHuman && appState.currentPartnerRole.type === 'digital_human'"
      id="digital-human-partner"
      class="sdk-container"
      :class="{ dragging: isDraggingPartnerDigitalHuman }"
      :style="partnerDigitalHumanPositionStyle"
      @mousedown="startDragPartnerDigitalHuman($event)"
    ></div>
    
    <!-- 用户数字人容器 -->
    <div
      v-show="appState.currentUserRole && appState.currentUserRole.showDigitalHuman && appState.currentUserRole.type === 'digital_human'"
      id="digital-human-user"
      class="sdk-container user-digital-human"
      :class="{ dragging: isDraggingUserDigitalHuman }"
      :style="userDigitalHumanPositionStyle"
      @mousedown="startDragUserDigitalHuman($event)"
    ></div>
    
    <!-- 语音输入动画 -->
    <div v-show="appState.asr.isListening" class="voice-animation">
      <img :src="siriIcon" alt="语音输入" />
    </div>
    
    <!-- 加载状态 -->
    <div v-if="false" class="loading-placeholder">
      <div class="loading-text">-- 正在连接 --</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, computed, ref, watch, onMounted, onUnmounted, type Ref } from 'vue'
import type { AppState, Role, UserRole } from '../types'
import { updateRole } from '../services/roleManagement'
import { updateUserRole } from '../services/userRoleManagement'
import siriIcon from '../assets/siri.png'
import { rendererManager } from '../renderers'
import type { IRenderer } from '../renderers'
import { DigitalHumanRenderer } from '../renderers/digital-human'
// 删除：不再需要 toMd5

// 注入全局状态
const appState = inject<AppState>('appState')!
const showUserIllustration = inject<Ref<boolean>>('showUserIllustration')!
const showPartnerIllustration = inject<Ref<boolean>>('showPartnerIllustration')!

// 容器引用
const containerRef = ref<HTMLElement | null>(null)

// 当前伙伴角色信息（数字人/立绘）
// 使用全局状态，不再需要本地 ref
// const currentPartnerRole = ref<Role | null>(null)
// const currentUserRole = ref<UserRole | null>(null)

// 拖动相关状态
const isDraggingPartner = ref(false)
const isDraggingUser = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const dragStartPositionX = ref(0)
const dragStartPositionY = ref(0)
const dragType = ref<'partner' | 'user' | null>(null)
// 拖动前对话面板的显示状态（用于拖动完成后恢复）
const historyPanelVisibleBeforeDrag = ref(false)

// 数字人渲染器实例
const partnerDigitalHumanRenderer = ref<IRenderer | null>(null)
const userDigitalHumanRenderer = ref<IRenderer | null>(null)

// 当前伙伴角色类型
const currentPartnerRoleType = computed(() => {
  return appState.currentPartnerRole?.type || 'digital_human'
})

// 当前用户角色类型
const currentUserRoleType = computed(() => {
  // 如果 currentUserRole 存在，使用其 type；如果不存在或 type 为 undefined，返回 undefined（不使用默认值）
  // 这样可以让 v-if 条件更精确：只有当角色存在且类型明确时才显示容器
  return appState.currentUserRole?.type
})


// 当前伙伴角色头像
const currentPartnerRoleAvatar = computed(() => {
  return appState.currentPartnerRole?.avatar || null
})

// 当前伙伴角色名称
const currentPartnerRoleName = computed(() => {
  return appState.currentPartnerRole?.name || appState.currentPartnerRole?.user || null
})

// 伙伴立绘图片URL（处理相对路径和绝对路径）
const partnerIllustrationImageUrl = computed(() => {
  if (!currentPartnerRoleAvatar.value) return ''
  const avatar = currentPartnerRoleAvatar.value
  // 如果是完整URL或绝对路径，直接返回
  if (avatar.startsWith('http') || avatar.startsWith('/')) {
    return avatar
  }
  // 如果是相对路径，添加服务器地址
  return `http://localhost:3001${avatar}`
})

// 当前用户角色头像
const currentUserRoleAvatar = computed(() => {
  return appState.currentUserRole?.avatar || null
})

// 当前用户角色名称
const currentUserRoleName = computed(() => {
  return appState.currentUserRole?.name || null
})

// 用户立绘图片URL（处理相对路径和绝对路径）
const userIllustrationImageUrl = computed(() => {
  if (!currentUserRoleAvatar.value) return ''
  const avatar = currentUserRoleAvatar.value
  // 如果是完整URL或绝对路径，直接返回
  if (avatar.startsWith('http') || avatar.startsWith('/')) {
    return avatar
  }
  // 如果是相对路径，添加服务器地址
  return `http://localhost:3001${avatar}`
})

// 加载当前伙伴角色信息
// 加载当前伙伴角色信息（不再修改 appState.currentPartnerRole，只用于其他用途）
async function loadCurrentPartnerRole() {
  // 不再修改 appState.currentPartnerRole，因为只能在入口处修改
  // 此函数保留用于其他用途（如果需要）
  return
}


// 创建或更新伙伴数字人渲染器
async function setupPartnerDigitalHumanRenderer(role: Role | null) {
  if (!containerRef.value) return

  // 销毁旧的渲染器
  if (partnerDigitalHumanRenderer.value && appState.currentPartnerRole) {
    const roleId = `partner:${appState.currentPartnerRole.user}`
    
    // 清理角色对象上的状态
    appState.currentPartnerRole.showDigitalHuman = false
    appState.currentPartnerRole.digitalHumanInstance = null
    appState.currentPartnerRole.isConnected = false
    
    // 销毁渲染器
    rendererManager.destroyRenderer(roleId)
    partnerDigitalHumanRenderer.value = null
  }

  // 如果角色是数字人类型，创建渲染器
  if (role && role.type === 'digital_human') {
    try {
      const roleId = `partner:${role.user}`
      const renderer = await rendererManager.createRenderer(roleId, {
        roleId,
        roleType: 'digital_human',
        positionX: role.positionX !== undefined ? role.positionX : 80,
        positionY: role.positionY !== undefined ? role.positionY : 50,
        scale: role.scale !== undefined ? role.scale : 1.0,
        avatarAppId: role.avatarAppId || '',
        avatarAppSecret: role.avatarAppSecret || '',
        containerId: 'digital-human-partner' // 固定容器ID
      })

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
            // 可以在这里处理状态变化
            console.log('数字人状态变化:', state)
          }
        })
      }

      // 容器在模板中定义，这里不需要创建容器或设置display

      partnerDigitalHumanRenderer.value = renderer
    } catch (error) {
      console.error('创建伙伴数字人渲染器失败:', error)
    }
  } else {
    // 非数字人角色时，隐藏容器
    if (role) {
      role.showDigitalHuman = false
    }
  }
}

// 创建或更新用户数字人渲染器
async function setupUserDigitalHumanRenderer(role: UserRole | null) {
  if (!containerRef.value) return

  // 销毁旧的渲染器
  if (userDigitalHumanRenderer.value && appState.currentUserRole) {
    const roleId = `user:${appState.currentUserRole.id}`
    
    // 清理角色对象上的状态
    appState.currentUserRole.showDigitalHuman = false
    appState.currentUserRole.digitalHumanInstance = null
    appState.currentUserRole.isConnected = false
    
    // 销毁渲染器
    rendererManager.destroyRenderer(roleId)
    userDigitalHumanRenderer.value = null
  }

  // 如果角色是数字人类型，创建渲染器
  if (role && role.type === 'digital_human') {
    try {
      const roleId = `user:${role.id}`
      const renderer = await rendererManager.createRenderer(roleId, {
        roleId,
        roleType: 'digital_human',
        positionX: role.positionX !== undefined ? role.positionX : 20,
        positionY: role.positionY !== undefined ? role.positionY : 50,
        scale: role.scale !== undefined ? role.scale : 1.0,
        avatarAppId: role.avatarAppId || '',
        avatarAppSecret: role.avatarAppSecret || '',
        containerId: 'digital-human-user' // 固定容器ID
      })

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
            console.log('数字人状态变化:', state)
          }
        })
      }

      // 容器在模板中定义，这里不需要创建容器或设置display

      userDigitalHumanRenderer.value = renderer
    } catch (error) {
      console.error('创建用户数字人渲染器失败:', error)
    }
  } else {
    // 非数字人角色时，隐藏容器
    if (role) {
      role.showDigitalHuman = false
    }
  }
}

// 监听 user 和 apiKey 变化，重新加载角色
watch([() => appState.llm.user, () => appState.llm.apiKey], async () => {
  await loadCurrentPartnerRole()
  // 排查问题：暂时注释掉同时操作两个数字人的渲染函数
  // await setupPartnerDigitalHumanRenderer(appState.currentPartnerRole)
  // await setupUserDigitalHumanRenderer(appState.currentUserRole)
}, { immediate: true })

// 监听角色更新事件，重新加载当前角色
const handleRoleUpdated = async () => {
  // 不再需要 loadCurrentPartnerRole 和 loadCurrentUserRole，因为 appState.currentUserRole 和 appState.currentPartnerRole 只在入口处修改
  // 排查问题：暂时注释掉同时操作两个数字人的渲染函数
  // await setupPartnerDigitalHumanRenderer(appState.currentPartnerRole)
  // await setupUserDigitalHumanRenderer(appState.currentUserRole)
}

// 监听伙伴角色变化
watch(() => appState.currentPartnerRole, async (newRole) => {
  await setupPartnerDigitalHumanRenderer(newRole)
})

// 监听用户角色变化
watch(() => appState.currentUserRole, async (newRole) => {
  await setupUserDigitalHumanRenderer(newRole)
})

// 删除：手动控制容器display的watch（显示/隐藏由 v-if 控制）

onMounted(() => {
  window.addEventListener('roleUpdated', handleRoleUpdated)
  
  // 标志：是否正在处理立绘拖动
  let isHandlingIllustrationDrag = false
  
  // 添加全局mousedown监听，检测鼠标位置
  const globalMouseDown = (event: MouseEvent) => {
    // 如果正在处理立绘拖动，跳过
    if (isHandlingIllustrationDrag) {
      return
    }
    
    // 如果事件目标已经是立绘容器或其子元素，说明事件已经到达立绘，不处理
    const target = event.target as HTMLElement
    if (target && (target.classList.contains('illustration-container') || target.closest('.illustration-container'))) {
      return
    }
    
    // 如果事件目标已经是数字人容器或其子元素，说明事件已经到达数字人，不处理
    if (target && (target.classList.contains('sdk-container') || target.closest('.sdk-container'))) {
      return
    }
    
    const x = event.clientX
    const y = event.clientY
    
    // 1.1 检测是否在面板区域（优先级高过立绘）
    const panelWrapper = document.querySelector('.history-panel-wrapper') as HTMLElement
    if (panelWrapper && panelWrapper.style.display !== 'none') {
      const panelRect = panelWrapper.getBoundingClientRect()
      if (x >= panelRect.left && x <= panelRect.right && y >= panelRect.top && y <= panelRect.bottom) {
        // 在面板区域，正常处理，不拦截
        return
      }
    }
    
    // 1.2 检测是否在立绘区域
    const illustrationContainers = document.querySelectorAll('.illustration-container') as NodeListOf<HTMLElement>
    let clickedIllustration: HTMLElement | null = null
    
    for (const container of illustrationContainers) {
      const rect = container.getBoundingClientRect()
      // 检查点击位置是否在立绘区域内
      if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
        clickedIllustration = container
        break
      }
    }
    
    // 如果点击在立绘区域
    if (clickedIllustration) {
      // 设置标志：正在处理立绘拖动
      isHandlingIllustrationDrag = true
      
      // 隐藏面板（如果显示）
      const panelVisible = panelWrapper && panelWrapper.style.display !== 'none'
      if (panelVisible) {
        panelWrapper.style.display = 'none'
        historyPanelVisibleBeforeDrag.value = true
      } else {
        historyPanelVisibleBeforeDrag.value = false
      }
      
      // 将鼠标事件目标指向立绘容器，触发立绘容器的@mousedown事件
      const syntheticEvent = new MouseEvent('mousedown', {
        bubbles: true,
        cancelable: true,
        clientX: x,
        clientY: y,
        button: event.button,
        buttons: event.buttons,
        view: window
      })
      
      // 在立绘容器上触发事件，让Vue的事件系统处理
      clickedIllustration.dispatchEvent(syntheticEvent)
      
      event.preventDefault()
      event.stopPropagation()
      return
    }
    
    // 1.3 检测是否在数字人区域
    const digitalHumanContainers = document.querySelectorAll('.sdk-container') as NodeListOf<HTMLElement>
    let clickedDigitalHuman: HTMLElement | null = null
    
    for (const container of digitalHumanContainers) {
      const rect = container.getBoundingClientRect()
      // 检查点击位置是否在数字人区域内
      if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
        clickedDigitalHuman = container
        break
      }
    }
    
    // 如果点击在数字人区域
    if (clickedDigitalHuman) {
      // 隐藏面板（如果显示）
      const panelVisible = panelWrapper && panelWrapper.style.display !== 'none'
      if (panelVisible) {
        panelWrapper.style.display = 'none'
        historyPanelVisibleBeforeDrag.value = true
      } else {
        historyPanelVisibleBeforeDrag.value = false
      }
      
      // 将鼠标事件目标指向数字人容器，触发数字人容器的@mousedown事件
      const syntheticEvent = new MouseEvent('mousedown', {
        bubbles: true,
        cancelable: true,
        clientX: x,
        clientY: y,
        button: event.button,
        buttons: event.buttons,
        view: window
      })
      
      // 在数字人容器上触发事件，让Vue的事件系统处理
      clickedDigitalHuman.dispatchEvent(syntheticEvent)
      
      event.preventDefault()
      event.stopPropagation()
      return
    }
  }
  document.addEventListener('mousedown', globalMouseDown, true) // 使用捕获阶段，优先处理
  
  // 添加全局mouseup监听，清除标志
  const globalMouseUp = () => {
    // 鼠标释放时清除标志
    isHandlingIllustrationDrag = false
  }
  document.addEventListener('mouseup', globalMouseUp, true)
  
  // 保存清理函数
  ;(window as any).__cleanupGlobalMouseDown = () => {
    document.removeEventListener('mousedown', globalMouseDown, true)
    document.removeEventListener('mouseup', globalMouseUp, true)
  }
})

onUnmounted(() => {
  window.removeEventListener('roleUpdated', handleRoleUpdated)
  // 清理全局mousedown监听
  if ((window as any).__cleanupGlobalMouseDown) {
    (window as any).__cleanupGlobalMouseDown()
  }
  // 清理立绘拖动事件监听器
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDragPartner)
  document.removeEventListener('mouseup', endDragUser)
  
  // 清理数字人拖动事件监听器
  document.removeEventListener('mousemove', handleDigitalHumanDrag)
  document.removeEventListener('mouseup', endDragPartnerDigitalHuman)
  document.removeEventListener('mouseup', endDragUserDigitalHuman)
  
  // 清理数字人渲染器
  if (partnerDigitalHumanRenderer.value && appState.currentPartnerRole) {
    const roleId = `partner:${appState.currentPartnerRole.user}`
    rendererManager.destroyRenderer(roleId)
  }
  if (userDigitalHumanRenderer.value && appState.currentUserRole) {
    const roleId = `user:${appState.currentUserRole.id}`
    rendererManager.destroyRenderer(roleId)
  }
  
  // 注意：数字人的 SDK 连接/断开由其他清理逻辑处理（如 rendererManager.destroyRenderer）
  // 拖拽清理函数不负责 SDK 连接/断开
})

// 背景图片样式
const backgroundStyle = computed(() => {
  const style: Record<string, string> = {}
  
  if (appState.ui.backgroundImage) {
    style.backgroundImage = `url("${appState.ui.backgroundImage}")`
    style.backgroundSize = 'cover'
    style.backgroundPosition = 'center'
    style.backgroundRepeat = 'no-repeat'
  }
  
  return style
})

// 拖动时的临时位置（用于实时更新显示）
const draggingPartnerPositionX = ref<number | null>(null)
const draggingPartnerPositionY = ref<number | null>(null)
const draggingUserPositionX = ref<number | null>(null)
const draggingUserPositionY = ref<number | null>(null)

// 数字人拖拽相关状态（独立实现，不复用立绘的状态）
const isDraggingPartnerDigitalHuman = ref(false)
const isDraggingUserDigitalHuman = ref(false)
const dragDigitalHumanStartX = ref(0)
const dragDigitalHumanStartY = ref(0)
const dragDigitalHumanStartPositionX = ref(0)
const dragDigitalHumanStartPositionY = ref(0)
const dragDigitalHumanType = ref<'partnerDigitalHuman' | 'userDigitalHuman' | null>(null)
const draggingPartnerDigitalHumanPositionX = ref<number | null>(null)
const draggingPartnerDigitalHumanPositionY = ref<number | null>(null)
const draggingUserDigitalHumanPositionX = ref<number | null>(null)
const draggingUserDigitalHumanPositionY = ref<number | null>(null)

// 伙伴角色位置和大小样式（从当前伙伴角色读取，如果没有则使用默认值）
const partnerAvatarPositionStyle = computed(() => {
  // 如果正在拖动，使用拖动时的临时位置
  const positionX = isDraggingPartner.value && draggingPartnerPositionX.value !== null 
    ? draggingPartnerPositionX.value 
    : (appState.currentPartnerRole?.positionX !== undefined ? appState.currentPartnerRole.positionX : 80)
  const positionY = isDraggingPartner.value && draggingPartnerPositionY.value !== null 
    ? draggingPartnerPositionY.value 
    : (appState.currentPartnerRole?.positionY !== undefined ? appState.currentPartnerRole.positionY : 50)
  const scale = appState.currentPartnerRole?.scale !== undefined ? appState.currentPartnerRole.scale : (appState.currentPartnerRole?.type === 'illustration' ? 0.7 : 1.0)
  
  const baseWidth = 512
  const baseHeight = 768
  const width = baseWidth * scale
  const height = baseHeight * scale
  
  return {
    left: `${positionX}%`,
    top: `${positionY}%`,
    transform: 'translate(-50%, -50%)',
    width: `${width}px`,
    height: `${height}px`
  }
})

// 用户角色位置和大小样式（从当前用户角色读取，如果没有则使用默认值）
const userAvatarPositionStyle = computed(() => {
  // 如果正在拖动，使用拖动时的临时位置
  const positionX = isDraggingUser.value && draggingUserPositionX.value !== null 
    ? draggingUserPositionX.value 
    : (appState.currentUserRole?.positionX !== undefined ? appState.currentUserRole.positionX : 20)
  const positionY = isDraggingUser.value && draggingUserPositionY.value !== null 
    ? draggingUserPositionY.value 
    : (appState.currentUserRole?.positionY !== undefined ? appState.currentUserRole.positionY : 50)
  const scale = appState.currentUserRole?.scale !== undefined ? appState.currentUserRole.scale : (appState.currentUserRole?.type === 'illustration' ? 0.7 : 1.0)
  
  const baseWidth = 512
  const baseHeight = 768
  const width = baseWidth * scale
  const height = baseHeight * scale
  
    return {
    left: `${positionX}%`,
    top: `${positionY}%`,
    transform: 'translate(-50%, -50%)',
    width: `${width}px`,
    height: `${height}px`
  }
})

// 伙伴数字人位置和大小样式（独立实现，不复用立绘的样式）
const partnerDigitalHumanPositionStyle = computed(() => {
  // 如果正在拖动数字人，使用拖动时的临时位置
  const positionX = isDraggingPartnerDigitalHuman.value && draggingPartnerDigitalHumanPositionX.value !== null 
    ? draggingPartnerDigitalHumanPositionX.value 
    : (appState.currentPartnerRole?.positionX !== undefined ? appState.currentPartnerRole.positionX : 80)
  const positionY = isDraggingPartnerDigitalHuman.value && draggingPartnerDigitalHumanPositionY.value !== null 
    ? draggingPartnerDigitalHumanPositionY.value 
    : (appState.currentPartnerRole?.positionY !== undefined ? appState.currentPartnerRole.positionY : 50)
  const scale = appState.currentPartnerRole?.scale !== undefined ? appState.currentPartnerRole.scale : 1.0
  
  const baseWidth = 512
  const baseHeight = 768
  const width = baseWidth * scale
  const height = baseHeight * scale
  
  return {
    left: `${positionX}%`,
    top: `${positionY}%`,
    transform: 'translate(-50%, -50%)',
    width: `${width}px`,
    height: `${height}px`
  }
})

// 用户数字人位置和大小样式（独立实现，不复用立绘的样式）
const userDigitalHumanPositionStyle = computed(() => {
  // 如果正在拖动数字人，使用拖动时的临时位置
  const positionX = isDraggingUserDigitalHuman.value && draggingUserDigitalHumanPositionX.value !== null 
    ? draggingUserDigitalHumanPositionX.value 
    : (appState.currentUserRole?.positionX !== undefined ? appState.currentUserRole.positionX : 20)
  const positionY = isDraggingUserDigitalHuman.value && draggingUserDigitalHumanPositionY.value !== null 
    ? draggingUserDigitalHumanPositionY.value 
    : (appState.currentUserRole?.positionY !== undefined ? appState.currentUserRole.positionY : 50)
  const scale = appState.currentUserRole?.scale !== undefined ? appState.currentUserRole.scale : (appState.currentUserRole?.type === 'illustration' ? 0.7 : 1.0)
  
  const baseWidth = 512
  const baseHeight = 768
  const width = baseWidth * scale
  const height = baseHeight * scale
  
  return {
    left: `${positionX}%`,
    top: `${positionY}%`,
    transform: 'translate(-50%, -50%)',
    width: `${width}px`,
    height: `${height}px`
  }
})

// 开始拖动伙伴立绘
function startDragPartner(event: MouseEvent) {
  if (!appState.currentPartnerRole || !appState.llm.apiKey) return
  
  event.preventDefault()
  event.stopPropagation()
  
  // 禁用config-panel和chat-tab的pointer-events，避免拦截拖动事件
  const configPanel = document.querySelector('.config-panel') as HTMLElement
  if (configPanel) {
    configPanel.style.pointerEvents = 'none'
  }
  const chatTab = document.querySelector('.chat-tab') as HTMLElement
  if (chatTab) {
    chatTab.style.pointerEvents = 'none'
  }
  
  isDraggingPartner.value = true
  dragType.value = 'partner'
  dragStartX.value = event.clientX
  dragStartY.value = event.clientY
  dragStartPositionX.value = appState.currentPartnerRole.positionX !== undefined ? appState.currentPartnerRole.positionX : 80
  dragStartPositionY.value = appState.currentPartnerRole.positionY !== undefined ? appState.currentPartnerRole.positionY : 50
  draggingPartnerPositionX.value = dragStartPositionX.value
  draggingPartnerPositionY.value = dragStartPositionY.value
  
  // 立即提升立绘的z-index（通过内联样式）
  const illustrationContainer = event.currentTarget as HTMLElement
  if (illustrationContainer) {
    illustrationContainer.style.zIndex = '1000'
  }
  
  document.addEventListener('mousemove', handleDrag, { passive: false })
  document.addEventListener('mouseup', endDragPartner)
}

// 开始拖动用户立绘
function startDragUser(event: MouseEvent) {
  if (!appState.currentUserRole || !appState.llm.apiKey) return
  
  event.preventDefault()
  event.stopPropagation()
  
  // 禁用config-panel和chat-tab的pointer-events，避免拦截拖动事件
  const configPanel = document.querySelector('.config-panel') as HTMLElement
  if (configPanel) {
    configPanel.style.pointerEvents = 'none'
  }
  const chatTab = document.querySelector('.chat-tab') as HTMLElement
  if (chatTab) {
    chatTab.style.pointerEvents = 'none'
  }
  
  isDraggingUser.value = true
  dragType.value = 'user'
  dragStartX.value = event.clientX
  dragStartY.value = event.clientY
  dragStartPositionX.value = appState.currentUserRole.positionX !== undefined ? appState.currentUserRole.positionX : 20
  dragStartPositionY.value = appState.currentUserRole.positionY !== undefined ? appState.currentUserRole.positionY : 50
  draggingUserPositionX.value = dragStartPositionX.value
  draggingUserPositionY.value = dragStartPositionY.value
  
  // 立即提升立绘的z-index（通过内联样式）
  const illustrationContainer = event.currentTarget as HTMLElement
  if (illustrationContainer) {
    illustrationContainer.style.zIndex = '1000'
  }
  
  document.addEventListener('mousemove', handleDrag, { passive: false })
  document.addEventListener('mouseup', endDragUser)
}

// 处理拖动
function handleDrag(event: MouseEvent) {
  if (!dragType.value) return
  
  const deltaX = event.clientX - dragStartX.value
  const deltaY = event.clientY - dragStartY.value
  
  // 计算新位置（百分比）
  const containerWidth = window.innerWidth
  const containerHeight = window.innerHeight
  const newPositionX = Math.max(0, Math.min(100, dragStartPositionX.value + (deltaX / containerWidth) * 100))
  const newPositionY = Math.max(0, Math.min(100, dragStartPositionY.value + (deltaY / containerHeight) * 100))
  
  if (dragType.value === 'partner') {
    draggingPartnerPositionX.value = newPositionX
    draggingPartnerPositionY.value = newPositionY
  } else if (dragType.value === 'user') {
    draggingUserPositionX.value = newPositionX
    draggingUserPositionY.value = newPositionY
  }
}

// 结束拖动伙伴立绘
async function endDragPartner(_event: MouseEvent) {
  if (!isDraggingPartner.value || !appState.currentPartnerRole || !appState.llm.apiKey) {
    cleanupDrag()
    return
  }
  
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDragPartner)
  
  const finalPositionX = draggingPartnerPositionX.value ?? dragStartPositionX.value
  const finalPositionY = draggingPartnerPositionY.value ?? dragStartPositionY.value
  
  // 更新角色配置
  try {
    await updateRole(
      appState.currentPartnerRole.id,
      appState.llm.apiKey,
      {
        positionX: finalPositionX,
        positionY: finalPositionY
      }
    )
    // 直接更新内存中的角色位置，避免重新加载
    if (appState.currentPartnerRole) {
      appState.currentPartnerRole.positionX = finalPositionX
      appState.currentPartnerRole.positionY = finalPositionY
    }
  } catch (error) {
    console.error('更新伙伴角色位置失败:', error)
  }
  
  cleanupDrag()
}

// 结束拖动用户立绘
async function endDragUser(_event: MouseEvent) {
  if (!isDraggingUser.value || !appState.currentUserRole || !appState.llm.apiKey) {
    cleanupDrag()
    return
  }
  
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDragUser)
  
  const finalPositionX = draggingUserPositionX.value ?? dragStartPositionX.value
  const finalPositionY = draggingUserPositionY.value ?? dragStartPositionY.value
  
  // 更新用户角色配置
  try {
    await updateUserRole(
      appState.currentUserRole.id,
      appState.llm.apiKey,
      {
        positionX: finalPositionX,
        positionY: finalPositionY
      }
    )
    // 直接更新内存中的角色位置，避免重新加载
    if (appState.currentUserRole) {
      appState.currentUserRole.positionX = finalPositionX
      appState.currentUserRole.positionY = finalPositionY
    }
  } catch (error) {
    console.error('更新用户角色位置失败:', error)
  }
  
  cleanupDrag()
}

// 开始拖动伙伴数字人
function startDragPartnerDigitalHuman(event: MouseEvent) {
  if (!appState.currentPartnerRole || !appState.llm.apiKey) return
  
  event.preventDefault()
  event.stopPropagation()
  
  // 禁用config-panel和chat-tab的pointer-events，避免拦截拖动事件
  const configPanel = document.querySelector('.config-panel') as HTMLElement
  if (configPanel) {
    configPanel.style.pointerEvents = 'none'
  }
  const chatTab = document.querySelector('.chat-tab') as HTMLElement
  if (chatTab) {
    chatTab.style.pointerEvents = 'none'
  }
  
  isDraggingPartnerDigitalHuman.value = true
  dragDigitalHumanType.value = 'partnerDigitalHuman'
  dragDigitalHumanStartX.value = event.clientX
  dragDigitalHumanStartY.value = event.clientY
  dragDigitalHumanStartPositionX.value = appState.currentPartnerRole.positionX !== undefined ? appState.currentPartnerRole.positionX : 80
  dragDigitalHumanStartPositionY.value = appState.currentPartnerRole.positionY !== undefined ? appState.currentPartnerRole.positionY : 50
  draggingPartnerDigitalHumanPositionX.value = dragDigitalHumanStartPositionX.value
  draggingPartnerDigitalHumanPositionY.value = dragDigitalHumanStartPositionY.value
  
  // 立即提升数字人容器的z-index（通过内联样式）
  const digitalHumanContainer = event.currentTarget as HTMLElement
  if (digitalHumanContainer) {
    digitalHumanContainer.style.zIndex = '1000'
  }
  
  document.addEventListener('mousemove', handleDigitalHumanDrag, { passive: false })
  document.addEventListener('mouseup', endDragPartnerDigitalHuman)
}

// 开始拖动用户数字人
function startDragUserDigitalHuman(event: MouseEvent) {
  if (!appState.currentUserRole || !appState.llm.apiKey) return
  
  event.preventDefault()
  event.stopPropagation()
  
  // 禁用config-panel和chat-tab的pointer-events，避免拦截拖动事件
  const configPanel = document.querySelector('.config-panel') as HTMLElement
  if (configPanel) {
    configPanel.style.pointerEvents = 'none'
  }
  const chatTab = document.querySelector('.chat-tab') as HTMLElement
  if (chatTab) {
    chatTab.style.pointerEvents = 'none'
  }
  
  isDraggingUserDigitalHuman.value = true
  dragDigitalHumanType.value = 'userDigitalHuman'
  dragDigitalHumanStartX.value = event.clientX
  dragDigitalHumanStartY.value = event.clientY
  dragDigitalHumanStartPositionX.value = appState.currentUserRole.positionX !== undefined ? appState.currentUserRole.positionX : 20
  dragDigitalHumanStartPositionY.value = appState.currentUserRole.positionY !== undefined ? appState.currentUserRole.positionY : 50
  draggingUserDigitalHumanPositionX.value = dragDigitalHumanStartPositionX.value
  draggingUserDigitalHumanPositionY.value = dragDigitalHumanStartPositionY.value
  
  // 立即提升数字人容器的z-index（通过内联样式）
  const digitalHumanContainer = event.currentTarget as HTMLElement
  if (digitalHumanContainer) {
    digitalHumanContainer.style.zIndex = '1000'
  }
  
  document.addEventListener('mousemove', handleDigitalHumanDrag, { passive: false })
  document.addEventListener('mouseup', endDragUserDigitalHuman)
}

// 处理数字人拖动
function handleDigitalHumanDrag(event: MouseEvent) {
  if (!dragDigitalHumanType.value) return
  
  const deltaX = event.clientX - dragDigitalHumanStartX.value
  const deltaY = event.clientY - dragDigitalHumanStartY.value
  
  // 计算新位置（百分比）
  const containerWidth = window.innerWidth
  const containerHeight = window.innerHeight
  const newPositionX = Math.max(0, Math.min(100, dragDigitalHumanStartPositionX.value + (deltaX / containerWidth) * 100))
  const newPositionY = Math.max(0, Math.min(100, dragDigitalHumanStartPositionY.value + (deltaY / containerHeight) * 100))
  
  if (dragDigitalHumanType.value === 'partnerDigitalHuman') {
    draggingPartnerDigitalHumanPositionX.value = newPositionX
    draggingPartnerDigitalHumanPositionY.value = newPositionY
  } else if (dragDigitalHumanType.value === 'userDigitalHuman') {
    draggingUserDigitalHumanPositionX.value = newPositionX
    draggingUserDigitalHumanPositionY.value = newPositionY
  }
}

// 结束拖动伙伴数字人
async function endDragPartnerDigitalHuman(_event: MouseEvent) {
  if (!isDraggingPartnerDigitalHuman.value || !appState.currentPartnerRole || !appState.llm.apiKey) {
    cleanupDigitalHumanDrag()
    return
  }
  
  document.removeEventListener('mousemove', handleDigitalHumanDrag)
  document.removeEventListener('mouseup', endDragPartnerDigitalHuman)
  
  const finalPositionX = draggingPartnerDigitalHumanPositionX.value ?? dragDigitalHumanStartPositionX.value
  const finalPositionY = draggingPartnerDigitalHumanPositionY.value ?? dragDigitalHumanStartPositionY.value
  
  // 更新角色配置（只更新位置，不涉及连接/断开）
  try {
    await updateRole(
      appState.currentPartnerRole.id,
      appState.llm.apiKey,
      {
        positionX: finalPositionX,
        positionY: finalPositionY
      }
    )
    // 直接更新内存中的角色位置，避免重新加载
    if (appState.currentPartnerRole) {
      appState.currentPartnerRole.positionX = finalPositionX
      appState.currentPartnerRole.positionY = finalPositionY
    }
  } catch (error) {
    console.error('更新伙伴数字人位置失败:', error)
  }
  
  cleanupDigitalHumanDrag()
  
  // 注意：拖拽结束只负责更新位置，不负责 SDK 连接/断开
  // 数字人容器使用 v-show，拖拽时容器始终存在，SDK 连接状态不受影响
}

// 结束拖动用户数字人
async function endDragUserDigitalHuman(_event: MouseEvent) {
  if (!isDraggingUserDigitalHuman.value || !appState.currentUserRole || !appState.llm.apiKey) {
    cleanupDigitalHumanDrag()
    return
  }
  
  document.removeEventListener('mousemove', handleDigitalHumanDrag)
  document.removeEventListener('mouseup', endDragUserDigitalHuman)
  
  const finalPositionX = draggingUserDigitalHumanPositionX.value ?? dragDigitalHumanStartPositionX.value
  const finalPositionY = draggingUserDigitalHumanPositionY.value ?? dragDigitalHumanStartPositionY.value
  
  // 更新用户角色配置（只更新位置，不涉及连接/断开）
  try {
    await updateUserRole(
      appState.currentUserRole.id,
      appState.llm.apiKey,
      {
        positionX: finalPositionX,
        positionY: finalPositionY
      }
    )
    // 直接更新内存中的角色位置，避免重新加载
    if (appState.currentUserRole) {
      appState.currentUserRole.positionX = finalPositionX
      appState.currentUserRole.positionY = finalPositionY
    }
  } catch (error) {
    console.error('更新用户数字人位置失败:', error)
  }
  
  cleanupDigitalHumanDrag()
  
  // 注意：拖拽结束只负责更新位置，不负责 SDK 连接/断开
  // 数字人容器使用 v-show，拖拽时容器始终存在，SDK 连接状态不受影响
}

// 清理数字人拖动状态
function cleanupDigitalHumanDrag() {
  isDraggingPartnerDigitalHuman.value = false
  isDraggingUserDigitalHuman.value = false
  dragDigitalHumanType.value = null
  draggingPartnerDigitalHumanPositionX.value = null
  draggingPartnerDigitalHumanPositionY.value = null
  draggingUserDigitalHumanPositionX.value = null
  draggingUserDigitalHumanPositionY.value = null
  
  // 恢复config-panel和chat-tab的pointer-events
  const configPanel = document.querySelector('.config-panel') as HTMLElement
  if (configPanel) {
    configPanel.style.pointerEvents = ''
  }
  const chatTab = document.querySelector('.chat-tab') as HTMLElement
  if (chatTab) {
    chatTab.style.pointerEvents = ''
  }
  
  // 恢复数字人容器的z-index
  const digitalHumanContainers = document.querySelectorAll('.sdk-container')
  digitalHumanContainers.forEach(container => {
    (container as HTMLElement).style.zIndex = ''
  })
  
  // 恢复面板状态（拖动事件结束恢复面板状态）
  if (historyPanelVisibleBeforeDrag.value) {
    const panelWrapper = document.querySelector('.history-panel-wrapper') as HTMLElement
    if (panelWrapper) {
      panelWrapper.style.display = ''
    }
  }
  historyPanelVisibleBeforeDrag.value = false
  
  // 注意：拖拽清理函数只负责清理拖拽状态，不负责 SDK 连接/断开
  // SDK 连接/断开由其他逻辑处理（如角色切换、连接/断开按钮等）
}

// 清理拖动状态
function cleanupDrag() {
  isDraggingPartner.value = false
  isDraggingUser.value = false
  dragType.value = null
  draggingPartnerPositionX.value = null
  draggingPartnerPositionY.value = null
  draggingUserPositionX.value = null
  draggingUserPositionY.value = null
  
  // 恢复config-panel和chat-tab的pointer-events
  const configPanel = document.querySelector('.config-panel') as HTMLElement
  if (configPanel) {
    configPanel.style.pointerEvents = ''
    }
  const chatTab = document.querySelector('.chat-tab') as HTMLElement
  if (chatTab) {
    chatTab.style.pointerEvents = ''
  }
  
  // 恢复立绘的z-index
  const illustrationContainers = document.querySelectorAll('.illustration-container')
  illustrationContainers.forEach(container => {
    (container as HTMLElement).style.zIndex = ''
  })
  
  // 恢复数字人容器的z-index
  const digitalHumanContainers = document.querySelectorAll('.sdk-container')
  digitalHumanContainers.forEach(container => {
    (container as HTMLElement).style.zIndex = ''
  })
  
  // 恢复面板状态（拖动事件结束恢复面板状态）
  if (historyPanelVisibleBeforeDrag.value) {
    const panelWrapper = document.querySelector('.history-panel-wrapper') as HTMLElement
    if (panelWrapper) {
      panelWrapper.style.display = ''
    }
  }
  historyPanelVisibleBeforeDrag.value = false
}
</script>

<style scoped>
.avatar-render {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  transition: background-image 0.5s ease-in-out;
}

.avatar-render.connected {
  z-index: 0;
}

.sdk-container {
  position: fixed;
  /* 移除固定宽高，使用内联样式动态设置 */
  max-width: 90vw;
  max-height: 90vh;
  opacity: 1;
  transition: opacity 0.3s ease-in-out, left 0.3s ease-in-out, top 0.3s ease-in-out, width 0.3s ease-in-out, height 0.3s ease-in-out;
  pointer-events: auto;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
  user-select: none;
  -webkit-user-select: none;
}

.sdk-container.visible {
  opacity: 1;
}

.avatar-render.connected {
  z-index: 1;
}

.illustration-container {
  position: fixed;
  max-width: 90vw;
  max-height: 90vh;
  opacity: 1;
  transition: opacity 0.3s ease-in-out, left 0.3s ease-in-out, top 0.3s ease-in-out, width 0.3s ease-in-out, height 0.3s ease-in-out;
  pointer-events: auto;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
  user-select: none;
  -webkit-user-select: none;
}

.illustration-container.dragging {
  cursor: grabbing;
  transition: none;
  z-index: 1000;
}

.sdk-container.dragging {
  cursor: grabbing;
  transition: none;
  z-index: 1000;
}

.illustration-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
  pointer-events: none;
}

.user-illustration {
  z-index: 3; /* 用户立绘在伙伴立绘之上 */
}

.voice-animation {
  position: absolute;
  left: 50%;
  top: 75%;
  transform: translateX(-50%);
  width: 360px;
  max-width: 90%;
  z-index: 101;
}

.voice-animation > img {
  width: 100%;
  height: auto;
}

.loading-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(5px);
}

.loading-text {
  font-size: 18px;
  color: #666;
  font-weight: 500;
}
</style>
