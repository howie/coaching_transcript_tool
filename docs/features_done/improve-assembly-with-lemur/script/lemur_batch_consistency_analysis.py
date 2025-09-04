#!/usr/bin/env python3
"""
分析 LeMUR 批次處理結果不一致的原因
"""

import json
import re

def analyze_batch_consistency():
    """分析批次處理的一致性問題"""
    
    print("🔍 分析 LeMUR 批次處理不一致問題")
    print("=" * 80)
    
    # 從用戶選擇的文本分析問題
    problem_segments = [
        {
            "speaker": "Speaker_1",
            "text": "這件 事 啊 你 用 的 這個 字 也蠻.",
            "quality": "差",
            "issues": ["字間有空格", "標點不完整", "句子結尾不當"]
        },
        {
            "speaker": "Speaker_2", 
            "text": "算有點 強烈 喔 對 其實 沒有 那麼 嚴重 應該 就是 說 反悔 的 人 或者 是 爽 約 的 人 就是 比較 這比較 正確 一點對 應該 爽約 的.",
            "quality": "差",
            "issues": ["字間有空格", "標點混亂", "重複用詞未修正", "句子結尾不當"]
        },
        {
            "speaker": "Speaker_1",
            "text": "人 對 所以 聽 起來 剛才 我 有 聽 到 一個 狀態 就是 說 就 你 不 想要 成為 變成 你 是 爽 約 的 人 了 是嗎?",
            "quality": "中等",
            "issues": ["字間有空格", "問號正確但英文問號"]
        }
    ]
    
    good_segments = [
        {
            "speaker": "Speaker_2",
            "text": "是，對。因為我其實從頭到尾都很積極地一直在詢問他的意見想法。",
            "quality": "優秀",
            "features": ["無空格", "標點正確", "語句完整", "中文標點"]
        },
        {
            "speaker": "Speaker_2",
            "text": "不想去，是嗎？對，因為我想不通，如果一個人很想去，他為什麼不趕快確認他的行程呢？對，這是我想不通的地方。所以我就覺得他可能是不想，但我也想不通他為什麼不直接跟我說OK。",
            "quality": "優秀",
            "features": ["無空格", "標點豐富", "語句流暢", "中文問號", "邏輯清晰"]
        }
    ]
    
    print("❌ 品質差的 segments 分析:")
    for i, seg in enumerate(problem_segments, 1):
        print(f"\n{i}. {seg['speaker']}: {seg['text']}")
        print(f"   問題: {', '.join(seg['issues'])}")
        
        # 分析空格問題
        space_count = seg['text'].count(' ')
        char_count = len(seg['text'])
        space_ratio = space_count / char_count if char_count > 0 else 0
        print(f"   空格統計: {space_count} 個空格 / {char_count} 字符 = {space_ratio:.2%}")
    
    print("\n✅ 品質好的 segments 分析:")
    for i, seg in enumerate(good_segments, 1):
        print(f"\n{i}. {seg['speaker']}: {seg['text']}")
        print(f"   優點: {', '.join(seg['features'])}")
        
        space_count = seg['text'].count(' ')
        char_count = len(seg['text'])
        space_ratio = space_count / char_count if char_count > 0 else 0
        print(f"   空格統計: {space_count} 個空格 / {char_count} 字符 = {space_ratio:.2%}")

