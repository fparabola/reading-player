"""
分句服务
提供文本分句接口，目前支持英文
支持两种算法：规则算法(r)和nltk(n)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from typing import List, Optional
import uvicorn

app = FastAPI(title="Sentence Splitter API", version="2.0.0")


class SentenceRequest(BaseModel):
    text: str
    language: str
    method: Optional[str] = "r"  # r=规则算法, n=nltk, 默认规则算法


class SentenceResponse(BaseModel):
    sentences: List[str]
    count: int
    method: str  # 返回实际使用的算法


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
            "/split": "POST - Split text into sentences"
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
