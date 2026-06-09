<template>
  <div class="image-processor">
    <div class="processor-header">
      <h1>图片处理工具</h1>
      <p class="subtitle">上传图片、添加标注、调用AI模型进行处理</p>
    </div>

    <div class="processor-content">
      <section class="upload-section">
        <h2>📤 图片上传</h2>
        <div class="sample-section">
          <h3>📷 示例图片</h3>
          <div class="sample-images">
            <div class="sample-item">
              <img src="/samples/2/1.png" alt="示例" @click="loadSampleImage('/samples/2/1.png')" />
              <span>示例 - 输入</span>
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

        <div v-if="uploadedFile" class="process-section">
          <h3>🎯 选择处理模式</h3>
          <div class="process-type-selector">
            <button
              class="type-btn"
              :class="{ active: processType === 'overlay' }"
              @click="processType = 'overlay'"
            >
              叠加显示
            </button>
            <button
              class="type-btn"
              :class="{ active: processType === 'mask' }"
              @click="processType = 'mask'"
            >
              分割掩码
            </button>
          </div>
          <button
            class="process-btn"
            @click="processImage"
            :disabled="isProcessing"
          >
            {{ isProcessing ? '处理中...' : '开始处理' }}
          </button>
        </div>

        <div v-if="isProcessing" class="loading-spinner">
          <div class="spinner"></div>
          <p>正在调用AI模型进行图像分割...</p>
        </div>

        <section v-if="resultImage" class="canvas-section">
          <h2>✏️ 标注补充</h2>
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
            <button class="clear-btn" @click="clearCanvas">🗑️ 清空</button>
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

        <div v-if="resultImage" class="result-section">
          <h3>✨ 处理结果</h3>
          <div class="result-preview">
            <img :src="resultImage" alt="处理结果" />
          </div>
          <div class="result-actions">
            <button class="download-btn" @click="downloadResult">
              📥 下载分割结果
            </button>
            <button
              class="remove-object-btn"
              @click="removeObject"
              :disabled="isRemovingObject"
            >
              {{ isRemovingObject ? '移除中...' : '🧹 目标移除' }}
            </button>
          </div>
        </div>

        <div v-if="isRemovingObject" class="loading-spinner">
          <div class="spinner"></div>
          <p>正在调用大模型进行目标移除...</p>
          <div class="progress-info">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: removeObjectProgress + '%' }"></div>
            </div>
            <span class="progress-text">处理中... {{ removeObjectProgress }}%</span>
          </div>
        </div>

        <div v-if="removeObjectTime" class="time-info">
          <span class="time-label">⏱️ 处理耗时：</span>
          <span class="time-value">{{ removeObjectTime }} 秒</span>
        </div>

        <div v-if="removeObjectSuccess" class="success-message">
          {{ removeObjectSuccess }}
        </div>

        <div v-if="removeObjectResult" class="remove-result-section">
          <h3>🎉 目标移除结果</h3>
          <div class="result-preview">
            <img :src="removeObjectResult" alt="目标移除结果" />
          </div>
          <button class="download-btn" @click="downloadRemoveResult">
            📥 下载结果
          </button>
        </div>

        <div v-if="removeObjectError" class="error-message">{{ removeObjectError }}</div>

        <div v-if="processError" class="error-message">{{ processError }}</div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'

const fileInput = ref(null)
const canvasContainer = ref(null)
const drawingCanvas = ref(null)

const uploadedImage = ref(null)
const uploadedFile = ref(null)
const isDragOver = ref(false)
const uploadError = ref('')
const processType = ref('overlay')
const isProcessing = ref(false)
const resultImage = ref(null)
const processError = ref('')
const resultData = ref(null)

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

const isRemovingObject = ref(false)
const removeObjectProgress = ref(0)
const removeObjectError = ref('')
const removeObjectResult = ref(null)
const removeObjectTime = ref(null)
const removeObjectSuccess = ref('')

const API_BASE_URL = 'http://127.0.0.1:5000'
const RUNNINGHUB_API_URL = ''
const RUNNINGHUB_QUERY_URL = ''
const RUNNINGHUB_UPLOAD_URL = ''
const API_KEY = ''

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
  processError.value = ''
  resultImage.value = null
  resultData.value = null

  const error = validateFile(file)
  if (error) {
    uploadError.value = error
    return
  }

  uploadedFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.readAsDataURL(file)
}

