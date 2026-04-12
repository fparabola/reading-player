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
    "base_url": config_helper.get_base_url(),
    "default_model": config_helper.get_default_model(),
    "system_prompt": config_helper.get_system_prompt()
}


def build_analyze_prompt(text: str) -> str:
    """
    构建分析提示
    """
    # 使用prompt_helper获取prompt
    prompt_template = prompt_helper.get_prompt("", "analyze_prompt")
    if not prompt_template:
        # 如果获取失败，使用默认prompt
        prompt_template = (
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
            "{text}"
        )
    # 替换文本占位符
    return prompt_template.replace("{text}", text)





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
    model_name = model or API_CONFIG["default_model"]
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=API_CONFIG["base_url"]
        )
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": API_CONFIG["system_prompt"]},
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
