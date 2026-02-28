"""
分句服务
提供文本分句接口，目前支持英文
支持两种算法：规则算法(r)和nltk(n)

新增功能：
- 书籍目录接口：获取资源目录中的书籍和章节
- 章节内容接口：获取章节的片段内容
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import re
import os
from pathlib import Path
from typing import List, Optional
import uvicorn

app = FastAPI(title="Sentence Splitter API", version="2.0.0")

# 资源目录常量
RESOURCE_DIR = Path(__file__).parent / "resource"


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
        for chapter_file in sorted(book_path.iterdir()):
            if chapter_file.is_file() and chapter_file.suffix.lower() == '.txt':
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
    paragraph_end: bool  # 是否到达段落结尾


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

    # 规范化：统一换行符为空格，去除多余空格
    text = re.sub(r'\r\n|\r|\n', ' ', text.strip())
    text = re.sub(r'\s+', ' ', text)

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
    获取书籍目录接口

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
        for chapter_file in sorted(book_path.iterdir()):
            if chapter_file.is_file() and chapter_file.suffix.lower() == '.txt':
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
    position: int = Query(0, ge=0, description="起始位置（字符索引），从0开始")
):
    """
    获取章节内容接口

    参数:
        book_name: 书名（文件夹名）
        chapter_name: 章节名（txt文件名）
        position: 起始位置（字符索引），从0开始

    返回:
        从起始位置到段落结尾的文本片段
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

        # 从起始位置开始查找段落结尾
        # 段落结尾定义为：换行符或连续的换行符后的第一个非空内容开始位置
        start_pos = position
        end_pos = len(text)

        # 查找下一个段落分隔符（双换行或文件结尾）
        remaining_text = text[position:]

        # 查找双换行符（段落分隔符）
        paragraph_end = remaining_text.find('\n\n')
        if paragraph_end != -1:
            end_pos = position + paragraph_end + 2  # 包含换行符
        else:
            # 查找单换行符（行分隔符）
            line_end = remaining_text.find('\n')
            if line_end != -1:
                end_pos = position + line_end + 1
            else:
                # 没有换行符，返回到文件结尾
                end_pos = len(text)

        # 如果位置很小且没有找到换行符，返回一段合理长度的内容
        if end_pos - start_pos > 2000:
            end_pos = start_pos + 2000

        content = text[start_pos:end_pos]

        return ChapterContentResponse(
            book_name=book_name,
            chapter_name=chapter_name,
            text=content,
            start_position=start_pos,
            end_position=end_pos,
            paragraph_end=(end_pos >= len(text) or text[end_pos-2:end_pos] == '\n\n' or text[end_pos-1:end_pos] == '\n')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading chapter: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
