# currentUserRole 数据流标注

## 数据流节点标注

### 节点1：用户登录后获取当前用户和伙伴角色

**位置：`ConfigPanel.vue` - `handleApiKeyLogin()` (2710行)**

```typescript
// 1.1 获取当前用户角色
await loadUserRoles()  // 2721行
  └─> loadUserRoles() (2840行)
      └─> getUserRoles(globalApiKey.value)  // 从API获取
      └─> currentUserRole.value = currentRole  // 2852行 - 【节点3：记录当前角色】

// 1.2 获取当前伙伴角色
await loadRoles()  // 2747行 - 加载伙伴角色列表
await getAndSetCurrentPartnerRole()  // 2749行 - 获取并设置当前伙伴角色
```

---

### 节点2：切换的时候更新当前角色

**位置：`ConfigPanel.vue` - `handleSetCurrentUserRole()` (3022行)**

```typescript
// 2.1 更新数据库
await setCurrentUserRole(role.id, globalApiKey.value)  // 3044行

// 2.2 重新加载角色列表
await loadUserRoles()  // 3045行
  └─> loadUserRoles() (2840行)
      └─> getUserRoles(globalApiKey.value)  // 从API获取
      └─> currentUserRole.value = currentRole  // 2852行

// 2.3 直接记录当前角色（使用传入的role参数）
currentUserRole.value = role  // 3047行 - 【节点3：记录当前角色】
```

---

### 节点3：记录当前角色

**位置1：登录后**
- `ConfigPanel.vue` - `loadUserRoles()` (2852行)
  ```typescript
  const currentRole = roleList.find(r => r.isCurrent) || null
  currentUserRole.value = currentRole  // ConfigPanel.vue 的 currentUserRole
  ```

**位置2：切换时**
- `ConfigPanel.vue` - `handleSetCurrentUserRole()` (3047行)
  ```typescript
  currentUserRole.value = role  // ConfigPanel.vue 的 currentUserRole
  ```

**位置3：AvatarRender.vue 同步更新**
- `AvatarRender.vue` - `loadCurrentUserRole()` (206行)
  ```typescript
  const role = userRoles.find(r => r.isCurrent)
  currentUserRole.value = role || null  // AvatarRender.vue 的 currentUserRole
  ```

---

### 节点4：更新连接按钮可用状态

**位置1：登录后触发**
- `ConfigPanel.vue` - `handleApiKeyLogin()` (2753行)
  ```typescript
  const event = new CustomEvent('roleUpdated')
  window.dispatchEvent(event)  // 触发 roleUpdated 事件
  ```

**位置2：切换时触发**
- `ConfigPanel.vue` - `handleSetCurrentUserRole()` (3059行)
  ```typescript
  const event = new CustomEvent('roleUpdated')
  window.dispatchEvent(event)  // 触发 roleUpdated 事件
  ```

**位置3：AvatarRender.vue 监听并更新**
- `AvatarRender.vue` - `handleRoleUpdated()` (381行)
  ```typescript
  const handleRoleUpdated = async () => {
    await loadCurrentPartnerRole()  // 383行
    await loadCurrentUserRole()     // 383行 - 更新 AvatarRender.vue 的 currentUserRole
    await setupPartnerDigitalHumanRenderer(currentPartnerRole.value)
    await setupUserDigitalHumanRenderer(currentUserRole.value)
  }
  ```

**连接按钮可用状态判断：**
- `ConfigPanel.vue` (1073行)
  ```typescript
  :disabled="isConnecting || appState.avatar.connectedRoles.has(`user:${role.id}`) || !role.isCurrent"
  ```
  - 只有 `role.isCurrent === true` 时按钮才可用

---

### 节点5：在点击连接时实时创建容器

**位置：`ConfigPanel.vue` - `handleConnectUserRoleFromList()` (1968行)**

```typescript
// 5.1 创建渲染器
renderer = await rendererManager.createRenderer(userRoleId, {...})  // 1995行

// 5.2 实时创建容器
appState.avatar.showUserDigitalHuman = true  // 2006行 - 设置显示状态

// 5.3 等待Vue渲染容器
await new Promise(resolve => setTimeout(resolve, 100))  // 2007行

// 5.4 获取容器并渲染
const roleIdHash = toMd5(userRoleId)  // 2009行
const containerId = `digital-human-${roleIdHash}`  // 2010行
const containerElement = document.getElementById(containerId)  // 2011行
if (!containerElement) {
  throw new Error(`数字人容器不存在: #${containerId}`)  // 2012行
}
await renderer.render(containerElement)  // 2015行
```

**容器创建条件（AvatarRender.vue 20行）：**
```vue
v-show="currentUserRoleType === 'digital_human' && appState.avatar.showUserDigitalHuman && currentUserRole"
```

**容器ID计算（AvatarRender.vue 129行）：**
```typescript
const userDigitalHumanContainerId = computed(() => {
  if (!currentUserRole.value) return ''  // 需要 AvatarRender.vue 的 currentUserRole 存在
  const roleId = `user:${currentUserRole.value.id}`
  return `digital-human-${toMd5(roleId)}`
})
```

---

## 数据流问题分析

### 问题：容器创建时 AvatarRender.vue 的 currentUserRole 可能未更新

**数据流断点：**
1. `ConfigPanel.vue` 的 `currentUserRole` 已更新（登录/切换时）
2. 触发 `roleUpdated` 事件
3. `AvatarRender.vue` 的 `handleRoleUpdated()` 异步执行 `loadCurrentUserRole()`
4. **连接时**：如果 `AvatarRender.vue` 的 `currentUserRole` 还未更新完成，容器不会创建

**原因：**
- 容器创建条件需要 `currentUserRole` 存在（AvatarRender.vue 20行）
- 容器ID计算需要 `currentUserRole.value.id`（AvatarRender.vue 129行）
- 连接时直接设置 `showUserDigitalHuman = true`，但 `currentUserRole` 可能还是 null 或旧值

**解决方案：**
连接前确保 `AvatarRender.vue` 的 `currentUserRole` 已更新：
- 方案1：连接前触发 `roleUpdated` 事件并等待处理完成
- 方案2：连接前直接调用 `loadCurrentUserRole()` 并等待完成

