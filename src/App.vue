<template>
  <div id="app">
    <button v-if="currentPage !== 'home'" @click="goHome" class="home-btn">🏠 返回首页</button>
    <Home v-if="currentPage === 'home'" @select="handleSelect" />
    <ImageProcessor v-else-if="currentPage === 'imageprocessor'" />
    <Wanwu v-else-if="currentPage === 'wanwu'" />
    <GAN v-else-if="currentPage === 'gan'" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Home from './components/Home.vue'
import ImageProcessor from './components/ImageProcessor.vue'
import Wanwu from './components/Wanwu.vue'
import GAN from './components/GAN.vue'

const currentPage = ref('home')

function handleSelect(type) {
  currentPage.value = type
}

function goHome() {
  currentPage.value = 'home'
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: #f5f5f5;
}

.home-btn {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1000;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-size: 1em;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}
</style>
