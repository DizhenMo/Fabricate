<template>
  <div class="gan-processor">
    <div class="processor-header">
      <h1>🎨 GAN图像修复</h1>
      <p class="subtitle">上传图片并绘制掩码，选择模型和参数进行图像修复</p>
    </div>

    <div class="processor-content">
      <div class="main-layout">
        <section class="upload-section">
          <h2>📤 图片上传</h2>
          <div
            class="upload-area"
            :class="{ 'drag-over': isDragOver, 'has-file': uploadedImage }"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/jpg"
              @change="handleFileSelect"
              hidden
            />
            <div v-if="!uploadedImage" class="upload-placeholder">
              <div class="upload-icon">🖼️</div>
              <p>点击或拖拽图片到此处</p>
              <p class="upload-hint">支持 JPG、PNG 格式，最大 10MB</p>
            </div>
            <div v-else class="image-preview">
              <img :src="uploadedImage" alt="预览图片" />
              <button class="remove-btn" @click.stop="removeImage">✕</button>
            </div>
          </div>
          <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
        </section>

        <section class="mask-section">
          <h2>🎭 掩码绘制</h2>

          <div class="mask-tools">
            <div class="tool-bar">
              <button
                class="tool-btn"
                :class="{ active: drawingMode === 'brush' }"
                @click="drawingMode = 'brush'"
                title="画笔"
              >
                🖌️ 画笔
              </button>
              <button
                class="tool-btn"
                :class="{ active: drawingMode === 'eraser' }"
                @click="drawingMode = 'eraser'"
                title="橡皮擦"
              >
                🧹 橡皮擦
              </button>
              <button
                class="tool-btn"
                @click="clearMask"
                title="清空掩码"
              >
                🗑️ 清空
              </button>
            </div>

            <div class="brush-size-control">
              <label>画笔大小:</label>
              <input
                type="range"
                v-model="brushSize"
                min="5"
                max="50"
                step="1"
              />
              <span>{{ brushSize }}px</span>
            </div>
          </div>

          <div class="canvas-container" ref="canvasContainer">
            <canvas
              ref="maskCanvas"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
              @touchstart.prevent="handleTouchStart"
              @touchmove.prevent="handleTouchMove"
              @touchend.prevent="stopDrawing"
            ></canvas>
            <div v-if="!uploadedImage" class="canvas-placeholder">
              请先上传图片
            </div>
          </div>

          <div class="mask-upload">
            <h3>或上传掩码图片</h3>
            <div
              class="upload-area small"
              :class="{ 'has-file': uploadedMaskImage }"
              @click="triggerMaskInput"
            >
              <input
                ref="maskFileInput"
                type="file"
                accept="image/png"
                @change="handleMaskFileSelect"
                hidden
              />
              <div v-if="!uploadedMaskImage" class="upload-placeholder small">
                <div class="upload-icon">📤</div>
                <p>点击上传PNG掩码</p>
              </div>
              <div v-else class="mask-preview">
                <img :src="uploadedMaskImage" alt="掩码预览" />
                <button class="remove-btn small" @click.stop="removeMaskImage">✕</button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section class="settings-section">
        <h2>⚙️ 参数设置</h2>

        <div class="settings-grid">
          <div class="setting-item">
            <label>修补模型选择:</label>
            <select v-model="selectedModel">
              <option value="人脸修复(基于FFHQ[7w张图]--最优)">
                人脸修复(基于FFHQ[7w张图]--最优)
              </option>
              <option value="通用修复(基于ImageNet[100w张图])">
                通用修复(基于ImageNet[100w张图])
              </option>
              <option value="风景修复(基于Places2[180w张图])">
                风景修复(基于Places2[180w张图])
              </option>
            </select>
          </div>

          <div class="setting-item">
            <label>截断值 psi (0-1): {{ psiValue }}</label>
            <input
              type="range"
              v-model="psiValue"
              min="0"
              max="1"
              step="0.1"
            />
          </div>

          <div class="setting-item">
            <label>噪声值 noise (0-9): {{ noiseValue }}</label>
            <input
              type="range"
              v-model="noiseValue"
              min="0"
              max="9"
              step="1"
            />
          </div>
        </div>
      </section>

      <section class="actions-section">
        <button
          class="action-btn primary"
          :disabled="!canProcess || isProcessing"
          @click="processImage"
        >
          {{ isProcessing ? '处理中...' : '🚀 开始修复' }}
        </button>
        <button
          class="action-btn secondary"
          :disabled="isProcessing"
          @click="clearAll"
        >
          🗑️ 清空全部
        </button>
      </section>

      <section v-if="isProcessing" class="loading-section">
        <div class="spinner"></div>
        <p>正在处理图片，请稍候...</p>
      </section>

      <section v-if="error" class="error-section">
        <p class="error-text">{{ error }}</p>
      </section>

      <section v-if="resultData" class="result-section">
        <h2>📊 修复结果</h2>

        <div class="result-grid">
          <div class="result-item">
            <h3>原始输入图像</h3>
            <img v-if="resultData[0]" :src="resultData[0]" alt="原始输入" />
            <p v-else class="no-image">无</p>
          </div>

          <div class="result-item">
            <h3>修复结果图</h3>
            <img v-if="resultData[1]" :src="resultData[1]" alt="修复结果" />
            <p v-else class="no-image">无</p>
          </div>
        </div>

        <div class="result-info">
          <div class="info-item">
            <h3>📝 服务器日志</h3>
            <pre class="log-content">{{ resultData[2] || '无' }}</pre>
          </div>

          <div class="info-item">
            <h3>📈 评估指标</h3>
            <pre class="metrics-content">{{ resultData[3] || '无' }}</pre>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import axios from 'axios'

