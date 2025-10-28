"""
快速修復所有 enum 值訪問的腳本
"""
import re
import os


def fix_enum_value(content):
    """修復 .value 訪問"""
    # 修復模式：xxx.current_engagement_state.value
    patterns = [
        (r'(\w+)\.current_engagement_state\.value',
         r'\1.current_engagement_state if isinstance(\1.current_engagement_state, str) else \1.current_engagement_state.value'),
        (r'(\w+)\.behavioral_archetype\.value',
         r'\1.behavioral_archetype if isinstance(\1.behavioral_archetype, str) else \1.behavioral_archetype.value'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content


def process_file(filepath):
    """處理單個文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    content = fix_enum_value(content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


# 修復文件
files_to_fix = [
    'src/utils/feedback_learner.py',
    'src/agents/feedback_processor.py',
]

print("修復 enum 值訪問...\n")
for filepath in files_to_fix:
    if os.path.exists(filepath):
        if process_file(filepath):
            print(f"✅ 已修復: {filepath}")
        else:
            print(f"⏭️  跳過: {filepath} (無需修改)")
    else:
        print(f"⚠️  找不到: {filepath}")

print("\n完成!")
