#!/usr/bin/env python3
"""
测试换行符分句功能（简化版）
"""

import re

# 简化版的split_sentences_rule函数，只测试换行符处理
def split_sentences_rule_simple(text):
    """
    简化版的规则算法分句，只测试换行符处理
    """
    if not text or not text.strip():
        return []

    sentences = []
    start = 0
    i = 0
    n = len(text)

    while i < n:
        # 查找句子的结束标记（包括中文标点和换行符）
        if text[i] not in '.!？。\n':
            i += 1
            continue

        # 如果是换行符，直接切分句子
        if text[i] == '\n':
            # 处理连续的换行符
            j = i
            while j < n and text[j] == '\n':
                j += 1
            # 保留原始文本，包括换行符和空格
            sentence = text[start:j]
            if sentence.strip():
                sentences.append(sentence)
            start = j
            i = j
            continue

        # 其他标点符号的处理（简化版）
        i += 1
        # 保留原始文本，包括换行符和空格
        sentence = text[start:i]
        if sentence.strip():
            sentences.append(sentence)

        start = i

    if start < n:
        sentence = text[start:]
        if sentence.strip():
            sentences.append(sentence)

    return sentences

# 测试文本
test_text = """CHAPTER TWO 
 THE VANISHING GLASS 
 Nearly ten years had passed since the Dursleys had woken up to find their nephew on the front step, but Privet Drive had hardly changed at all. 
"""

print("测试文本:")
print(repr(test_text))
print("\n分句结果:")
sentences = split_sentences_rule_simple(test_text)
for i, sentence in enumerate(sentences):
    print(f"句子 {i+1}: {repr(sentence)}")

print(f"\n共分成了 {len(sentences)} 句")
