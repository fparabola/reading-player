"""
LLM服务
提供与大语言模型交互的接口
"""
import json
import traceback
from openai import OpenAI
from typing import Optional, AsyncGenerator
from config_helper import config_helper
from prompt_helper import prompt_helper

# API配置
API_CONFIG = {
    "base_url": config_helper.get("api.base_url"),
    "default_model": config_helper.get("api.default_model")
}


def build_analyze_prompt() -> str:
    """
    构建分析提示（作为system prompt）
    """
    # 使用prompt_helper获取prompt
    prompt_template = prompt_helper.get_prompt("", "analyze_prompt")
    # 移除文本占位符部分
    if prompt_template:
        # 移除"以下是文本：\n{text}"部分
        prompt_template = prompt_template.split("以下是文本：")[0].strip()
    return prompt_template if prompt_template else "你是英语句子解析助手，中文回答。"





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
    system_prompt = build_analyze_prompt()
    user_prompt = text
    model_name = model or API_CONFIG["default_model"]
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=API_CONFIG["base_url"]
        )
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
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
