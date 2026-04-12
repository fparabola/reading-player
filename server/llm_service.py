"""
LLM服务
提供与大语言模型交互的接口
"""
import json
import traceback
from openai import OpenAI
from typing import Optional, AsyncGenerator


def build_analyze_prompt(text: str) -> str:
    """
    构建分析提示
    """
    # 从md文件中读取prompt
    prompt_path = Path(__file__).parent / "prompt" / "analyze_prompt.md"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    # 替换文本占位符
    return prompt_template.replace("{text}", text)


def analyze_text(api_key: str, text: str, model: Optional[str] = None) -> str:
    """
    分析文本
    
    参数:
    - api_key: API密钥
    - text: 要分析的文本
    - model: 模型名称
    
    返回:
    - 分析结果
    """
    prompt = build_analyze_prompt(text)
    model_name = model or "Qwen/Qwen3-14B"
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是英语句子解析助手，中文回答。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM exception: {str(e)}")
        print(traceback.format_exc())
        raise


def analyze_text_stream(api_key: str, text: str, model: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    流式分析文本
    
    参数:
    - api_key: API密钥
    - text: 要分析的文本
    - model: 模型名称
    
    返回:
    - 流式分析结果
    """
    prompt = build_analyze_prompt(text)
    model_name = model or "Qwen/Qwen3-14B"
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是英语句子解析助手，中文回答。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        print(f"LLM exception: {str(e)}")
        print(traceback.format_exc())
        pass
