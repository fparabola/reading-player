#!/usr/bin/env python3
"""
测试split_sentences函数的实际行为
"""

import sys
sys.path.append('src')

from sentence_service import split_sentences

# 测试文本
test_text = '"It all gets so confusing if we keep saying \'You-Know-Who.\' I have never seen any reason to be frightened of saying Voldemort\'s name. \n "I know you haven \'t, said Professor McGonagall, sounding half exasperated, half admiring. \n' 

print("测试文本:")
print(repr(test_text))
print("\n文本长度:", len(test_text))
print("包含换行符:", '\n' in test_text)

print("\nsplit_sentences结果:")
sentences, method = split_sentences(test_text, "en", "r")
for i, sentence in enumerate(sentences):
    print(f"句子 {i+1}: {repr(sentence)}")

print(f"\n共分成了 {len(sentences)} 句")
print(f"使用的算法: {method}")
