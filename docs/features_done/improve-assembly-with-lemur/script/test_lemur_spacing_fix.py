#!/usr/bin/env python3
"""
測試 LeMUR 空格修復功能
"""

import re
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def clean_chinese_text_spacing(text: str) -> str:
    """Clean unwanted spaces between Chinese characters."""

    # Iteratively remove spaces between Chinese characters until no more changes
    # This handles cases like "這 是 測 試" → "這是測試"
    prev_text = ""
    while prev_text != text:
        prev_text = text
        # Remove spaces between Chinese characters (CJK Unified Ideographs)
        text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)

    # Remove spaces around Chinese punctuation
    text = re.sub(r"\s*([，。？！；：「」『』（）【】〔〕])\s*", r"\1", text)

    # Clean up multiple spaces but preserve single spaces between non-Chinese words
    text = re.sub(r"\s+", " ", text).strip()

    return text


def test_spacing_fixes():
    """測試空格修復功能"""

    print("🧪 測試 LeMUR 空格修復功能")
    print("=" * 80)

    # 測試案例：來自實際問題數據
    test_cases = [
        {
            "name": "問題案例 1",
            "input": "這件 事 啊 你 用 的 這個 字 也蠻.",
            "expected": "這件事啊你用的這個字也蠻。",
            "issues": ["字間空格", "句號缺失"],
        },
        {
            "name": "問題案例 2",
            "input": "算有點 強烈 喔 對 其實 沒有 那麼 嚴重 應該 就是 說 反悔 的 人 或者 是 爽 約 的 人 就是 比較 這比較 正確 一點對 應該 爽約 的.",
            "expected": "算有點強烈喔對其實沒有那麼嚴重應該就是說反悔的人或者是爽約的人就是比較這比較正確一點對應該爽約的。",
            "issues": ["大量字間空格", "重複詞彙"],
        },
        {
            "name": "問題案例 3",
            "input": "人 對 所以 聽 起來 剛才 我 有 聽 到 一個 狀態 就是 說 就 你 不 想要 成為 變成 你 是 爽 約 的 人 了 是嗎?",
            "expected": "人對所以聽起來剛才我有聽到一個狀態就是說就你不想要成為變成你是爽約的人了是嗎？",
            "issues": ["字間空格", "英文問號"],
        },
        {
            "name": "正常案例（應該保持不變）",
            "input": "是，對。因為我其實從頭到尾都很積極地一直在詢問他的意見想法。",
            "expected": "是，對。因為我其實從頭到尾都很積極地一直在詢問他的意見想法。",
            "issues": [],
        },
        {
            "name": "混合案例",
            "input": "你 好 ， 我 是 教 練 。 今 天 怎 麼 樣 ？",
            "expected": "你好，我是教練。今天怎麼樣？",
            "issues": ["字間空格", "標點前後空格"],
        },
    ]

    success_count = 0

    for i, case in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}: {case['name']}")
        print("-" * 50)
        print(f"輸入: {case['input']}")
        print(f"預期: {case['expected']}")

        # 執行清理
        result = clean_chinese_text_spacing(case["input"])
        print(f"實際: {result}")

        # 分析結果
        input_spaces = case["input"].count(" ")
        result_spaces = result.count(" ")
        space_reduction = input_spaces - result_spaces

        print(f"空格統計: {input_spaces} → {result_spaces} (減少 {space_reduction})")

        # 檢查是否符合預期
        if result == case["expected"]:
            print("✅ 通過")
            success_count += 1
        else:
            print("❌ 未通過")

        if case["issues"]:
            print(f"已知問題: {', '.join(case['issues'])}")

    print("\n" + "=" * 80)
    print(
        f"📊 測試結果: {success_count}/{len(test_cases)} 通過 ({success_count / len(test_cases) * 100:.1f}%)"
    )

    if success_count == len(test_cases):
        print("🎉 所有測試通過！空格修復功能正常工作。")
    else:
        print("⚠️  有些測試未通過，需要進一步調整。")

    return success_count == len(test_cases)


def test_regex_patterns():
    """測試正則表達式模式"""

    print("\n🔧 測試正則表達式模式")
    print("=" * 80)

    patterns = [
        {
            "name": "中文字間空格移除",
            "pattern": r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])",
            "replacement": r"\1\2",
            "test_strings": [
                ("你 好", "你好"),
                ("這 是 測 試", "這是測試"),  # 應該變成 "這是測試" 經過多次應用
                ("Hello 你好 World", "Hello 你好 World"),  # 英文保持空格
            ],
        },
        {
            "name": "中文標點周圍空格清理",
            "pattern": r"\s*([，。？！；：「」『』（）【】〔〕])\s*",
            "replacement": r"\1",
            "test_strings": [
                ("你好 ， 世界", "你好，世界"),
                ("是嗎 ？", "是嗎？"),
                ("「 你好 」", "「你好」"),
            ],
        },
    ]

    for pattern_test in patterns:
        print(f"\n測試: {pattern_test['name']}")
        print(f"模式: {pattern_test['pattern']}")

        for test_str, expected in pattern_test["test_strings"]:
            result = re.sub(
                pattern_test["pattern"], pattern_test["replacement"], test_str
            )
            status = "✅" if result == expected else "❌"
            print(f'  {status} "{test_str}" → "{result}" (預期: "{expected}")')


if __name__ == "__main__":
    success = test_spacing_fixes()
    test_regex_patterns()

    print("\n🎯 總結:")
    if success:
        print("修復功能測試通過，應該能有效解決 LeMUR 批次處理的空格問題。")
    else:
        print("修復功能需要進一步調整，請檢查正則表達式模式。")
