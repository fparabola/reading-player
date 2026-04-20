# Reading Player

Reading Player 是一个基于 Web 的文本播放器，支持文本分句、TTS 朗读、进度控制等功能，适用于语言学习、有声阅读等场景。

## 功能特性

- 📚 支持多书籍管理和章节选择
- 🔊 内置多种 TTS 引擎（Pocket TTS、Edge TTS）
- ⏱️ 可调节语速和自动播放设置
- 🎯 精准的句子级进度控制
- 📝 句子解析功能，支持查看句子结构和语法
- 🌙 深色主题，护眼阅读
- 📱 响应式设计，支持不同设备

## 技术栈

### 前端
- Vue 3 + Vite
- JavaScript
- CSS3

### 后端
- Python 3
- FastAPI
- NLTK（自然语言处理）
- Pocket TTS（文本转语音）
- Edge TTS（文本转语音）

## 目录结构

```
txt_player/
├── player-vue/         # 前端项目
│   ├── public/          # 静态资源
│   ├── src/             # 源代码
│   │   ├── App.vue      # 主应用组件
│   │   ├── main.js      # 入口文件
│   │   └── styles.css   # 样式文件
│   ├── package.json     # 项目配置
│   └── vue.config.js    # Vue 配置
├── server/              # 后端项目
│   ├── src/             # 源代码
│   │   ├── tts/         # TTS 音频文件
│   │   ├── config_helper.py  # 配置辅助
│   │   ├── llm_service.py    # LLM 服务
│   │   ├── prompt_helper.py  # 提示辅助
│   │   ├── sentence_service.py  # 句子服务
│   │   └── service_manager.py  # 服务管理
│   ├── README.md        # 后端说明
│   ├── index.html       # 后端页面
│   ├── manage.bat       # Windows 管理脚本
│   ├── manage.sh        # Linux/Mac 管理脚本
│   ├── pocket_tts.html  # Pocket TTS 页面
│   └── requirements.txt # 依赖项
└── .gitignore           # Git 忽略文件
```

## 安装与部署

### 前端

1. 进入前端目录
   ```bash
   cd player-vue
   ```

2. 安装依赖
   ```bash
   npm install
   ```

3. 开发模式运行
   ```bash
   npm run serve
   ```

4. 构建生产版本
   ```bash
   npm run build
   ```

### 后端

1. 进入后端目录
   ```bash
   cd server
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 启动服务
   - Windows:
     ```bash
     .\manage.bat start
     ```
   - Linux/Mac:
     ```bash
     ./manage.sh start
     ```

4. 停止服务
   - Windows:
     ```bash
     .\manage.bat stop
     ```
   - Linux/Mac:
     ```bash
     ./manage.sh stop
     ```

## 使用方法

1. 启动前端和后端服务
2. 打开前端页面（默认：http://localhost:8080）
3. 选择书籍和章节
4. 点击播放按钮开始朗读
5. 使用进度条控制阅读进度
6. 调整语速和其他设置

## 核心功能

### 句子分割
- **规则算法**：基于标点符号和换行符的规则分割
- **NLTK算法**：基于自然语言处理的智能分割

### TTS 朗读
- **Pocket TTS**：默认 TTS 引擎，音质清晰
- **Edge TTS**：微软 Edge 语音服务，支持多种语言和声音

### 句子解析
- 点击句子可查看详细解析
- 支持语法分析和结构展示

## 配置说明

### 前端配置
- `API_CANDIDATES`：API 服务地址列表，用于自动检测后端服务
- `DEFAULT_BOOK`：默认书籍

### 后端配置
- 服务端口：默认为 8000
- TTS 缓存：位于 `src/tts/` 目录

## 开发指南

### 前端开发
- 主要组件：`App.vue`
- 核心功能：文本加载、句子分割、TTS 调用、进度控制

### 后端开发
- 核心服务：`sentence_service.py`（句子分割）、TTS 服务
- API 接口：`/split`（句子分割）、`/tts`（文本转语音）、`/analyze_stream`（句子解析）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