function removeImage() {
  uploadedImage.value = null
  uploadedFile.value = null
  resultImage.value = null
  resultData.value = null
  processError.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  clearCanvas()
  drawingContext.value = null
  originalImageData.value = null
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

async function processImage() {
  if (!uploadedFile.value) {
    processError.value = '请先上传图片'
    return
  }

  isProcessing.value = true
  processError.value = ''

  try {
    const formData = new FormData()
    formData.append('image', uploadedFile.value)
    formData.append('type', processType.value)

    const response = await fetch(`${API_BASE_URL}/segment`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || '处理失败')
    }

    const blob = await response.blob()
    resultData.value = blob
    resultImage.value = URL.createObjectURL(blob)
    nextTick(() => {
      setupCanvas()
    })
  } catch (error) {
    processError.value = `处理失败: ${error.message}`
    console.error('Process error:', error)
  } finally {
    isProcessing.value = false
  }
}

function downloadResult() {
  if (!resultData.value || !uploadedFile.value) return

  const link = document.createElement('a')
  const originalName = uploadedFile.value.name
  const baseName = originalName.substring(0, originalName.lastIndexOf('.'))
  link.download = `${baseName}_${processType.value}.png`
  link.href = resultImage.value
  link.click()
}

function setupCanvas() {
  if (!drawingCanvas.value || !resultImage.value) return

  const canvas = drawingCanvas.value
  const container = canvasContainer.value
  const ctx = canvas.getContext('2d')

  const img = new Image()
  img.onload = () => {
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

    drawingContext.value = ctx
    ctx.drawImage(img, 0, 0, width, height)
    originalImageData.value = ctx.getImageData(0, 0, width, height)

    tempCanvas.value = document.createElement('canvas')
    tempCanvas.value.width = width
    tempCanvas.value.height = height
  }
  img.src = resultImage.value
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

async function removeObject() {
  if (!resultImage.value || isRemovingObject.value) return

  isRemovingObject.value = true
  removeObjectProgress.value = 0
  removeObjectError.value = ''
  removeObjectSuccess.value = ''

  const startTime = performance.now()

  try {
    removeObjectProgress.value = 10

    const canvas = drawingCanvas.value
    const ctx = canvas.getContext('2d')

    const resultCanvas = document.createElement('canvas')
    resultCanvas.width = canvas.width
    resultCanvas.height = canvas.height
    const resultCtx = resultCanvas.getContext('2d')

    resultCtx.putImageData(originalImageData.value, 0, 0)

    const currentImageData = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height)
    const currentData = currentImageData.data
    const originalData = originalImageData.value.data
    const resultData = resultCtx.getImageData(0, 0, canvas.width, canvas.height)
    const rData = resultData.data

    for (let i = 0; i < currentData.length; i += 4) {
      const rCurrent = currentData[i]
      const gCurrent = currentData[i + 1]
      const bCurrent = currentData[i + 2]

      const rOriginal = originalData[i]
      const gOriginal = originalData[i + 1]
      const bOriginal = originalData[i + 2]

      const diff = Math.abs(rCurrent - rOriginal) + Math.abs(gCurrent - gOriginal) + Math.abs(bCurrent - bOriginal)

      if (diff > 30) {
        rData[i + 3] = 0
      }
    }

    resultCtx.putImageData(resultData, 0, 0)
    const annotatedImageData = resultCanvas.toDataURL('image/png')

    removeObjectProgress.value = 20

    const uploadFormData = new FormData()
    const blob = await fetch(annotatedImageData).then(r => r.blob())
    uploadFormData.append('file', blob, 'annotated.png')

    const uploadResponse = await axios.post(RUNNINGHUB_UPLOAD_URL, uploadFormData, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded / progressEvent.total) * 30)
          removeObjectProgress.value = 10 + percentCompleted
        }
      }
    })

    if (!uploadResponse.data || uploadResponse.data.code !== 0) {
      throw new Error('图片上传失败: ' + (uploadResponse.data?.message || '未知错误'))
    }

    const imageUrl = uploadResponse.data.data.download_url
    removeObjectProgress.value = 40

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
          fieldValue: "移除标记部分",
          description: "text"
        }
      ],
      instanceType: "plus",
      usePersonalQueue: "false"
    }

    removeObjectProgress.value = 50

    const taskResponse = await axios.post(RUNNINGHUB_API_URL, payload, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      }
    })

    if (!taskResponse.data || !taskResponse.data.taskId) {
      throw new Error('任务提交失败: ' + (taskResponse.data?.errorMessage || '未知错误'))
    }

    const taskId = taskResponse.data.taskId
    removeObjectProgress.value = 60

    let taskStatus = 'QUEUED'
    let taskResult = null
    let retryCount = 0
    const maxRetries = 30

    while (retryCount < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, 3000))

      const queryResponse = await axios.post(RUNNINGHUB_QUERY_URL, { taskId }, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`
        }
      })

      if (!queryResponse.data) {
        throw new Error('查询任务状态失败')
      }

      taskStatus = queryResponse.data.status
      taskResult = queryResponse.data

      if (taskStatus === 'SUCCESS') {
        removeObjectProgress.value = 90
        break
      } else if (taskStatus === 'FAILED') {
        throw new Error('任务执行失败: ' + (taskResult.errorMessage || '未知错误'))
      } else if (taskStatus === 'RUNNING') {
        removeObjectProgress.value = Math.min(60 + (retryCount * 2), 80)
      }

      retryCount++
    }

    if (retryCount >= maxRetries) {
      throw new Error('任务执行超时，请稍后重试')
    }

    if (taskResult.results && taskResult.results.length > 0) {
      removeObjectResult.value = taskResult.results[0].url
      removeObjectSuccess.value = '✨ 目标移除成功！'
    } else {
      throw new Error('任务成功但未返回结果')
    }

    const endTime = performance.now()
    removeObjectTime.value = ((endTime - startTime) / 1000).toFixed(2)

    removeObjectProgress.value = 100

  } catch (error) {
    const endTime = performance.now()
    removeObjectTime.value = ((endTime - startTime) / 1000).toFixed(2)

    if (error.code === 'ECONNABORTED') {
      removeObjectError.value = '请求超时，请检查网络连接后重试'
    } else {
      removeObjectError.value = `处理失败: ${error.message}`
    }
  } finally {
    isRemovingObject.value = false
  }
}

function downloadRemoveResult() {
  if (!removeObjectResult.value) return

  const link = document.createElement('a')
  link.href = removeObjectResult.value
  link.download = `removed_object_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.image-processor {
  max-width: 800px;
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
  justify-content: center;
}

.upload-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
}

