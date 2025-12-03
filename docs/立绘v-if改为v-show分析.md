# 立绘 v-if 改为 v-show 分析

## 一、当前实现

### 1.1 立绘容器定义

```vue
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
```

### 1.2 显示条件分析

**条件1：** `showPartnerIllustration` - 用户手动控制显示/隐藏
**条件2：** `currentPartnerRoleType === 'illustration'` - 角色类型必须是立绘
**条件3：** `currentPartnerRoleAvatar` - 角色必须有头像

## 二、v-if vs v-show 的区别

### 2.1 v-if 的特点

- **条件为 false 时**：元素不会被渲染到 DOM 中（完全移除）
- **条件为 true 时**：元素被创建并渲染到 DOM 中
- **切换成本**：需要创建/销毁 DOM 元素
- **内存占用**：隐藏时不占用 DOM 内存

### 2.2 v-show 的特点

- **条件为 false 时**：元素仍然在 DOM 中，只是通过 CSS `display: none` 隐藏
- **条件为 true 时**：元素显示（移除 `display: none`）
- **切换成本**：只需要切换 CSS 属性，很快
- **内存占用**：隐藏时仍然占用 DOM 内存

## 三、改为 v-show 的影响分析

### 3.1 优点

1. **切换速度更快**：
   - 不需要重新创建 DOM 元素
   - 不需要重新绑定事件监听器
   - 只需要切换 CSS `display` 属性

2. **事件监听器保持**：
   - `@mousedown="startDragPartner($event)"` 不需要重新绑定
   - 拖拽相关的事件监听器保持有效

3. **样式计算保持**：
   - `partnerAvatarPositionStyle` 计算属性保持有效
   - 不需要重新计算样式

### 3.2 缺点和风险

1. **角色类型切换问题**：
   - 当前条件包含 `currentPartnerRoleType === 'illustration'`
   - 如果改为 `v-show`，从立绘角色切换到数字人角色时：
     - 立绘容器不会销毁，只是隐藏
     - 容器仍然占用 DOM 内存
     - 可能导致内存泄漏（如果图片很大）

2. **角色切换时的容器残留**：
   - 从角色A（立绘）切换到角色B（数字人）：
     - 角色A的立绘容器仍然存在（只是隐藏）
     - 如果频繁切换角色，会有多个隐藏的容器残留

3. **头像变化时的处理**：
   - 如果 `currentPartnerRoleAvatar` 从有变为无：
     - 容器不会销毁，只是隐藏
     - 如果头像很大，仍然占用内存

4. **与数字人的不一致**：
   - 数字人使用 `v-show` 是因为需要保持 SDK 连接状态
   - 立绘不需要保持连接状态，使用 `v-if` 更合理

### 3.3 关键问题

**问题1：角色类型切换时的容器处理**

当前实现（v-if）：
- 从立绘角色切换到数字人角色：立绘容器被销毁 ✅
- 从数字人角色切换到立绘角色：立绘容器被创建 ✅

如果改为 v-show：
- 从立绘角色切换到数字人角色：立绘容器仍然存在（只是隐藏）⚠️
- 从数字人角色切换到立绘角色：立绘容器显示（如果之前存在）⚠️

**问题2：显示条件的复杂性**

当前条件包含三个部分：
1. `showPartnerIllustration` - 用户控制
2. `currentPartnerRoleType === 'illustration'` - 角色类型
3. `currentPartnerRoleAvatar` - 头像存在

如果改为 `v-show`，需要确保：
- 当角色类型变化时，容器应该被隐藏（但不能销毁）
- 当头像变化时，容器应该被隐藏（但不能销毁）

这可能导致容器在不需要时仍然存在。

## 四、建议

### 4.1 不建议改为 v-show

**理由：**

1. **立绘的特点**：
   - 静态图片，创建/销毁成本低
   - 不需要保持连接状态
   - 使用 `v-if` 更符合语义（条件渲染）

2. **显示条件的复杂性**：
   - 条件包含角色类型判断
   - 当角色类型变化时，容器应该销毁，而不是隐藏
   - 使用 `v-if` 可以自动处理这种情况

3. **内存管理**：
   - 立绘图片可能很大
   - 使用 `v-if` 可以确保不需要时完全移除，释放内存
   - 使用 `v-show` 可能导致内存占用增加

4. **与数字人的区别**：
   - 数字人使用 `v-show` 是因为需要保持 SDK 连接状态
   - 立绘不需要保持连接状态，使用 `v-if` 更合理

### 4.2 如果必须改为 v-show

**需要处理的问题：**

1. **分离显示条件**：
   ```vue
   <!-- 容器创建条件：只依赖角色类型和头像 -->
   <div 
     v-if="currentPartnerRoleType === 'illustration' && currentPartnerRoleAvatar"
     class="illustration-container"
     v-show="showPartnerIllustration"
   >
   ```

2. **确保角色切换时清理**：
   - 在角色切换时，需要手动清理旧的容器
   - 或者使用 `key` 属性强制重新渲染

3. **内存管理**：
   - 需要确保图片在隐藏时不会占用过多内存
   - 可能需要使用 `loading="lazy"` 或其他优化

## 五、结论

**不建议将立绘的 `v-if` 改为 `v-show`**，原因：

1. ✅ 立绘是静态图片，创建/销毁成本低
2. ✅ 显示条件包含角色类型判断，使用 `v-if` 更合理
3. ✅ 可以确保不需要时完全移除，释放内存
4. ✅ 与数字人的区别是合理的（数字人需要保持连接状态）

**如果确实需要改为 `v-show`**（例如为了性能优化），需要：
1. 分离容器创建条件和显示条件
2. 确保角色切换时正确处理容器
3. 考虑内存管理问题

