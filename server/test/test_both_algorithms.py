#!/usr/bin/env python3
"""
测试规则算法和nltk算法的分句结果
"""

import sys
sys.path.append('src')

from sentence_service import split_sentences_rule, split_sentences_nltk, NLTK_AVAILABLE

# 测试文本
test_text = """CHAPTER TWO 
 THE VANISHING GLASS 
 Nearly ten years had passed since the Dursleys had woken up to find their nephew on the front step, but Privet Drive had hardly changed at all. 
"""

print("测试文本:")
print(repr(test_text))
print("\n规则算法结果:")
r_sentences = split_sentences_rule(test_text)
for i, sentence in enumerate(r_sentences):
    print(f"句子 {i+1}: {repr(sentence)}")

print(f"\n规则算法共分成了 {len(r_sentences)} 句")

if NLTK_AVAILABLE:
    print("\nnltk算法结果:")
    n_sentences = split_sentences_nltk(test_text)
    for i, sentence in enumerate(n_sentences):
        print(f"句子 {i+1}: {repr(sentence)}")
    print(f"\nnltk算法共分成了 {len(n_sentences)} 句")
else:
    print("\nnltk不可用，无法测试nltk算法")