.upload-section h2 {
  margin: 0 0 15px;
  font-size: 1.3em;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
}

.canvas-section {
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.canvas-section h2 {
  margin: 0 0 15px;
  font-size: 1.3em;
  color: #333;
  border-bottom: 2px solid #ff6b6b;
  padding-bottom: 10px;
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
  border-color: #ff6b6b;
}

.tool-btn.active {
  border-color: #ff6b6b;
  background: #ff6b6b;
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

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: #ffebee;
  border-radius: 6px;
  color: #c62828;
  text-align: center;
}

.process-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9ff;
  border-radius: 8px;
  border: 1px solid #e8eaff;
}

.process-section h3 {
  margin: 0 0 15px;
  font-size: 1.1em;
  color: #333;
}

.process-type-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.type-btn {
  flex: 1;
  padding: 10px 15px;
  border: 2px solid #667eea;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95em;
  color: #667eea;
  transition: all 0.3s ease;
}

.type-btn:hover {
  background: #f0f2ff;
}

.type-btn.active {
  background: #667eea;
  color: white;
}

.process-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.process-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.process-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  margin-top: 20px;
  padding: 30px;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  margin: 0 auto 15px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-spinner p {
  margin: 0;
  color: #666;
  font-size: 0.95em;
}

.result-section {
  margin-top: 20px;
  padding: 20px;
  background: #f0fff0;
  border-radius: 8px;
  border: 1px solid #c8e6c9;
}

.result-section h3 {
  margin: 0 0 15px;
  font-size: 1.1em;
  color: #2e7d32;
}

.result-preview {
  margin-bottom: 15px;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  padding: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-preview img {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  display: block;
}

.result-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.download-btn {
  flex: 1;
  padding: 12px;
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}

.remove-object-btn {
  flex: 1;
  padding: 12px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s ease;
}

.remove-object-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
}

.remove-object-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  background: linear-gradient(90deg, #ff6b6b 0%, #ee5a24 100%);
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

.remove-result-section {
  margin-top: 20px;
  padding: 20px;
  background: #fff3e0;
  border-radius: 8px;
  border: 1px solid #ffe0b2;
}

.remove-result-section h3 {
  margin: 0 0 15px;
  font-size: 1.1em;
  color: #e65100;
}
</style>