def identify_root_causes():
    """識別根本原因"""
    
    print("\n🎯 可能的根本原因分析:")
    print("=" * 80)
    
    causes = [
        {
            "原因": "批次處理順序不一致",
            "說明": "LeMUR 對不同批次的內容品質不同，早期批次可能品質較差",
            "證據": "問題 segments 集中在前面時間段",
            "可能性": "高"
        },
        {
            "原因": "Prompt 執行不一致", 
            "說明": "Claude 3.5 Sonnet 對同樣 prompt 在不同批次執行效果不同",
            "證據": "相同 prompt 產生不同品質結果",
            "可能性": "高"
        },
        {
            "原因": "批次內容影響處理品質",
            "說明": "某些內容（如較短或較混亂的 segments）更難處理",
            "證據": "問題 segments 相對較短且內容不完整",
            "可能性": "中"
        },
        {
            "原因": "解析邏輯問題",
            "說明": "LeMUR 返回正確但解析時出問題",
            "證據": "需要檢查實際 LeMUR 回應",
            "可能性": "中"
        },
        {
            "原因": "原始數據品質差異",
            "說明": "某些原始 segments 本身品質就較差",
            "證據": "AssemblyAI 可能在某些時間段轉錄品質較差",
            "可能性": "低"
        }
    ]
    
    for i, cause in enumerate(causes, 1):
        print(f"\n{i}. {cause['原因']} (可能性: {cause['可能性']})")
        print(f"   說明: {cause['說明']}")
        print(f"   證據: {cause['證據']}")

def suggest_solutions():
    """建議解決方案"""
    
    print("\n💡 建議解決方案:")
    print("=" * 80)
    
    solutions = [
        {
            "方案": "強化 Prompt 一致性",
            "具體做法": [
                "在每個批次 prompt 開頭加強調不要空格的指令",
                "增加具體範例說明正確格式",
                "使用更嚴格的格式要求"
            ],
            "優先級": "高",
            "實施難度": "低"
        },
        {
            "方案": "增加後處理清理步驟",
            "具體做法": [
                "對 LeMUR 回應進行額外的清理",
                "移除中文字之間的空格",
                "標準化標點符號格式"
            ],
            "優先級": "高", 
            "實施難度": "低"
        },
        {
            "方案": "批次品質驗證",
            "具體做法": [
                "對每個批次結果進行品質檢查",
                "發現品質差的批次自動重新處理",
                "記錄批次處理成功率"
            ],
            "優先級": "中",
            "實施難度": "中"
        },
        {
            "方案": "調整批次策略",
            "具體做法": [
                "減少批次大小確保處理品質",
                "優化批次分割邏輯",
                "考慮內容相似性分批"
            ],
            "優先級": "中",
            "實施難度": "中"
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"\n{i}. {solution['方案']} (優先級: {solution['優先級']}, 難度: {solution['實施難度']})")
        for j, step in enumerate(solution['具體做法'], 1):
            print(f"   {j}. {step}")

def immediate_fix_recommendations():
    """立即修復建議"""
    
    print("\n🚨 立即修復建議:")
    print("=" * 80)
    
    fixes = [
        {
            "修復": "強化 Prompt",
            "代碼位置": "_process_punctuation_batch() 方法",
            "修改內容": """
在中文 prompt 開頭加上:
IMPORTANT: 絕對不要在中文字之間加空格！中文應該連續書寫。
正確範例: 你好我是教練 → 你好，我是教練。
錯誤範例: 你 好 我 是 教 練 → 這是錯誤的！

然後是原有的 prompt...
""",
            "預期效果": "減少空格問題 80%"
        },
        {
            "修復": "增加後處理清理",
            "代碼位置": "_parse_batch_response_to_segments() 方法",
            "修改內容": """
在解析每行文本後，對中文文本進行清理:
# 移除中文字之間的不必要空格
if is_chinese_text(text):
    text = re.sub(r'([\\u4e00-\\u9fff])\\s+([\\u4e00-\\u9fff])', r'\\1\\2', text)
""",
            "預期效果": "消除剩餘空格問題"
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n{i}. {fix['修復']}")
        print(f"   位置: {fix['代碼位置']}")
        print(f"   修改: {fix['修改內容']}")
        print(f"   效果: {fix['預期效果']}")

if __name__ == "__main__":
    analyze_batch_consistency()
    identify_root_causes() 
    suggest_solutions()
    immediate_fix_recommendations()
    
    print("\n🎯 總結:")
    print("主要問題是 LeMUR 批次處理不一致，建議先實施 Prompt 強化和後處理清理。")