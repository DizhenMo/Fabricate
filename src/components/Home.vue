<template>
  <div class="home-container">
    <div class="home-header">
      <h1>Fabricate</h1>
      <p class="subtitle">请选择要使用的模块</p>
    </div>

    <div class="card-container">
      <div class="card" @click="selectProcessor('imageprocessor')">
        <div class="card-icon">🎨</div>
        <h2>标记移除</h2>
        <p>使用FLUX扩散模型进行图像处理</p>
        <div class="card-features">
          <span>✨ 图像分割</span>
          <span>🎯 目标检测</span>
          <span>🌈 风格转换</span>
        </div>
        <button class="card-btn">进入</button>
      </div>

      <div class="card" @click="selectProcessor('wanwu')">
        <div class="card-icon">🔮</div>
        <h2>分割移除</h2>
        <p>使用U-net模型自动分割进行处理</p>
        <div class="card-features">
          <span>🗑️ 物体移除</span>
          <span>🎭 背景处理</span>
          <span>✨ 智能填充</span>
        </div>
        <button class="card-btn">进入</button>
      </div>

      <div class="card" @click="selectProcessor('gan')">
        <div class="card-icon">🤖</div>
        <h2>GAN模型</h2>
        <p>使用GAN模型进行图像处理</p>
        <div class="card-features">
          <span>🎨 图像处理</span>
          <span>🔄 风格转换</span>
          <span>✨ 智能增强</span>
        </div>
        <button class="card-btn">进入</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['select'])

function selectProcessor(type) {
  emit('select', type)
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.home-header {
  text-align: left;
  margin-bottom: 50px;
  color: white;
}

.home-header h1 {
  font-size: 3em;
  margin: 0 0 15px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.subtitle {
  font-size: 1.3em;
  opacity: 0.9;
  margin: 0;
}

.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  max-width: 800px;
  width: 100%;
}

.card {
  background: white;
  border-radius: 20px;
  padding: 40px 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.card:hover::before {
  transform: scaleX(1);
}

.card-icon {
  font-size: 4em;
  margin-bottom: 20px;
}

.card h2 {
  font-size: 1.8em;
  color: #333;
  margin: 0 0 15px;
}

.card p {
  color: #666;
  font-size: 1em;
  margin: 0 0 20px;
  line-height: 1.5;
}

.card-features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-bottom: 25px;
}

.card-features span {
  background: #f0f0f0;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  color: #555;
}

.card-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 40px;
  border-radius: 25px;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}

.card-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

@media (max-width: 600px) {
  .home-header h1 {
    font-size: 2em;
  }

  .card-container {
    grid-template-columns: 1fr;
  }
}
</style>
