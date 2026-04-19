"""
分句服务
提供文本分句接口，目前支持英文
支持两种算法：规则算法(r)和nltk(n)

新增功能：
- 书籍目录接口：获取资源目录中的书籍和章节
- 章节内容接口：获取章节的片段内容
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
import re
import os
import configparser
import hashlib
from pathlib import Path
import threading
from typing import List, Optional
import uvicorn
import edge_tts
import json
import numpy as np
import requests
import traceback
import httpx
import sys
import wave

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_service import analyze_text_stream
from config_helper import config_helper

app = FastAPI(title="Sentence Splitter API", version="2.0.0")

# 添加 CORS 中间件，允许本地文件访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（本地文件）
    allow_credentials=False,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 资源目录
RESOURCE_DIR = Path(__file__).parent.parent / "resource"
LOG_PATH = Path(__file__).parent / "service.log"
CONFIG_PATH = Path(__file__).parent.parent / "config.ini"
TTS_CACHE_DIR = Path(__file__).parent / "tts"
_CONFIG_CACHE: Optional[configparser.ConfigParser] = None
_POCKET_TTS_MODEL = None
_POCKET_TTS_MODEL_LOCK = threading.Lock()
_POCKET_TTS_VOICE_STATES = {}
_POCKET_TTS_VOICE_LOCK = threading.Lock()

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

    return config_helper.get("auth.siliconflow_api_key").strip()

@app.on_event("startup")
async def log_api_key():
    env_key = (os.getenv("SILICONFLOW_API_KEY") or "").strip()
    api_key = get_siliconflow_api_key()
    source = "env" if env_key else ("config" if api_key else "missing")
    log_line(f"SILICONFLOW_API_KEY({source})={mask_key(api_key)}")

async def synthesize_tts(text: str, voice: str, rate: str) -> bytes:
    # 创建缓存目录
    TTS_CACHE_DIR.mkdir(exist_ok=True)
    
    # 生成缓存文件名：句子md5 + 语音 + 语速
    md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    cache_filename = f"{md5_hash}_{voice.replace(' ', '_')}_{rate.replace('+', 'p').replace('-', 'm').replace('%', 'pc')}.mp3"
    cache_path = TTS_CACHE_DIR / cache_filename
    
    # 检查缓存是否存在
    if cache_path.exists():
        try:
            with open(cache_path, 'rb') as f:
                return f.read()
        except Exception:
            pass
    
    # 缓存不存在，生成新的TTS
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    audio_bytes = bytearray()
    async for chunk in communicator.stream():
        if chunk.get("type") == "audio":
            audio_bytes.extend(chunk.get("data", b""))
    
    audio_bytes = bytes(audio_bytes)
    
    # 保存到缓存
    if audio_bytes:
        try:
            with open(cache_path, 'wb') as f:
                f.write(audio_bytes)
        except Exception:
            pass
    
    return audio_bytes


def get_pocket_tts_model():
    global _POCKET_TTS_MODEL
    if _POCKET_TTS_MODEL is not None:
        return _POCKET_TTS_MODEL

    with _POCKET_TTS_MODEL_LOCK:
        if _POCKET_TTS_MODEL is None:
            try:
                from pocket_tts import TTSModel
            except ImportError as exc:
                raise RuntimeError(
                    "pocket-tts is not installed. Run `pip install pocket-tts` in the server environment."
                ) from exc

            _POCKET_TTS_MODEL = TTSModel.load_model()

    return _POCKET_TTS_MODEL


def get_pocket_tts_voice_state(voice: str):
    normalized_voice = (voice or "").strip() or "alba"
    cached_state = _POCKET_TTS_VOICE_STATES.get(normalized_voice)
    if cached_state is not None:
        return cached_state

    with _POCKET_TTS_VOICE_LOCK:
        cached_state = _POCKET_TTS_VOICE_STATES.get(normalized_voice)
        if cached_state is None:
            model = get_pocket_tts_model()
            cached_state = model.get_state_for_audio_prompt(normalized_voice)
            _POCKET_TTS_VOICE_STATES[normalized_voice] = cached_state

    return cached_state


def pcm_tensor_to_wav_bytes(audio, sample_rate: int) -> bytes:
    audio_array = audio.detach().cpu().numpy()
    if audio_array.ndim != 1:
        audio_array = np.reshape(audio_array, (-1,))

    if np.issubdtype(audio_array.dtype, np.floating):
        audio_array = np.clip(audio_array, -1.0, 1.0)
        audio_array = (audio_array * 32767.0).astype(np.int16)
    elif audio_array.dtype != np.int16:
        audio_array = audio_array.astype(np.int16)

    with io.BytesIO() as buffer:
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())
        return buffer.getvalue()


def synthesize_pocket_tts_sync(text: str, voice: str) -> bytes:
    TTS_CACHE_DIR.mkdir(exist_ok=True)

    normalized_voice = (voice or "").strip() or "alba"
    safe_voice = re.sub(r"[^0-9A-Za-z._-]+", "_", normalized_voice)
    md5_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    cache_filename = f"{md5_hash}_pocket_{safe_voice}.wav"
    cache_path = TTS_CACHE_DIR / cache_filename

    if cache_path.exists():
        try:
            return cache_path.read_bytes()
        except Exception:
            pass

    model = get_pocket_tts_model()
    voice_state = get_pocket_tts_voice_state(normalized_voice)
    audio = model.generate_audio(voice_state, text)
    wav_bytes = pcm_tensor_to_wav_bytes(audio, model.sample_rate)

    if wav_bytes:
        try:
            cache_path.write_bytes(wav_bytes)
        except Exception:
            pass

    return wav_bytes

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
            # 移除文件后缀
            chapter_name = chapter_file.name
            if chapter_name.endswith('.txt'):
                chapter_name = chapter_name[:-4]
            chapters.append(ChapterInfo(name=chapter_name))

        if chapters:  # 只添加有章节的书籍
            books.append(BookInfo(name=book_path.name, chapters=chapters))

    return books


def get_chapter_path(book_name: str, chapter_name: str) -> Path:
    """获取章节文件的路径"""
    # 添加.txt后缀
    if not chapter_name.endswith('.txt'):
        chapter_name = f"{chapter_name}.txt"
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
    遵循第一性原理：
    1. 遇到换行必须分割
    2. 处理段内分句（根据标点符号）
    """
    if not text or not text.strip():
        return []

    sentences = []
    current_sentence = ''
    i = 0
    n = len(text)

    while i < n:
        # 逐字符处理
        char = text[i]
        current_sentence += char
        
        # 规则1：遇到换行必须分割
        if char == '\n':
            if current_sentence.strip():
                sentences.append(current_sentence)
            current_sentence = ''
            i += 1
            continue
        
        # 规则2：处理段内分句（根据标点符号）
        if char in '.!？。':
            # 检查是否是真句子结束
            
            # 1. 检查是否是省略号 "..." 或 "……"
            if (i + 2 < n and text[i+1] == '.' and text[i+2] == '.') or \
               (i + 1 < n and text[i+1] == '…'):
                i += 3 if text[i+1] == '.' else 2
                continue
            
            # 2. 检查点号前是否是已知缩写
            word_start = i - 1
            while word_start >= 0 and not text[word_start].isspace():
                word_start -= 1
            word_start += 1
            
            word = text[word_start:i].lower()
            if word in ENGLISH_ABBREVIATIONS:
                i += 1
                continue
            
            # 3. 检查是否是单个大写字母+点
            if re.match(r'^[a-zA-Z]$', text[word_start:i]):
                i += 1
                continue
            
            # 4. 检查后面是否是大写字母（新句子开始）
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            
            if j < n:
                next_char = text[j]
                # 检查是否是引号，然后是大写字母
                if next_char == '"' and j + 1 < n and text[j + 1].isupper():
                    pass  # 这是一个新句子的开始
                elif not next_char.isupper() and next_char != '"' and not next_char.isdigit():
                    i += 1
                    continue
            
            # 是真句子结束，分割句子
            if current_sentence.strip():
                sentences.append(current_sentence)
            current_sentence = ''
        
        i += 1
    
    # 处理最后一个句子
    if current_sentence.strip():
        sentences.append(current_sentence)
    
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
            # 移除文件后缀
            chapter_name = chapter_file.name
            if chapter_name.endswith('.txt'):
                chapter_name = chapter_name[:-4]
            chapters.append({"name": chapter_name})

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
            # 移除文件后缀
            chapter_name = chapter_file.name
            if chapter_name.endswith('.txt'):
                chapter_name = chapter_name[:-4]
            chapters.append({"name": chapter_name})

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





@app.get("/tts/pocket")
async def pocket_tts(
    text: str = Query(..., min_length=1, description="要朗读的文本"),
    voice: str = Query("alba", description="Pocket TTS voice，支持内置 voice 名称或本地 wav/safetensors 路径")
):
    try:
        audio = await run_in_threadpool(synthesize_pocket_tts_sync, text, voice)
        if not audio:
            raise HTTPException(status_code=500, detail="Pocket TTS returned empty audio")
        return Response(content=audio, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pocket TTS error: {str(e)}")


@app.post("/analyze_stream")
async def analyze_text_stream_endpoint(request: AnalyzeRequest):
    api_key = get_siliconflow_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing SILICONFLOW_API_KEY (env or config.ini)")

    async def stream_generator():
        async for delta in analyze_text_stream(api_key, request.text, request.model):
            yield delta

    return StreamingResponse(stream_generator(), media_type="text/plain; charset=utf-8", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    })




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