const fileInput = ref(null)
const maskFileInput = ref(null)
const maskCanvas = ref(null)
const canvasContainer = ref(null)

const uploadedImage = ref(null)
const uploadedFile = ref(null)
const uploadedMaskImage = ref(null)
const uploadedMaskFile = ref(null)
const isDragOver = ref(false)
const uploadError = ref('')

const drawingMode = ref('brush')
const brushSize = ref(20)
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)

const selectedModel = ref('人脸修复(基于FFHQ[7w张图]--最优)')
const psiValue = ref(0.5)
const noiseValue = ref(2)

const isProcessing = ref(false)
const error = ref('')
const resultData = ref(null)

const API_URL = 'http://fortunefreedom.top:9091/'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']

const canProcess = computed(() => {
  return uploadedFile.value && (uploadedMaskImage.value || hasDrawnMask())
})

function hasDrawnMask() {
  if (!maskCanvas.value) return false
  const ctx = maskCanvas.value.getContext('2d')
  const imageData = ctx.getImageData(0, 0, maskCanvas.value.width, maskCanvas.value.height)
  return imageData.data.some((value, index) => index % 4 === 3 && value > 0)
}

function triggerFileInput() {
  fileInput.value.click()
}

function triggerMaskInput() {
  maskFileInput.value.click()
}

function validateFile(file) {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return '不支持的文件格式，请上传 JPG 或 PNG 格式的图片'
  }
  if (file.size > MAX_FILE_SIZE) {
    return '文件大小超过限制（最大 10MB）'
  }
  return null
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    processFile(file)
  }
}

function handleDrop(event) {
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    processFile(file)
  } else {
    uploadError.value = '请上传图片文件'
  }
}

function processFile(file) {
  uploadError.value = ''
  error.value = ''

  const errorMsg = validateFile(file)
  if (errorMsg) {
    uploadError.value = errorMsg
    return
  }

  uploadedFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
    nextTick(() => {
      setupCanvas()
    })
  }
  reader.readAsDataURL(file)
}

function removeImage() {
  uploadedImage.value = null
  uploadedFile.value = null
  resultData.value = null
  error.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  clearMask()
}

function handleMaskFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    processMaskFile(file)
  }
}

function processMaskFile(file) {
  if (file.type !== 'image/png') {
    error.value = '掩码图片必须是 PNG 格式'
    return
  }

  uploadedMaskFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedMaskImage.value = e.target.result
    loadMaskImageToCanvas(e.target.result)
  }
  reader.readAsDataURL(file)
}

function removeMaskImage() {
  uploadedMaskImage.value = null
  uploadedMaskFile.value = null
  if (maskFileInput.value) {
    maskFileInput.value.value = ''
  }
  clearMask()
}

