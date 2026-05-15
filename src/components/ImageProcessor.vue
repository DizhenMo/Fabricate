<template>
  <div class="image-processor">
    <div class="processor-header">
      <h1>图片处理工具</h1>
      <p class="subtitle">上传图片、添加标注、调用AI模型进行处理</p>
    </div>

    <div class="processor-content">
      <div class="left-panel">
        <section class="upload-section">
          <h2>📤 图片上传</h2>
          <div class="sample-section">
            <h3>📷 示例图片</h3>
            <div class="sample-images">
              <div class="sample-item">
                <img src="/samples/1/1.jpg" alt="示例1" @click="loadSampleImage('/samples/1/1.jpg')" />
                <span>示例1 - 输入</span>
              </div>
              <div class="sample-item">
                <img src="/samples/1/2.png" alt="示例2" @click="loadSampleImage('/samples/1/2.png')" />
                <span>示例2 - 输入</span>
              </div>
              <div class="sample-item">
                <img src="/samples/1/3.jpg" alt="示例3" @click="loadSampleImage('/samples/1/3.jpg')" />
                <span>示例3 - 输入</span>
              </div>
            </div>
          </div>
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

        <section class="canvas-section">
          <h2>✏️ 图片标注</h2>
          <div class="toolbar">
            <div class="tool-group">
              <span class="tool-label">绘制工具：</span>
              <button
                v-for="tool in drawingTools"
                :key="tool.id"
                :class="['tool-btn', { active: currentTool === tool.id }]"
                @click="currentTool = tool.id"
                :title="tool.name"
              >
                {{ tool.icon }}
              </button>
            </div>
            <div class="tool-group">
              <span class="tool-label">颜色：</span>
              <input type="color" v-model="strokeColor" class="color-picker" />
            </div>
            <div class="tool-group">
              <span class="tool-label">线宽：</span>
              <input
                type="range"
                v-model="strokeWidth"
                min="1"
                max="20"
                class="width-slider"
              />
              <span class="width-value">{{ strokeWidth }}px</span>
            </div>
            <button class="clear-btn" @click="clearCanvas">🗑️ 清空标注</button>
          </div>
          <div class="canvas-container" ref="canvasContainer">
            <canvas
              ref="drawingCanvas"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
              @touchstart.prevent="handleTouchStart"
              @touchmove.prevent="handleTouchMove"
              @touchend.prevent="stopDrawing"
            ></canvas>
          </div>
        </section>
      </div>

      <div class="right-panel">
        <section class="prompt-section">
          <h2>💬 Prompt 配置</h2>
          <div class="prompt-templates">
            <span class="tool-label">模板：</span>
            <select v-model="selectedTemplate" @change="applyTemplate" class="template-select">
              <option value="">选择Prompt模板</option>
              <option v-for="template in promptTemplates" :key="template.name" :value="template.name">
                {{ template.name }}
              </option>
            </select>
          </div>
          <textarea
            v-model="promptText"
            class="prompt-input"
            placeholder="输入你的prompt..."
            rows="8"
          ></textarea>
          <div class="prompt-actions">
            <button class="action-btn" @click="formatPrompt">✨ 格式化</button>
            <button class="action-btn" @click="resetPrompt">🔄 重置</button>
          </div>
          <div v-if="promptHistory.length > 0" class="history-section">
            <h3>📜 历史记录</h3>
            <div class="history-list">
              <div
                v-for="(history, index) in promptHistory"
                :key="index"
                class="history-item"
                @click="loadHistory(history)"
              >
                <span class="history-text">{{ history.text.substring(0, 50) }}...</span>
                <span class="history-time">{{ formatTime(history.time) }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="api-section">
          <h2>🚀 API 调用</h2>
          <button
            class="process-btn"
            :disabled="!canProcess || isProcessing"
            @click="processImage"
          >
            <span v-if="isProcessing" class="spinner">⏳</span>
            <span v-else>{{ isProcessing ? '处理中...' : '开始处理' }}</span>
          </button>
          <div v-if="isProcessing" class="progress-info">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <span class="progress-text">处理中... {{ progress }}%</span>
          </div>
          <div v-if="processTime" class="time-info">
            <span class="time-label">⏱️ 处理耗时：</span>
            <span class="time-value">{{ processTime }} 秒</span>
          </div>
          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
        </section>

        <section v-if="resultImage" class="result-section">
          <h2>✅ 处理结果</h2>
          <div class="result-image-container">
            <img :src="resultImage" alt="处理结果" class="result-image" />
          </div>
          <div class="result-actions">
            <button class="download-btn" @click="downloadResult">
              💾 手动下载
            </button>
            <button class="save-btn" @click="autoSaveResult">
              📥 自动保存
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'

const fileInput = ref(null)
const canvasContainer = ref(null)
const drawingCanvas = ref(null)

const uploadedImage = ref(null)
const uploadedFile = ref(null)
const isDragOver = ref(false)
const uploadError = ref('')

const currentTool = ref('freehand')
const strokeColor = ref('#ff0000')
const strokeWidth = ref(3)
const isDrawing = ref(false)
const drawingTools = [
  { id: 'freehand', name: '自由曲线', icon: '✏️' },
  { id: 'rectangle', name: '矩形', icon: '⬜' },
  { id: 'circle', name: '圆形', icon: '⭕' },
  { id: 'line', name: '直线', icon: '📏' }
]

const drawingContext = ref(null)
const lastPos = ref({ x: 0, y: 0 })
const startPos = ref({ x: 0, y: 0 })
const tempCanvas = ref(null)
const originalImageData = ref(null)

const promptText = ref('')
const selectedTemplate = ref('')
const promptHistory = ref([])
const promptTemplates = [
  {
    name: '目标移除',
    text: '请移除圈出的目标对象。'
  },
  {
    name: '目标检测',
    text: '请检测图像中的目标对象，标注出它们的位置和类别。'
  },
  {
    name: '图像增强',
    text: '请增强图像的细节和色彩，提高图像质量和清晰度。'
  },
  {
    name: '风格转换',
    text: '请将图像转换为指定的艺术风格，保持内容的同时改变视觉效果。'
  }
]

const isProcessing = ref(false)
const progress = ref(0)
const processTime = ref(null)
const successMessage = ref('')
const errorMessage = ref('')
const resultImage = ref(null)

const API_URL = ref('https://www.runninghub.cn/openapi/v2/run/ai-app/2042898453923110913')
const QUERY_URL = ref('https://www.runninghub.cn/openapi/v2/query')
const API_KEY = ref('cf6fc254954d4bc7ba8e4341dcd0b462')

const canProcess = computed(() => {
  return uploadedImage.value && promptText.value.trim() !== ''
})

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']

function triggerFileInput() {
  fileInput.value.click()
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
  const error = validateFile(file)
  if (error) {
    uploadError.value = error
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
  promptText.value = ''
  resultImage.value = null
  clearCanvas()
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function setupCanvas() {
  if (!drawingCanvas.value || !uploadedImage.value) return

  const canvas = drawingCanvas.value
  const container = canvasContainer.value
  const ctx = canvas.getContext('2d')

  const img = new Image()
  img.onload = () => {
    const maxWidth = container.clientWidth - 20
    const maxHeight = 500

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

    drawingContext.value = ctx
    ctx.drawImage(img, 0, 0, width, height)
    originalImageData.value = ctx.getImageData(0, 0, width, height)

    tempCanvas.value = document.createElement('canvas')
    tempCanvas.value.width = width
    tempCanvas.value.height = height
  }
  img.src = uploadedImage.value
}

function getCanvasCoords(event) {
  const canvas = drawingCanvas.value
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
  isDrawing.value = true
  const coords = getCanvasCoords(event)
  startPos.value = coords
  lastPos.value = coords

  if (currentTool.value === 'freehand') {
    drawingContext.value.beginPath()
    drawingContext.value.moveTo(coords.x, coords.y)
    drawingContext.value.strokeStyle = strokeColor.value
    drawingContext.value.lineWidth = strokeWidth.value
    drawingContext.value.lineCap = 'round'
    drawingContext.value.lineJoin = 'round'
  }
}

function draw(event) {
  if (!isDrawing.value) return

  const coords = getCanvasCoords(event)
  const ctx = drawingContext.value

  if (currentTool.value === 'freehand') {
    ctx.strokeStyle = strokeColor.value
    ctx.lineWidth = strokeWidth.value
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.lineTo(coords.x, coords.y)
    ctx.stroke()
  }

  lastPos.value = coords
}

function stopDrawing() {
  if (!isDrawing.value) return
  isDrawing.value = false

  const ctx = drawingContext.value

  if (currentTool.value !== 'freehand') {
    ctx.putImageData(originalImageData.value, 0, 0)
    ctx.strokeStyle = strokeColor.value
    ctx.lineWidth = strokeWidth.value
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    if (currentTool.value === 'rectangle') {
      const width = lastPos.value.x - startPos.value.x
      const height = lastPos.value.y - startPos.value.y
      ctx.strokeRect(startPos.value.x, startPos.value.y, width, height)
    } else if (currentTool.value === 'circle') {
      const radiusX = Math.abs(lastPos.value.x - startPos.value.x) / 2
      const radiusY = Math.abs(lastPos.value.y - startPos.value.y) / 2
      const centerX = startPos.value.x + (lastPos.value.x - startPos.value.x) / 2
      const centerY = startPos.value.y + (lastPos.value.y - startPos.value.y) / 2
      ctx.beginPath()
      ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI)
      ctx.stroke()
    } else if (currentTool.value === 'line') {
      ctx.beginPath()
      ctx.moveTo(startPos.value.x, startPos.value.y)
      ctx.lineTo(lastPos.value.x, lastPos.value.y)
      ctx.stroke()
    }

    originalImageData.value = ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height)
  }
}

function handleTouchStart(event) {
  startDrawing(event)
}

function handleTouchMove(event) {
  draw(event)
}

function clearCanvas() {
  if (drawingContext.value && originalImageData.value) {
    drawingContext.value.putImageData(originalImageData.value, 0, 0)
  }
}

function applyTemplate() {
  const template = promptTemplates.find(t => t.name === selectedTemplate.value)
  if (template) {
    promptText.value = template.text
  }
}

function formatPrompt() {
  if (promptText.value.trim()) {
    promptText.value = promptText.value.trim()
      .split(/[.!?]+/)
      .filter(s => s.trim())
      .map(s => s.trim())
      .join('。\n')
    if (!promptText.value.endsWith('。')) {
      promptText.value += '。'
    }
  }
}

function resetPrompt() {
  promptText.value = ''
  selectedTemplate.value = ''
}

function loadHistory(history) {
  promptText.value = history.text
}

async function loadSampleImage(imagePath) {
  try {
    const response = await fetch(imagePath)
    const blob = await response.blob()
    const file = new File([blob], imagePath.split('/').pop(), { type: blob.type })
    processFile(file)
  } catch (error) {
    uploadError.value = '加载示例图片失败'
  }
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function processImage() {
  if (!canProcess.value || isProcessing.value) return

  isProcessing.value = true
  progress.value = 0
  processTime.value = null
  successMessage.value = ''
  errorMessage.value = ''
  resultImage.value = null

  if (promptHistory.value.length >= 10) {
    promptHistory.value.pop()
  }
  promptHistory.value.unshift({
    text: promptText.value,
    time: Date.now()
  })

  const startTime = performance.now()

  try {
    const canvas = drawingCanvas.value
    
    // 创建一个新的canvas用于处理透明标记
    const resultCanvas = document.createElement('canvas')
    resultCanvas.width = canvas.width
    resultCanvas.height = canvas.height
    const ctx = resultCanvas.getContext('2d')
    
    // 绘制原始图片（没有标记的版本）
    ctx.putImageData(originalImageData.value, 0, 0)
    
    // 获取当前canvas的图像数据（包含标记）
    const currentImageData = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height)
    const currentData = currentImageData.data
    
    // 获取原始图片的图像数据
    const originalData = originalImageData.value.data
    
    // 获取结果canvas的图像数据
    const resultImageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const resultData = resultImageData.data
    
    // 遍历像素，将标记部分设为透明
    for (let i = 0; i < currentData.length; i += 4) {
      // 比较当前像素与原始像素
      const rCurrent = currentData[i]
      const gCurrent = currentData[i + 1]
      const bCurrent = currentData[i + 2]
      
      const rOriginal = originalData[i]
      const gOriginal = originalData[i + 1]
      const bOriginal = originalData[i + 2]
      
      // 计算颜色差异
      const diff = Math.abs(rCurrent - rOriginal) + Math.abs(gCurrent - gOriginal) + Math.abs(bCurrent - bOriginal)
      
      // 如果差异较大，认为是标记像素，设为透明
      if (diff > 30) {
        // 将标记部分设为透明
        resultData[i + 3] = 0
      }
    }
    
    // 将处理后的数据放回canvas
    ctx.putImageData(resultImageData, 0, 0)
    
    // 获取处理后的图片数据（PNG格式，支持透明）
    const annotatedImageData = resultCanvas.toDataURL('image/png')

    progress.value = 10

    const uploadUrl = 'https://www.runninghub.cn/openapi/v2/media/upload/binary'
    const uploadFormData = new FormData()
    uploadFormData.append('file', dataURLtoBlob(annotatedImageData), 'annotated.png')

    const uploadResponse = await axios.post(uploadUrl, uploadFormData, {
      headers: {
        'Authorization': `Bearer ${API_KEY.value}`
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded / progressEvent.total) * 30)
          progress.value = 10 + percentCompleted
        }
      }
    })

    if (!uploadResponse.data || uploadResponse.data.code !== 0) {
      throw new Error('图片上传失败: ' + (uploadResponse.data?.message || '未知错误'))
    }

    const imageUrl = uploadResponse.data.data.download_url
    progress.value = 40

    const payload = {
      nodeInfoList: [
        {
          nodeId: "213",
          fieldName: "image",
          fieldValue: imageUrl,
          description: "image"
        },
        {
          nodeId: "207",
          fieldName: "text",
          fieldValue: promptText.value,
          description: "text"
        }
      ],
      instanceType: "plus",
      usePersonalQueue: "false"
    }

    progress.value = 50

    const taskResponse = await axios.post(API_URL.value, payload, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY.value}`
      }
    })

    if (!taskResponse.data || !taskResponse.data.taskId) {
      throw new Error('任务提交失败: ' + (taskResponse.data?.errorMessage || '未知错误'))
    }

    const taskId = taskResponse.data.taskId
    progress.value = 60

    let taskStatus = 'QUEUED'
    let taskResult = null
    let retryCount = 0
    const maxRetries = 30

    while (retryCount < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      const queryResponse = await axios.post(QUERY_URL.value, { taskId }, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY.value}`
        }
      })

      if (!queryResponse.data) {
        throw new Error('查询任务状态失败')
      }

      taskStatus = queryResponse.data.status
      taskResult = queryResponse.data

      if (taskStatus === 'SUCCESS') {
        progress.value = 90
        break
      } else if (taskStatus === 'FAILED') {
        throw new Error('任务执行失败: ' + (taskResult.errorMessage || '未知错误'))
      } else if (taskStatus === 'RUNNING') {
        progress.value = Math.min(60 + (retryCount * 2), 80)
      }

      retryCount++
    }

    if (retryCount >= maxRetries) {
      throw new Error('任务执行超时，请稍后重试')
    }

    if (taskResult.results && taskResult.results.length > 0) {
      resultImage.value = taskResult.results[0].url
      successMessage.value = '✨ 图片处理成功！'
    } else {
      throw new Error('任务成功但未返回结果')
    }

    const endTime = performance.now()
    processTime.value = ((endTime - startTime) / 1000).toFixed(2)

    progress.value = 100

  } catch (error) {
    const endTime = performance.now()
    processTime.value = ((endTime - startTime) / 1000).toFixed(2)

    if (error.code === 'ECONNABORTED') {
      errorMessage.value = '请求超时，请检查网络连接后重试'
    } else {
      errorMessage.value = `处理失败: ${error.message}`
    }
  } finally {
    isProcessing.value = false
  }
}

