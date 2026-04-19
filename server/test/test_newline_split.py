#!/usr/bin/env python3
"""
测试换行符分句功能
"""

import sys
sys.path.append('src')

import sentence_service
from sentence_service import split_sentences_rule

# 测试文本
test_text = """CHAPTER TWO 
 THE VANISHING GLASS 
 Nearly ten years had passed since the Dursleys had woken up to find their nephew on the front step, but Privet Drive had hardly changed at all. 
"""

print("测试文本:")
print(repr(test_text))
print("\n分句结果:")
sentences = split_sentences_rule(test_text)
for i, sentence in enumerate(sentences):
    print(f"句子 {i+1}: {repr(sentence)}")

print(f"\n共分成了 {len(sentences)} 句")
