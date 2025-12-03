<script setup lang="ts">
import { provide, ref } from 'vue'
import Info from './components/ConfigPanel.vue'
import SdkRender from './components/AvatarRender.vue'
import { appState, appStore } from './stores/app'

// 立绘显示状态（全局共享）
const showUserIllustration = ref(false)
const showPartnerIllustration = ref(false)

// 提供全局状态和方法
provide('appState', appState)
provide('appStore', appStore)
provide('showUserIllustration', showUserIllustration)
provide('showPartnerIllustration', showPartnerIllustration)
</script>

<template>
  <div class="main">
    <SdkRender/>
    <Info />
  </div>
</template>

<style scoped>
.main {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}
</style>
