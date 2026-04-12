"""
对比测试规则算法和nltk算法
"""
import urllib.request
import json

url = "http://localhost:8000/split"

text = """Mr. and Mrs. Dursley, of number four, Privet Drive, were proud to say that they were perfectly normal, thank you very much. They were the last people you'd expect to be involved in anything strange or mysterious, because they just didn't hold with such nonsense.
Mr. Dursley was the director of a firm called Grunnings, which made drills. He was a big, beefy man with hardly any neck, although he did have a very large mustache. Mrs. Dursley was thin and blonde and had nearly twice the usual amount of neck, which came in very useful as she spent so much of her time craning over garden fences, spying on the neighbors."""

# 测试规则算法
data_r = json.dumps({"text": text, "language": "en", "method": "r"}).encode('utf-8')
req_r = urllib.request.Request(url, data=data_r, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req_r, timeout=10) as response:
    result_r = json.loads(response.read().decode('utf-8'))

# 测试nltk算法
data_n = json.dumps({"text": text, "language": "en", "method": "n"}).encode('utf-8')
req_n = urllib.request.Request(url, data=data_n, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req_n, timeout=10) as response:
    result_n = json.loads(response.read().decode('utf-8'))

print("="*60)
print(f"规则算法 (规则: {result_r['count']}句)")
print("="*60)
for i, s in enumerate(result_r['sentences'], 1):
    print(f"{i}. {s}")

print()
print("="*60)
print(f"NLTK算法 (NLTK: {result_n['count']}句)")
print("="*60)
for i, s in enumerate(result_n['sentences'], 1):
    print(f"{i}. {s}")

print()
print("="*60)
print("对比 Differences")
print("="*60)
if result_r['count'] != result_n['count']:
    print(f"❌ 句数不同: 规则={result_r['count']}, NLTK={result_n['count']}")

# 找出差异
for i, (r_s, n_s) in enumerate(zip(result_r['sentences'], result_n['sentences']), 1):
    if r_s != n_s:
        print(f"\n第{i}句不同:")
        print(f"  规则: {r_s}")
        print(f"  NLTK: {n_s}")
