# Fabricate

图像处理与生成系统，基于 Vue 3 + Flask 构建的 Web 应用。

## 功能特性

- **UNet 图像分割**：基于 UNet 模型的图像分割处理
- **GAN 图像生成**：生成对抗网络图像生成功能
- **图像后处理**：支持图像掩码、叠加、配色等处理

## 技术栈

### 前端
- Vue 3
- Vite
- Element Plus

### 后端
- Python Flask
- PyTorch (UNet, GAN)
- OpenCV

## 快速开始

### 前端

```bash
npm install
npm run dev
```

### 后端

```bash
cd Backend
pip install -r requirements.txt
python api.py
```

## 项目结构

```
├── src/                 # 前端源代码
│   ├── components/      # Vue 组件
│   └── assets/          # 静态资源
├── Backend/             # 后端代码
│   ├── Unet.py         # UNet 模型
│   ├── api.py          # Flask API
│   └── inference.py    # 推理脚本
└── public/             # 公共资源
```