function setupCanvas() {
  if (!uploadedImage.value || !maskCanvas.value) return

  const img = new Image()
  img.onload = () => {
    const canvas = maskCanvas.value
    const container = canvasContainer.value

    const maxWidth = container.clientWidth - 20
    const maxHeight = 400

    let width = img.width
    let height = img.height

    if (width > maxWidth) {
      height = (maxWidth / width) * height
      width = maxWidth
    }

    if (height > maxHeight) {
      width = (maxHeight / height) * width
      height = maxHeight
    }

    canvas.width = width
    canvas.height = height
    canvas.style.width = width + 'px'
    canvas.style.height = height + 'px'

    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0, width, height)
    ctx.fillStyle = 'white'
  }
  img.src = uploadedImage.value
}

function loadMaskImageToCanvas(maskSrc) {
  if (!uploadedImage.value || !maskCanvas.value) return

  const img = new Image()
  img.onload = () => {
    const canvas = maskCanvas.value
    const ctx = canvas.getContext('2d')

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  }
  img.src = maskSrc
}

function getCanvasCoords(event) {
  const canvas = maskCanvas.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height

  if (event.touches) {
    return {
      x: (event.touches[0].clientX - rect.left) * scaleX,
      y: (event.touches[0].clientY - rect.top) * scaleY
    }
  }

  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY
  }
}

function startDrawing(event) {
  if (!uploadedImage.value) return
  isDrawing.value = true
  const coords = getCanvasCoords(event)
  lastX.value = coords.x
  lastY.value = coords.y
}

function draw(event) {
  if (!isDrawing.value || !uploadedImage.value) return

  const canvas = maskCanvas.value
  const ctx = canvas.getContext('2d')
  const coords = getCanvasCoords(event)

  ctx.beginPath()
  ctx.arc(coords.x, coords.y, brushSize.value, 0, Math.PI * 2)

  if (drawingMode.value === 'brush') {
    ctx.fillStyle = 'rgba(0, 0, 0, 1)'
  } else {
    ctx.fillStyle = 'rgba(255, 255, 255, 1)'
  }

  ctx.fill()
  ctx.closePath()

  lastX.value = coords.x
  lastY.value = coords.y
}

function stopDrawing() {
  isDrawing.value = false
}

function handleTouchStart(event) {
  startDrawing(event)
}

function handleTouchMove(event) {
  draw(event)
}

function clearMask() {
  if (!maskCanvas.value || !uploadedImage.value) return

  const canvas = maskCanvas.value
  const ctx = canvas.getContext('2d')

  const img = new Image()
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  }
  img.src = uploadedImage.value
}

async function processImage() {
  if (!canProcess.value) {
    error.value = '请上传图片和掩码'
    return
  }

  isProcessing.value = true
  error.value = ''
  resultData.value = null

  try {
    const canvas = maskCanvas.value
    const maskBlob = await new Promise(resolve => {
      canvas.toBlob(resolve, 'image/png')
    })

    const formData = new FormData()
    formData.append('input_image', uploadedFile.value, 'input_image.png')
    formData.append('input_mask', maskBlob, 'input_mask.png')
    formData.append('slider_1', psiValue.value)
    formData.append('slider_2', noiseValue.value)
    formData.append('radio', selectedModel.value)

    const urls = [
      `${API_URL}process_image`,
      `${API_URL}api/predict/process_image`,
      `${API_URL}v1/predict/process_image`
    ]

    let result = null
    let lastError = null

    for (const url of urls) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
          mode: 'cors'
        })

        if (response.ok) {
          result = await response.json()
          break
        }
        lastError = `${response.status} ${response.statusText}`
      } catch (e) {
        lastError = e.message
      }
    }

    if (result && result.data) {
      resultData.value = result.data
    } else if (result && result.error) {
      error.value = `API错误: ${result.error}`
    } else if (result) {
      resultData.value = result
    } else {
      error.value = `无法连接到API服务器，最后错误: ${lastError || '未知错误'}`
    }
  } catch (err) {
    console.error('API Error:', err)
    error.value = `处理失败: ${err.message || '请检查网络连接和API服务状态'}`
  } finally {
    isProcessing.value = false
  }
}

