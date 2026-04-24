# Hospital OCR Service

医疗记录 OCR 解析服务，基于 PaddleOCR (PP-OCRv5)。

## 功能

- **医疗记录识别**: 解析病历、检查报告等图片
- **结构化数据提取**: 自动提取姓名、年龄、性别、诊断等信息
- **多页处理**: 支持多张图片批量解析
- **GPU 加速**: 自动检测并使用 CUDA（可选）

---

## 项目结构

```
API/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── api/
│   │   └── router_ocr.py    # OCR 路由
│   ├── core/
│   │   └── logger.py        # 日志配置
│   ├── services/
│   │   └── ocr_service.py   # OCR 服务 (PaddleOCR)
│   └── schemas/
│   │   └── __init__.py      # 数据模型
│   └── models/
│   │   └ __init__.py
├── config/
│   ├── settings.py          # 配置管理
│   ├── .env.example         # 环境变量示例
│   └── .env                 # 实际配置 (需创建)
├── logs/                    # 日志输出目录
├── requirements.txt         # pip 依赖
├── environment.yml          # Conda 环境配置
└── README.md
```

---

## 快速启动

### 方式一：Conda 环境 (推荐)

```bash
# 1. 创建 Conda 环境
cd API
conda env create -f environment.yml

# 2. 激活环境
conda activate hospital-ocr

# 3. 配置环境变量
cp config/.env.example config/.env

# 4. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方式二：pip 安装

```bash
cd API

# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 配置说明

编辑 `config/.env` 文件：

```env
# 服务配置
SERVICE_NAME=hospital-ocr
SERVICE_VERSION=1.0.0
DEBUG=true

# 日志
LOG_LEVEL=INFO
LOG_DIR=logs

# OCR 配置
MAX_IMAGE_SIZE_MB=10
```

---

## API 接口

服务启动后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 系统接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |

### OCR 接口

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| POST | `/api/ocr/parse` | 解析医疗记录图片 | `images[]` (base64), `files[]` (上传文件) |

**请求示例 (上传文件):**
```
POST /api/ocr/parse
Content-Type: multipart/form-data

files: [image1.jpg, image2.jpg]
```

**请求示例 (base64):**
```json
POST /api/ocr/parse
Content-Type: application/x-www-form-urlencoded

images=["base64_encoded_string_1", "base64_encoded_string_2"]
```

**返回示例:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "combined_text": "姓名：张三\n年龄：45\n诊断：重症肌无力",
    "structured_data": {
      "patient_name": "张三",
      "patient_age": "45",
      "diagnosis": "重症肌无力"
    },
    "total_pages": 1,
    "success_pages": 1,
    "source": "paddleocr-local-gpu"
  }
}
```

---

## OCR 模型

使用 PaddleOCR PP-OCRv5 模型：
- 支持中英文识别
- GPU 加速（自动检测 CUDA）
- 首次运行会自动下载模型

---

## Docker 部署

```bash
# 构建镜像
docker build -t hospital-ocr .

# 运行容器
docker run -d -p 8000:8000 hospital-ocr
```

---

## 响应格式

所有接口统一返回格式：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | FastAPI 0.109.0 |
| OCR | PaddleOCR 2.7.3 + PaddlePaddle 2.6.0 |
| Python | 3.9 |