function dataURLtoBlob(dataurl) {
  const arr = dataurl.split(',')
  const mime = arr[0].match(/:(.*?);/)[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  return new Blob([u8arr], { type: mime })
}

function downloadResult() {
  if (!resultImage.value) return

  const link = document.createElement('a')
  link.href = resultImage.value
  link.download = `processed_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function autoSaveResult() {
  if (!resultImage.value) return

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const filename = `Fabricate_${timestamp}.png`

  if (window.showSaveFilePicker) {
    const handle = window.showSaveFilePicker({
      suggestedName: filename,
      types: [{
        description: 'PNG Image',
        accept: { 'image/png': ['.png'] }
      }]
    })
  } else {
    downloadResult()
  }
}

onMounted(() => {
  if (uploadedImage.value) {
    nextTick(() => {
      setupCanvas()
    })
  }
})
</script>

<style scoped>
.image-processor {
  max-width: 1400px;
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1024px) {
  .processor-content {
    grid-template-columns: 1fr;
  }
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

section h2 {
  margin: 0 0 15px;
  font-size: 1.3em;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
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

.sample-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9ff;
  border-radius: 8px;
  border: 1px solid #e8eaff;
}

.sample-section h3 {
  margin: 0 0 15px;
  font-size: 1.1em;
  color: #333;
}

.sample-images {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 10px;
}

.sample-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.sample-item:hover {
  transform: scale(1.05);
}

.sample-item img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid #ddd;
  transition: border-color 0.2s;
}

.sample-item:hover img {
  border-color: #667eea;
}

.sample-item span {
  margin-top: 5px;
  font-size: 0.85em;
  color: #666;
  text-align: center;
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

.upload-icon {
  font-size: 3em;
  margin-bottom: 10px;
}

.upload-hint {
  font-size: 0.9em;
  color: #999;
  margin-top: 5px;
}

.image-preview {
  position: relative;
  max-width: 100%;
}

.image-preview img {
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

.remove-btn:hover {
  background: #ff3344;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 8px;
  align-items: center;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-label {
  font-size: 0.9em;
  color: #666;
}

.tool-btn {
  padding: 8px 12px;
  border: 2px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 1.2em;
  transition: all 0.2s;
}

.tool-btn:hover {
  border-color: #667eea;
}

.tool-btn.active {
  border-color: #667eea;
  background: #667eea;
  color: white;
}

.color-picker {
  width: 40px;
  height: 30px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.width-slider {
  width: 100px;
}

.width-value {
  font-size: 0.9em;
  color: #666;
  min-width: 45px;
}

.clear-btn {
  padding: 8px 15px;
  border: none;
  border-radius: 6px;
  background: #ff6b6b;
  color: white;
  cursor: pointer;
  font-size: 0.9em;
  margin-left: auto;
}

.clear-btn:hover {
  background: #ff4757;
}

.canvas-container {
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.canvas-container canvas {
  display: block;
  max-width: 100%;
  cursor: crosshair;
}

.prompt-templates {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.template-select {
  flex: 1;
  padding: 8px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 0.95em;
  cursor: pointer;
}

.template-select:focus {
  outline: none;
  border-color: #667eea;
}

.prompt-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 0.95em;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}

.prompt-input:focus {
  outline: none;
  border-color: #667eea;
}

.prompt-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #667eea;
  color: white;
  cursor: pointer;
  font-size: 0.9em;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #5568d3;
}

.history-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.history-section h3 {
  margin: 0 0 10px;
  font-size: 1em;
  color: #666;
}

.history-list {
  max-height: 150px;
  overflow-y: auto;
}

.history-item {
  padding: 8px;
  margin-bottom: 5px;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.2s;
}

.history-item:hover {
  background: #e8e8e8;
}

.history-text {
  font-size: 0.9em;
  color: #333;
}

.history-time {
  font-size: 0.8em;
  color: #999;
}

.process-btn {
  width: 100%;
  padding: 15px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.process-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.process-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-info {
  margin-top: 15px;
}

.progress-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.progress-text {
  display: block;
  text-align: center;
  margin-top: 5px;
  font-size: 0.9em;
  color: #666;
}

.time-info {
  margin-top: 15px;
  padding: 10px;
  background: #e8f5e9;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
}

.time-label {
  color: #2e7d32;
}

.time-value {
  font-weight: bold;
  color: #2e7d32;
}

.success-message {
  margin-top: 15px;
  padding: 12px;
  background: #e8f5e9;
  border-radius: 6px;
  color: #2e7d32;
  font-weight: 500;
  text-align: center;
}

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: #ffebee;
  border-radius: 6px;
  color: #c62828;
  text-align: center;
}

.result-image-container {
  text-align: center;
  margin: 15px 0;
}

.result-image {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.result-actions {
  display: flex;
  gap: 10px;
}

.download-btn,
.save-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
}

.download-btn {
  background: #667eea;
  color: white;
}

.download-btn:hover {
  background: #5568d3;
}

.save-btn {
  background: #4caf50;
  color: white;
}

.save-btn:hover {
  background: #45a049;
}
</style>
