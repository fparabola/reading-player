"""
分句服务
提供文本分句接口，目前支持英文
支持两种算法：规则算法(r)和nltk(n)

新增功能：
- 书籍目录接口：获取资源目录中的书籍和章节
- 章节内容接口：获取章节的片段内容
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import os
import configparser
from pathlib import Path
from typing import List, Optional
import uvicorn
import edge_tts
import json
import requests
import traceback

app = FastAPI(title="Sentence Splitter API", version="2.0.0")

# 添加 CORS 中间件，允许本地文件访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（本地文件）
    allow_credentials=False,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 资源目录常量
RESOURCE_DIR = Path(__file__).parent / "resource"
LOG_PATH = Path(__file__).parent / "service.log"
CONFIG_PATH = Path(__file__).parent / "config.ini"
_CONFIG_CACHE: Optional[configparser.ConfigParser] = None

def log_line(message: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[analyze] {message}\n")
    except Exception:
        pass

def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"

def load_local_config() -> configparser.ConfigParser:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    parser = configparser.ConfigParser()
    if not CONFIG_PATH.exists():
        _CONFIG_CACHE = parser
        return _CONFIG_CACHE

    try:
        parser.read(CONFIG_PATH, encoding="utf-8")
        _CONFIG_CACHE = parser
    except Exception as e:
        log_line(f"load config failed: {str(e)}")
        _CONFIG_CACHE = configparser.ConfigParser()
    return _CONFIG_CACHE

def get_siliconflow_api_key() -> str:
    env_key = (os.getenv("SILICONFLOW_API_KEY") or "").strip()
    if env_key:
        return env_key

    config = load_local_config()
    return (config.get("auth", "siliconflow_api_key", fallback="") or "").strip()

@app.on_event("startup")
async def log_api_key():
    env_key = (os.getenv("SILICONFLOW_API_KEY") or "").strip()
    api_key = get_siliconflow_api_key()
    source = "env" if env_key else ("config" if api_key else "missing")
    log_line(f"SILICONFLOW_API_KEY({source})={mask_key(api_key)}")

async def synthesize_tts(text: str, voice: str, rate: str) -> bytes:
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    audio_bytes = bytearray()
    async for chunk in communicator.stream():
        if chunk.get("type") == "audio":
            audio_bytes.extend(chunk.get("data", b""))
    return bytes(audio_bytes)

def chapter_sort_key(name: str) -> tuple:
    match = re.search(r"\d+", name)
    if match:
        return (0, int(match.group()), name.lower())
    return (1, name.lower())


def get_resource_books() -> List[BookInfo]:
    """
    获取资源目录中的所有书籍和章节

    目录结构：
    resource/
        书名1/
            章节1.txt
            章节2.txt
        书名2/
            章节1.txt
    """
    books = []

    if not RESOURCE_DIR.exists():
        return books

    for book_path in sorted(RESOURCE_DIR.iterdir()):
        if not book_path.is_dir():
            continue

        chapters = []
        chapter_files = [
            chapter_file
            for chapter_file in book_path.iterdir()
            if chapter_file.is_file() and chapter_file.suffix.lower() == '.txt'
        ]
        for chapter_file in sorted(chapter_files, key=lambda p: chapter_sort_key(p.name)):
            chapters.append(ChapterInfo(name=chapter_file.name))

        if chapters:  # 只添加有章节的书籍
            books.append(BookInfo(name=book_path.name, chapters=chapters))

    return books


def get_chapter_path(book_name: str, chapter_name: str) -> Path:
    """获取章节文件的路径"""
    return RESOURCE_DIR / book_name / chapter_name


def get_chapter_text(book_name: str, chapter_name: str) -> str:
    """读取章节文本内容"""
    chapter_path = get_chapter_path(book_name, chapter_name)

    if not chapter_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Chapter not found: {book_name}/{chapter_name}"
        )

    try:
        with open(chapter_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        for encoding in ['gbk', 'gb18030', 'latin-1']:
            try:
                with open(chapter_path, 'r', encoding=encoding) as f:
                    return f.read()
            except:
                continue
        raise HTTPException(
            status_code=500,
            detail=f"Could not decode chapter file: {chapter_name}"
        )


class SentenceRequest(BaseModel):
    text: str
    language: str
    method: Optional[str] = "r"  # r=规则算法, n=nltk, 默认规则算法


class SentenceResponse(BaseModel):
    sentences: List[str]
    count: int
    method: str  # 返回实际使用的算法


class ChapterInfo(BaseModel):
    name: str  # 章节名称（文件名）


class BookInfo(BaseModel):
    name: str  # 书名（文件夹名）
    chapters: List[ChapterInfo]  # 章节列表


class BooksResponse(BaseModel):
    books: List[BookInfo]


class ChapterContentResponse(BaseModel):
    book_name: str
    chapter_name: str
    text: str
    start_position: int
    end_position: int


class AnalyzeRequest(BaseModel):
    text: str
    model: Optional[str] = None


class AnalyzeResponse(BaseModel):
    meaning: str
    vocabulary: str
    grammar: str


def build_analyze_prompt(text: str) -> str:
    return (
        "你是一名资深的英文导读老师，现在正在帮我进行英语精读训练。我是英语学习者。\n"
        "请用 **Markdown** 输出，严格按下面结构回答：\n\n"
        "## 1. 自然中文翻译\n"
        "- 给出自然中文翻译（不要逐词直译）\n\n"
        "## 2. 作者意图\n"
        "- 作者这样写有什么特殊含义（如果句子有特殊意味）\n\n"
        "## 3. 重点词汇\n"
        "- 词性 + 核心含义 + 语境含义\n\n"
        "## 4. 重点短语/固定搭配\n"
        "- 列出并解释\n\n"
        "## 5. 语法重点\n"
        "- 总结本段语法重点\n\n"
        "讲解要清晰，适合中级英语学习者。\n\n"
        "以下是文本：\n"
        f"{text}"
    )


class BookListResponse(BaseModel):
    books: List[str]  # 书名列表


# 英文缩写列表，避免在这些词汇后错误分句
ENGLISH_ABBREVIATIONS = {
    'mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'gen', 'rep', 'sen', 'gov',
    'capt', 'col', 'maj', 'lt', 'sgt', 'pvt', 'st', 'ave', 'blvd', 'rd',
    'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
    'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
    'etc', 'eg', 'ie', 'vs', 'approx', 'no', 'tel', 'fax',
    'vol', 'chap', 'p', 'pp', 'et', 'al', 'ps', 'pps'
}

# nltk模块是否可用
NLTK_AVAILABLE = False
try:
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
    # 下载nltk数据（如果未下载）
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
        except:
            pass
except ImportError:
    pass


def split_sentences_rule(text: str) -> List[str]:
    """
    规则算法分句
    使用基于规则的算法处理缩写和边界情况
    """
    if not text or not text.strip():
        return []

    # 保留换行符，只去除多余空格
    text = re.sub(r'\s+', ' ', text.strip())

    sentences = []
    start = 0
    i = 0
    n = len(text)

    while i < n:
        # 跳过引号后的内容，引号内的标点不应该分句
        if text[i] == '"':
            i = text.find('"', i + 1)
            if i == -1:
                i = n - 1
            i += 1
            continue

        # 查找句子的结束标记
        if text[i] not in '.!?':
            i += 1
            continue

        end_pos = i

        # 检查是否是真句子结束

        # 1. 检查后面是否还有字母
        j = i + 1
        while j < n and text[j].isalpha():
            j += 1
        if j > i + 1:
            i = j - 1
            i += 1
            continue

        # 2. 检查是否是省略号 "..."
        if i + 2 < n and text[i+1] == '.' and text[i+2] == '.':
            i += 3
            continue

        # 3. 检查点号前是否是已知缩写
        word_start = i - 1
        while word_start >= start and not text[word_start].isspace():
            word_start -= 1
        word_start += 1

        word = text[word_start:i].lower()

        if word in ENGLISH_ABBREVIATIONS:
            i += 1
            continue

        # 检查是否是单个大写字母+点
        if re.match(r'^[a-zA-Z]$', text[word_start:i]):
            i += 1
            continue

        # 4. 检查后面是否是大写字母（新句子开始）
        j = i + 1
        while j < n and text[j].isspace():
            j += 1

        if j < n:
            next_char = text[j]
            if not next_char.isupper() and next_char != '"' and not next_char.isdigit():
                i += 1
                continue

        i += 1
        sentence = text[start:i].strip()
        if sentence:
            sentences.append(sentence)

        start = i
        while start < n and text[start].isspace():
            start += 1
        i = start

    if start < n:
        sentence = text[start:].strip()
        if sentence:
            sentences.append(sentence)

    return sentences


def split_sentences_nltk(text: str) -> List[str]:
    """
    使用nltk分句
    """
    if not NLTK_AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="nltk is not available. Please install nltk: pip install nltk"
        )

    if not text or not text.strip():
        return []

    # 使用nltk的sent_tokenize
    sentences = sent_tokenize(text)
    return sentences


def split_sentences(text: str, language: str, method: str = "r") -> tuple[List[str], str]:
    """
    根据语言和方法分句

    参数:
    - text: 输入文本
    - language: 语言代码
    - method: 算法方法 ('r'=规则, 'n'=nltk)

    返回:
    - (sentences_list, actual_method_used)
    """
    language = language.lower()
    method = method.lower()

    if language not in ['en', 'english', 'eng']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {language}. Currently only English is supported."
        )

    # 选择算法
    if method == 'n' or method == 'nltk':
        if NLTK_AVAILABLE:
            return split_sentences_nltk(text), 'nltk'
        else:
            # nltk不可用，降级到规则算法
            return split_sentences_rule(text), 'rule (nltk unavailable)'
    else:
        # 默认使用规则算法
        return split_sentences_rule(text), 'rule'


@app.get("/")
async def root():
    """API根路径"""
    return {
        "service": "Sentence Splitter API",
        "version": "2.0.0",
        "nltk_available": NLTK_AVAILABLE,
        "methods": {
            "rule": "Rule-based algorithm (default)",
            "nltk": "NLTK tokenizer (install nltk first)"
        },
        "endpoints": {
            "/split": "POST - Split text into sentences",
            "/books": "GET - Get all books and chapters",
            "/chapter/{book_name}": "GET - Get chapters of a specific book",
            "/chapter/{book_name}/{chapter_name}": "GET - Get chapter content with position",
            "/health": "GET - Health check"
        }
    }


@app.post("/split", response_model=SentenceResponse)
async def split_text(request: SentenceRequest):
    """
    分句接口

    参数:
    - text: 要分割的文本
    - language: 语言代码 (目前只支持 'en' 或 'english')
    - method: 算法方法 (可选)
        - 'r' 或 'rule' 或不填: 使用规则算法 (默认)
        - 'n' 或 'nltk': 使用nltk分句

    返回:
    - sentences: 句子列表
    - count: 句子数量
    - method: 实际使用的算法
    """
    try:
        sentences, actual_method = split_sentences(request.text, request.language, request.method)
        return SentenceResponse(sentences=sentences, count=len(sentences), method=actual_method)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "nltk_available": NLTK_AVAILABLE
    }


@app.get("/books", response_model=BooksResponse)
async def get_books():
    """
    获取书籍目录接口（包含章节信息）

    返回所有书籍及其章节信息

    目录结构：
        resource/
            书名1/
                章节1.txt
                章节2.txt
    """
    try:
        books = get_resource_books()
        return BooksResponse(books=books)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading books: {str(e)}")


@app.get("/books/list", response_model=BookListResponse)
async def get_book_list():
    """
    获取书名列表接口（仅返回书名）

    返回 resource 目录下的所有书名

    目录结构：
        resource/
            书名1/
                章节1.txt
            书名2/
                章节1.txt
    """
    try:
        books = get_resource_books()
        book_names = [book.name for book in books]
        return BookListResponse(books=book_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading book list: {str(e)}")


@app.get("/books/{book_name}")
async def get_book_info(book_name: str):
    """
    获取指定书籍信息（章节列表）

    与 /chapter/{book_name} 功能相同
    """
    try:
        from urllib.parse import unquote
        book_name = unquote(book_name)

        book_path = RESOURCE_DIR / book_name
        if not book_path.exists() or not book_path.is_dir():
            raise HTTPException(status_code=404, detail=f"Book not found: {book_name}")

        chapters = []
        chapter_files = [
            chapter_file
            for chapter_file in book_path.iterdir()
            if chapter_file.is_file() and chapter_file.suffix.lower() == '.txt'
        ]
        for chapter_file in sorted(chapter_files, key=lambda p: chapter_sort_key(p.name)):
            chapters.append({"name": chapter_file.name})

        return {
            "book_name": book_name,
            "chapters": chapters
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading book info: {str(e)}")


@app.get("/chapter/{book_name}")
async def get_chapters(book_name: str):
    """
    获取指定书籍的所有章节

    参数:
        book_name: 书名（文件夹名）

    返回:
        该书的章节列表
    """
    try:
        book_path = RESOURCE_DIR / book_name
        if not book_path.exists() or not book_path.is_dir():
            raise HTTPException(status_code=404, detail=f"Book not found: {book_name}")

        chapters = []
        chapter_files = [
            chapter_file
            for chapter_file in book_path.iterdir()
            if chapter_file.is_file() and chapter_file.suffix.lower() == '.txt'
        ]
        for chapter_file in sorted(chapter_files, key=lambda p: chapter_sort_key(p.name)):
            chapters.append({"name": chapter_file.name})

        return {
            "book_name": book_name,
            "chapters": chapters
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading chapters: {str(e)}")


@app.get("/chapter/{book_name}/{chapter_name}")
async def get_chapter_content(
    book_name: str,
    chapter_name: str,
    position: int = Query(0, ge=0, description="起始位置（字符索引），从0开始"),
    min_size: int = Query(100, ge=0, description="最小内容长度（字符数），默认100")
):
    """
    获取章节内容接口

    参数:
        book_name: 书名（文件夹名）
        chapter_name: 章节名（txt文件名）
        position: 起始位置（字符索引），从0开始
        min_size: 最小内容长度（字符数），默认100

    返回:
        从起始位置开始，内容长度至少为 min_size 并且读取到段落结尾的文本片段
    """
    try:
        # URL解码（处理中文和特殊字符）
        from urllib.parse import unquote
        book_name = unquote(book_name)
        chapter_name = unquote(chapter_name)

        # 读取章节内容
        text = get_chapter_text(book_name, chapter_name)

        # 检查位置是否超出范围
        if position >= len(text):
            return ChapterContentResponse(
                book_name=book_name,
                chapter_name=chapter_name,
                text="",
                start_position=position,
                end_position=len(text),
                paragraph_end=True
            )

        start_pos = position
        end_pos = position
        text_length = len(text)

        # 不断读取段落，直到满足最小长度或到达文件结尾
        while end_pos < text_length:
            remaining = text[end_pos:]

            # 查找段落分隔符（双换行符）
            paragraph_sep = remaining.find('\n\n')

            if paragraph_sep != -1:
                # 找到段落分隔符，包含分隔符
                next_end = end_pos + paragraph_sep + 2
            else:
                # 没有双换行符，查找单换行符或直接到结尾
                line_sep = remaining.find('\n')
                if line_sep != -1:
                    next_end = end_pos + line_sep + 1
                else:
                    next_end = text_length

            # 检查当前片段满足条件
            current_size = next_end - start_pos

            if current_size >= min_size and (next_end >= text_length or '\n\n' in text[end_pos:next_end]):
                # 满足最小长度且到达段落结尾，返回
                end_pos = next_end
                break

            # 如果已经是文件结尾，直接返回
            if next_end >= text_length:
                end_pos = text_length
                break

            # 继续读取下一段落
            end_pos = next_end

            # 安全限制：最多读取 50000 字符
            if end_pos - start_pos > 50000:
                break

        content = text[start_pos:end_pos]

        return ChapterContentResponse(
            book_name=book_name,
            chapter_name=chapter_name,
            text=content,
            start_position=start_pos,
            end_position=end_pos,
            paragraph_end=(end_pos >= text_length or
                           (end_pos >= 2 and text[end_pos-2:end_pos] == '\n\n') or
                           (end_pos >= 1 and text[end_pos-1:end_pos] == '\n'))
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading chapter: {str(e)}")


@app.get("/tts")
async def tts(
    text: str = Query(..., min_length=1, description="要朗读的文本"),
    voice: str = Query("zh-CN-XiaoxiaoNeural", description="语音"),
    rate: str = Query("+0%", description="语速，例如 +0%, -10%")
):
    try:
        audio = await synthesize_tts(text, voice, rate)
        if not audio:
            raise HTTPException(status_code=500, detail="TTS returned empty audio")
        return Response(content=audio, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    api_key = get_siliconflow_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing SILICONFLOW_API_KEY (env or config.ini)")

    prompt = build_analyze_prompt(request.text)

    model_name = request.model or "Qwen/Qwen3-14B"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是英语句子解析助手，中文回答。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        log_line("request start")
        resp = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        if resp.status_code != 200:
            log_line(f"LLM status={resp.status_code} body={resp.text}")
            raise HTTPException(status_code=500, detail="LLM error")
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        log_line(f"LLM response: {content}")
    except HTTPException:
        raise
    except Exception as e:
        log_line(f"LLM exception: {str(e)}")
        log_line(traceback.format_exc())
        raise HTTPException(status_code=500, detail="LLM error")

    return AnalyzeResponse(
        meaning=content,
        vocabulary="",
        grammar=""
    )


@app.post("/analyze_stream")
async def analyze_text_stream(request: AnalyzeRequest):
    api_key = get_siliconflow_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing SILICONFLOW_API_KEY (env or config.ini)")

    prompt = build_analyze_prompt(request.text)

    model_name = request.model or "Qwen/Qwen3-14B"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是英语句子解析助手，中文回答。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    def stream_generator():
        full_text = []
        try:
            log_line("stream request start")
            resp = requests.post(
                "https://api.siliconflow.cn/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                stream=True,
                timeout=60
            )
            if resp.status_code != 200:
                log_line(f"LLM status={resp.status_code} body={resp.text}")
                yield ""
                return
            resp.encoding = "utf-8"

            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                    if not delta:
                        continue
                    full_text.append(delta)
                    yield delta
                except Exception:
                    continue
        except Exception as e:
            log_line(f"LLM stream exception: {str(e)}")
            log_line(traceback.format_exc())
        finally:
            if full_text:
                log_line(f"LLM response: {''.join(full_text)}")

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