function clearAll() {
  removeImage()
  removeMaskImage()
  selectedModel.value = '人脸修复(基于FFHQ[7w张图]--最优)'
  psiValue.value = 0.5
  noiseValue.value = 2
  resultData.value = null
  error.value = ''
}

watch(uploadedImage, () => {
  if (uploadedImage.value) {
    nextTick(() => {
      setupCanvas()
    })
  }
})
</script>

<style scoped>
.gan-processor {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.processor-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.processor-header h1 {
  margin: 0;
  font-size: 2em;
}

.subtitle {
  margin: 10px 0 0;
  opacity: 0.9;
}

.processor-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}

.upload-section,
.mask-section,
.settings-section,
.actions-section,
.result-section,
.loading-section,
.error-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h2 {
  margin: 0 0 15px;
  font-size: 1.3em;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
}

h3 {
  margin: 10px 0;
  font-size: 1.1em;
  color: #555;
}

.upload-area {
  border: 3px dashed #ddd;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area.small {
  min-height: 120px;
  padding: 15px;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.upload-area.drag-over {
  border-color: #667eea;
  background: #e8eaff;
}

.upload-area.has-file {
  border-style: solid;
  border-color: #667eea;
}

.upload-placeholder {
  color: #666;
}

.upload-placeholder.small {
  font-size: 0.9em;
}

.upload-icon {
  font-size: 3em;
  margin-bottom: 10px;
}

.upload-placeholder.small .upload-icon {
  font-size: 2em;
}

.upload-hint {
  font-size: 0.9em;
  color: #999;
  margin-top: 5px;
}

.image-preview,
.mask-preview {
  position: relative;
  max-width: 100%;
}

.image-preview img,
.mask-preview img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
}

.remove-btn {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: #ff4757;
  color: white;
  cursor: pointer;
  font-size: 1.2em;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn.small {
  width: 24px;
  height: 24px;
  font-size: 1em;
}

.remove-btn:hover {
  background: #ff3344;
}

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: #ffebee;
  border-radius: 6px;
  color: #c62828;
  text-align: center;
}

.mask-tools {
  margin-bottom: 15px;
}

.tool-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.tool-btn {
  padding: 8px 16px;
  border: 2px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9em;
}

.tool-btn:hover {
  border-color: #667eea;
  background: #f0f0ff;
}

.tool-btn.active {
  border-color: #667eea;
  background: #667eea;
  color: white;
}

.brush-size-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brush-size-control label {
  font-size: 0.9em;
  color: #666;
}

.brush-size-control input[type="range"] {
  flex: 1;
  max-width: 200px;
}

.brush-size-control span {
  font-size: 0.9em;
  color: #333;
  min-width: 50px;
}

.canvas-container {
  position: relative;
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mask-section canvas {
  cursor: crosshair;
  border-radius: 4px;
}

.canvas-placeholder {
  color: #999;
  font-size: 1.1em;
}

.mask-upload {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.mask-upload h3 {
  font-size: 1em;
  color: #666;
  margin-bottom: 10px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-item label {
  font-weight: 600;
  color: #333;
}

.setting-item select {
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  cursor: pointer;
}

.setting-item select:focus {
  outline: none;
  border-color: #667eea;
}

.setting-item input[type="range"] {
  width: 100%;
  cursor: pointer;
}

.actions-section {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.action-btn {
  padding: 15px 40px;
  border: none;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.action-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.secondary {
  background: #f0f0f0;
  color: #666;
}

.action-btn.secondary:hover:not(:disabled) {
  background: #e0e0e0;
}

.action-btn.secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-section {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-section {
  background: #ffebee;
}

.error-text {
  color: #c62828;
  margin: 0;
  text-align: center;
}

.result-section h2 {
  margin-bottom: 20px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.result-item {
  text-align: center;
}

.result-item h3 {
  color: #555;
  margin-bottom: 10px;
}

.result-item img {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  border: 2px solid #ddd;
}

.no-image {
  color: #999;
  font-style: italic;
}

.result-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 768px) {
  .result-info {
    grid-template-columns: 1fr;
  }
}

.info-item {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 15px;
}

.info-item h3 {
  margin-bottom: 10px;
  color: #667eea;
}

.log-content,
.metrics-content {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  margin: 0;
  font-size: 0.9em;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 200px;
  overflow-y: auto;
}
</style>
