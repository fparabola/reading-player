# Server 文档

## 概述

`server` 目录提供了一个基于 FastAPI 的**文本分句服务**（Sentence Splitting Service），支持将连续文本分割成独立的句子。

## 项目结构

```
server/
├── sentence_service.py   # FastAPI 主服务
├── service_manager.py    # 服务管理脚本
├── index.html            # Web 测试界面
├── requirements.txt      # Python 依赖
├── manage.bat            # Windows 管理脚本
├── manage.sh             # Linux/Mac 管理脚本
├── service.log           # 服务日志
└── test_*.py             # 测试文件
```

## 功能特性

### 1. 书籍目录服务 (`/books`)

获取 `resource/` 目录中的所有书籍及其章节信息。

**目录结构要求：**
```
resource/
    书名1/
        章节1.txt
        章节2.txt
    书名2/
        章节1.txt
```

### 2. 分句服务 (`/split`)

支持两种分句算法：

| 算法 | method 参数 | 说明 |
|------|-------------|------|
| 规则算法 | `r` | 基于标点符号和规则的智能分句（默认） |
| NLTK 算法 | `n` | 使用 NLTK 库的 SentTokenizer |

### 3. 章节内容服务 (`/chapter/{book_name}/{chapter_name}`)

获取章节的文本内容，支持从指定位置读取到段落结尾。

### 4. 健康检查 (`/health`)

检查服务是否在线运行。

## 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install fastapi>=0.115.0 uvicorn[standard]>=0.32.0 pydantic>=2.10.0 nltk>=3.8
```

首次运行需要下载 NLTK 数据：

```python
import nltk
nltk.download('punkt_tab')
```

## 运行服务

### 方法 1: 使用服务管理器

**Windows:**
```bash
# 双击 manage.bat 打开菜单
python service_manager.py start   # 启动
python service_manager.py stop    # 停止
python service_manager.py restart # 重启
python service_manager.py status  # 查看状态
```

**Linux/Mac:**
```bash
python service_manager.py start
python service_manager.py stop
python service_manager.py restart
python service_manager.py status
```

### 方法 2: 直接运行服务

```bash
python -m uvicorn sentence_service:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 `http://localhost:8000` 启动。

## API 接口

### 分句接口

**请求:**

```http
POST /split
Content-Type: application/json

{
  "text": "Mr. Smith went to the store. He bought apples!",
  "language": "en",
  "method": "r"
}
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | 是 | 要分句的文本 |
| `language` | string | 否 | 语言代码，目前支持 `en`（默认） |
| `method` | string | 否 | 算法，`r`=规则，`n`=NLTK |

**响应:**

```json
{
  "sentences": [
    "Mr. Smith went to the store.",
    "He bought apples!"
  ],
  "count": 2,
  "method": "rule"
}
```

### 健康检查接口

**请求:**

```http
GET /health
```

**响应:**

```json
{
  "status": "healthy",
  "nltk_available": true
}
```

### 获取所有书籍接口

**请求:**

```http
GET /books
```

**响应:**

```json
{
  "books": [
    {
      "name": "哈利波特1-7英文原版",
      "chapters": [
        {"name": "1.Harry Potter and the Sorcerer's Stone.txt"},
        {"name": "2.CHAPTER ONE.txt"}
      ]
    }
  ]
}
```

### 获取书籍章节接口

**请求:**

```http
GET /chapter/{book_name}
```

**参数:**

| 参数 | 说明 | 示例 |
|------|------|------|
| `book_name` | 书名（文件夹名，URL编码） | `哈利波特1-7英文原版` |

**响应:**

```json
{
  "book_name": "哈利波特1-7英文原版",
  "chapters": [
    {"name": "1.Harry Potter and the Sorcerer's Stone.txt"},
    {"name": "2.CHAPTER ONE.txt"}
  ]
}
```

### 获取章节内容接口

**请求:**

```http
GET /chapter/{book_name}/{chapter_name}?position=0
```

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `book_name` | path | 是 | 书名（文件夹名，URL编码） |
| `chapter_name` | path | 是 | 章节名（txt文件名，URL编码） |
| `position` | query | 否 | 起始位置（字符索引），默认0 |

**响应:**

```json
{
  "book_name": "哈利波特1-7英文原版",
  "chapter_name": "1.Harry Potter and the Sorcerer's Stone.txt",
  "text": "这里是从指定位置开始到段落结尾的文本内容...",
  "start_position": 0,
  "end_position": 250,
  "paragraph_end": false
}
```

## Web 测试界面

访问 `http://localhost:8000` 或直接打开 `index.html` 文件。

界面功能：
- 输入文本进行分句测试
- 选择语言和算法
- 查看分句统计（总句数、句号数、感叹号数、问号数）
- 复制分句结果
- 自动降级到本地 JavaScript 处理（当 API 不可用时）

## 测试

### 快速测试

```bash
python test_service.py
```

### 测试两种算法对比

```bash
python test_both_methods.py
```

### 测试《哈利·波特》片段

```bash
python test_harry_potter.py
```

### 调试测试

```bash
python test_debug.py
```

### 测试章节API接口

```bash
python test_chapter_api.py
```

测试书籍目录和章节内容获取接口。

## 日志

服务运行日志保存在 `service.log` 文件中，可以通过以下命令查看：

```bash
# Windows (需要 PowerShell)
Get-Content service.log -Tail 50

# Linux/Mac
tail -f service.log
```

## 算法说明

### 规则算法 (Rule-based)

基于以下规则的智能分句：
- 识别句结束符：`.` `!` `?`
- 处理缩写（如 Dr., Mr., Jan. 等）
- 跳过省略号 `...`
- 检查新句开始（大写字母、引号、数字）
- 跳过引号内的标点

### NLTK 算法

使用 NLTK 的预训练句子标记器 `SentTokenizer`，适合通用英文文本。

## 配置

默认配置位于 `sentence_service.py`:

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `host` | `0.0.0.0` | 监听地址 |
| `port` | `8000` | 监听端口 |
| `reload` | `True` | 热重载 |

可通过修改 `service_manager.py` 中的 `SERVICE_CONFIG` 变量自定义配置。

## 故障排除

### 问题：NLTK 相关错误

```bash
# 下载所需数据
python -c "import nltk; nltk.download('punkt_tab')"
```

### 问题：端口 8000 被占用

修改 `service_manager.py` 中的端口号或手动指定端口：

```bash
python -m uvicorn sentence_service:app --port 8080
```

### 问题：服务启动失败

检查 `service.log` 文件获取详细错误信息。

## 版本

- Python: 3.8+
- FastAPI: >=0.115.0
- NLTK: >=3.8
