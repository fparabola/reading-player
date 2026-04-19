#!/usr/bin/env python3
"""
测试处理引号后的标点符号
"""

import sys
sys.path.append('src')

from sentence_service import split_sentences_rule

# 测试文本（包含引号和标点符号）
test_text = '"It all gets so confusing if we keep saying \'You-Know-Who.\' I have never seen any reason to be frightened of saying Voldemort\'s name. "I know you haven \'t, said Professor McGonagall, sounding half exasperated, half admiring.' 

print("测试文本:")
print(repr(test_text))
print("\n文本长度:", len(test_text))

print("\nsplit_sentences_rule结果:")
sentences = split_sentences_rule(test_text)
for i, sentence in enumerate(sentences):
    print(f"句子 {i+1}: {repr(sentence)}")

print(f"\n共分成了 {len(sentences)} 句")
