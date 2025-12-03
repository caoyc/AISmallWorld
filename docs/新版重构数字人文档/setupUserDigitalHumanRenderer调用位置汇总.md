# setupUserDigitalHumanRenderer 调用位置汇总

## 调用位置1：watch 监听 appState.llm.user 和 appState.llm.apiKey 变化

**文件：** `src/components/AvatarRender.vue`  
**行号：** 297-301

```typescript:297:301:src/components/AvatarRender.vue
// 监听 user 和 apiKey 变化，重新加载角色
watch([() => appState.llm.user, () => appState.llm.apiKey], async () => {
  await loadCurrentPartnerRole()
  await setupPartnerDigitalHumanRenderer(appState.currentPartnerRole)
  await setupUserDigitalHumanRenderer(appState.currentUserRole)
}, { immediate: true })
```

**触发条件：** `appState.llm.user` 或 `appState.llm.apiKey` 发生变化

**问题：** 如果 `handleConnectRoleFromList` 修改了 `appState.llm.user` 或 `appState.llm.apiKey`，会触发此 watch，导致 `setupUserDigitalHumanRenderer` 被调用

---

## 调用位置2：handleRoleUpdated 事件监听器

**文件：** `src/components/AvatarRender.vue`  
**行号：** 304-308

```typescript:304:308:src/components/AvatarRender.vue
// 监听角色更新事件，重新加载当前角色
const handleRoleUpdated = async () => {
  // 不再需要 loadCurrentPartnerRole 和 loadCurrentUserRole，因为 appState.currentUserRole 和 appState.currentPartnerRole 只在入口处修改
  await setupPartnerDigitalHumanRenderer(appState.currentPartnerRole)
  await setupUserDigitalHumanRenderer(appState.currentUserRole)
}
```

**注册位置：** 第323行
```typescript:323:323:src/components/AvatarRender.vue
window.addEventListener('roleUpdated', handleRoleUpdated)
```

**触发条件：** 其他地方调用 `window.dispatchEvent(new CustomEvent('roleUpdated'))`

**问题：** 如果 `handleConnectRoleFromList` 触发了 `roleUpdated` 事件，会调用 `setupUserDigitalHumanRenderer`

---

## 调用位置3：watch 监听 appState.currentUserRole 引用变化

**文件：** `src/components/AvatarRender.vue`  
**行号：** 316-318

```typescript:316:318:src/components/AvatarRender.vue
// 监听用户角色变化
watch(() => appState.currentUserRole, async (newRole) => {
  await setupUserDigitalHumanRenderer(newRole)
})
```

**触发条件：** `appState.currentUserRole` 的引用发生变化（不是属性变化）

**问题：** 如果 `handleConnectRoleFromList` 修改了 `appState.currentUserRole` 的引用，会触发此 watch

---

## 总结

**所有调用位置：**
1. ✅ **watch([() => appState.llm.user, () => appState.llm.apiKey], ...)** - 监听 user 和 apiKey 变化
2. ✅ **handleRoleUpdated()** - 监听 roleUpdated 事件
3. ✅ **watch(() => appState.currentUserRole, ...)** - 监听用户角色引用变化

**需要检查：**
- `handleConnectRoleFromList` 是否修改了 `appState.llm.user` 或 `appState.llm.apiKey`？
- `handleConnectRoleFromList` 是否触发了 `roleUpdated` 事件？
- `handleConnectRoleFromList` 是否修改了 `appState.currentUserRole` 的引用？

---

## 关键发现：SDK实例限制问题

**问题描述：** 一个数字人SDK实例应该只能接一个数字人。

**当前实现：**
- 每次调用 `DigitalHumanService.connect()` 都会创建新的 `new window.XmovAvatar(constructorOptions)` 实例
- 用户角色和伙伴角色使用不同的容器ID（`digital-human-user` 和 `digital-human-partner`）
- 每个 `DigitalHumanRenderer` 都有自己的 `instance` 属性

**可能的问题：**
- 如果SDK底层（`window.XmovAvatar`）只支持一个全局实例，那么：
  - 当连接伙伴角色时，创建新的SDK实例可能会覆盖或影响已连接的用户角色数字人
  - 这可能导致用户角色数字人消失（容器完全消失）

**代码位置：**
- `src/renderers/digital-human/DigitalHumanService.ts:87` - `avatar = new window.XmovAvatar(constructorOptions)`
- `src/renderers/digital-human/DigitalHumanRenderer.ts:82-89` - `this.instance = await this.service.connect(...)`

**需要验证：**
- SDK是否支持多个实例同时存在？
- 如果只支持一个实例，是否需要先断开用户角色数字人，再连接伙伴角色数字人？

---

## 关键问题：setupUserDigitalHumanRenderer 的逻辑缺陷

**问题描述：** `setupUserDigitalHumanRenderer` 函数在重新创建渲染器时，不会恢复 `showDigitalHuman = true`。

**函数逻辑：**
1. 先销毁旧的渲染器，并清理状态（`showDigitalHuman = false`、`isConnected = false`、`digitalHumanInstance = null`）
2. 如果角色是数字人类型，创建新的渲染器
3. **但是，它不会恢复 `showDigitalHuman = true`！**

**问题场景：**
- 用户角色数字人已经连接并显示（`showDigitalHuman = true`、`isConnected = true`）
- 如果 `setupUserDigitalHumanRenderer` 被调用（无论什么原因）
- 它会先清理状态（`showDigitalHuman = false`）
- 然后创建新的渲染器，但不会恢复 `showDigitalHuman = true`
- 导致容器消失（因为模板中的 `v-if="appState.currentUserRole?.showDigitalHuman"` 为 `false`）

**代码位置：**
- `src/components/AvatarRender.vue:234-294` - `setupUserDigitalHumanRenderer` 函数

**关键代码：**
```typescript:243:250:src/components/AvatarRender.vue
// 清理角色对象上的状态
appState.currentUserRole.showDigitalHuman = false  // ⚠️ 清理显示状态
appState.currentUserRole.digitalHumanInstance = null
appState.currentUserRole.isConnected = false

// 销毁渲染器
rendererManager.destroyRenderer(roleId)
userDigitalHumanRenderer.value = null
```

**然后创建新渲染器，但不会恢复 `showDigitalHuman = true`：**
```typescript:253:284:src/components/AvatarRender.vue
// 如果角色是数字人类型，创建渲染器
if (role && role.type === 'digital_human') {
  // ... 创建渲染器 ...
  userDigitalHumanRenderer.value = renderer
  // ⚠️ 没有恢复 showDigitalHuman = true
}
```

**需要检查：**
- 为什么连接伙伴角色时会触发 `setupUserDigitalHumanRenderer`？
- 如果必须调用，是否应该恢复已连接角色的 `showDigitalHuman = true`？

