# setupUserDigitalHumanRenderer 和 setupPartnerDigitalHumanRenderer 实现差异对比

## 一、函数签名差异

### 1.1 setupPartnerDigitalHumanRenderer

```typescript:172:172:src/components/AvatarRender.vue
async function setupPartnerDigitalHumanRenderer(role: Role | null) {
```

**参数类型：** `Role | null`

### 1.2 setupUserDigitalHumanRenderer

```typescript:235:235:src/components/AvatarRender.vue
async function setupUserDigitalHumanRenderer(role: UserRole | null) {
```

**参数类型：** `UserRole | null`

**差异：** 参数类型不同（`Role` vs `UserRole`）

---

## 二、销毁旧渲染器逻辑差异

### 2.1 setupPartnerDigitalHumanRenderer

```typescript:176:187:src/components/AvatarRender.vue
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
```

**使用的变量：**
- `partnerDigitalHumanRenderer.value`
- `appState.currentPartnerRole`
- `roleId = partner:${appState.currentPartnerRole.user}`

### 2.2 setupUserDigitalHumanRenderer

```typescript:239:250:src/components/AvatarRender.vue
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
```

**使用的变量：**
- `userDigitalHumanRenderer.value`
- `appState.currentUserRole`
- `roleId = user:${appState.currentUserRole.id}`

**差异：**
- 使用的ref不同（`partnerDigitalHumanRenderer` vs `userDigitalHumanRenderer`）
- 使用的appState不同（`appState.currentPartnerRole` vs `appState.currentUserRole`）
- roleId格式不同（`partner:${role.user}` vs `user:${role.id}`）

---

## 三、创建渲染器逻辑差异

### 3.1 setupPartnerDigitalHumanRenderer

```typescript:192:202:src/components/AvatarRender.vue
const roleId = `partner:${role.user}`
const renderer = await rendererManager.createRenderer(roleId, {
  roleId,
  roleType: 'digital_human',
  positionX: role.positionX !== undefined ? role.positionX : 90,
  positionY: role.positionY !== undefined ? role.positionY : 50,
  scale: role.scale !== undefined ? role.scale : 1.0,
  avatarAppId: role.avatarAppId || '',
  avatarAppSecret: role.avatarAppSecret || '',
  containerId: 'digital-human-partner' // 固定容器ID
})
```

**关键差异：**
- `roleId = partner:${role.user}`
- `positionX` 默认值：`90`
- `containerId: 'digital-human-partner'`

### 3.2 setupUserDigitalHumanRenderer

```typescript:255:265:src/components/AvatarRender.vue
const roleId = `user:${role.id}`
const renderer = await rendererManager.createRenderer(roleId, {
  roleId,
  roleType: 'digital_human',
  positionX: role.positionX !== undefined ? role.positionX : 10,
  positionY: role.positionY !== undefined ? role.positionY : 50,
  scale: role.scale !== undefined ? role.scale : 1.0,
  avatarAppId: role.avatarAppId || '',
  avatarAppSecret: role.avatarAppSecret || '',
  containerId: 'digital-human-user' // 固定容器ID
})
```

**关键差异：**
- `roleId = user:${role.id}`
- `positionX` 默认值：`10`
- `containerId: 'digital-human-user'`

**差异：**
- roleId格式不同（`partner:${role.user}` vs `user:${role.id}`）
- positionX默认值不同（`90` vs `10`）
- containerId不同（`digital-human-partner` vs `digital-human-user`）

---

## 四、保存渲染器引用差异

### 4.1 setupPartnerDigitalHumanRenderer

```typescript:222:222:src/components/AvatarRender.vue
partnerDigitalHumanRenderer.value = renderer
```

### 4.2 setupUserDigitalHumanRenderer

```typescript:284:284:src/components/AvatarRender.vue
userDigitalHumanRenderer.value = renderer
```

**差异：** 保存到不同的ref（`partnerDigitalHumanRenderer` vs `userDigitalHumanRenderer`）

---

## 五、错误日志差异

### 5.1 setupPartnerDigitalHumanRenderer

```typescript:224:224:src/components/AvatarRender.vue
console.error('创建伙伴数字人渲染器失败:', error)
```

### 5.2 setupUserDigitalHumanRenderer

```typescript:286:286:src/components/AvatarRender.vue
console.error('创建用户数字人渲染器失败:', error)
```

**差异：** 错误日志文本不同（"伙伴" vs "用户"）

---

## 六、相同点

**两个函数的逻辑结构完全相同：**
1. ✅ 都先检查 `containerRef.value`
2. ✅ 都先销毁旧的渲染器并清理状态
3. ✅ 都检查角色类型是否为 `digital_human`
4. ✅ 都创建渲染器并设置回调函数
5. ✅ 都保存渲染器引用
6. ✅ 都在非数字人类型时隐藏容器

**回调函数完全相同：**
- `onSubtitleOn`、`onSubtitleOff`、`onStateChange` 的实现完全相同

---

## 七、总结

**差异汇总：**

| 项目 | setupPartnerDigitalHumanRenderer | setupUserDigitalHumanRenderer | 差异 |
|------|----------------------------------|-------------------------------|------|
| **参数类型** | `Role \| null` | `UserRole \| null` | ✅ 不同 |
| **roleId格式** | `partner:${role.user}` | `user:${role.id}` | ✅ 不同 |
| **容器ID** | `digital-human-partner` | `digital-human-user` | ✅ 不同 |
| **positionX默认值** | `90` | `10` | ✅ 不同 |
| **使用的ref** | `partnerDigitalHumanRenderer` | `userDigitalHumanRenderer` | ✅ 不同 |
| **使用的appState** | `appState.currentPartnerRole` | `appState.currentUserRole` | ✅ 不同 |
| **错误日志** | "创建伙伴数字人渲染器失败" | "创建用户数字人渲染器失败" | ✅ 不同 |

**相同点：**
- ✅ 逻辑结构完全相同
- ✅ 回调函数完全相同
- ✅ 错误处理逻辑完全相同

**结论：** 两个函数的实现逻辑完全相同，只是使用的变量、容器ID、默认位置不同。

