from llm_service import rebuild_annotated_html

# 测试数据：多个标注
structured_annotations = {
    "text": "I will take my coat off and put on my hat.",
    "annotations": [
        {
            "id": "P1",
            "type": "phrase",
            "risk": "high",
            "text": "take off",
            "parts": [
                {
                    "part": 1,
                    "text": "take",
                    "start": 7,
                    "end": 11
                },
                {
                    "part": 2,
                    "text": "off",
                    "start": 22,
                    "end": 25
                }
            ]
        },
        {
            "id": "P2",
            "type": "phrase",
            "risk": "medium",
            "text": "put on",
            "parts": [
                {
                    "part": 1,
                    "text": "put",
                    "start": 26,
                    "end": 29
                },
                {
                    "part": 2,
                    "text": "on",
                    "start": 30,
                    "end": 32
                }
            ]
        }
    ]
}

# 修正位置信息
test_text = "I will take my coat off and put on my hat."
print(f"原始文本: {test_text}")
print(f"文本长度: {len(test_text)}")
print(f"位置 7-11: '{test_text[7:11]}'")
print(f"位置 22-25: '{test_text[22:25]}'")
print(f"位置 26-29: '{test_text[26:29]}'")
print(f"位置 30-32: '{test_text[30:32]}'")

# 修正后的测试数据
structured_annotations_corrected = {
    "text": "I will take my coat off and put on my hat.",
    "annotations": [
        {
            "id": "P1",
            "type": "phrase",
            "risk": "high",
            "text": "take off",
            "parts": [
                {
                    "part": 1,
                    "text": "take",
                    "start": 7,
                    "end": 11
                },
                {
                    "part": 2,
                    "text": "off",
                    "start": 21,
                    "end": 24
                }
            ]
        },
        {
            "id": "P2",
            "type": "phrase",
            "risk": "medium",
            "text": "put on",
            "parts": [
                {
                    "part": 1,
                    "text": "put",
                    "start": 26,
                    "end": 29
                },
                {
                    "part": 2,
                    "text": "on",
                    "start": 30,
                    "end": 32
                }
            ]
        }
    ]
}

# 重建HTML
annotated_html = rebuild_annotated_html(structured_annotations)
print("重建的HTML:")
print(annotated_html)
