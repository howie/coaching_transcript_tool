#!/bin/bash
#
# 完整流程測試範例腳本
# 
# 用途：測試音檔上傳 → 轉檔 → LeMUR優化的完整流程
# 
# 使用方法：
#   1. 設定環境變量
#   2. 修改音檔路徑
#   3. 執行腳本
#

set -e  # 遇到錯誤立即退出

# ================================
# 設定區域 - 請修改以下參數
# ================================

# API認證Token (必需)
AUTH_TOKEN="${AUTH_TOKEN:-your_token_here}"

# API URL (可選)
API_URL="${API_URL:-http://localhost:8000}"

# 音檔路徑 (請修改為實際路徑)
AUDIO_FILE="${AUDIO_FILE:-/path/to/your/coaching_session.mp3}"

# 會談標題 (可選)
SESSION_TITLE="LeMUR優化測試 - $(date +%Y%m%d_%H%M%S)"

# 自訂提示詞 (可選)
SPEAKER_PROMPT="這是一段教練與客戶的對話。請識別：教練（通常提問引導）和客戶（通常分享問題）。請將說話者標記為「教練」或「客戶」。"

PUNCTUATION_PROMPT="請改善這段教練對話的標點符號：1) 在適當位置加上逗號句號 2) 改善語氣詞標點 3) 保持原有說話風格 4) 讓對話更容易閱讀。請保持內容完整，只改善標點格式。"

# 結果輸出檔案
OUTPUT_FILE="results_full_pipeline_$(date +%Y%m%d_%H%M%S).json"

# ================================
# 預檢查
# ================================

echo "🔍 執行預檢查..."

# 檢查認證Token
if [ "$AUTH_TOKEN" = "your_token_here" ]; then
    echo "❌ 錯誤：請設定正確的AUTH_TOKEN"
    echo "   export AUTH_TOKEN=\"your_actual_token\""
    exit 1
fi

# 檢查音檔是否存在
if [ ! -f "$AUDIO_FILE" ]; then
    echo "❌ 錯誤：音檔不存在: $AUDIO_FILE"
    echo "   請修改 AUDIO_FILE 為正確的檔案路徑"
    exit 1
fi

# 檢查腳本是否存在
SCRIPT_PATH="../test_lemur_full_pipeline.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 錯誤：測試腳本不存在: $SCRIPT_PATH"
    echo "   請確認當前目錄位置正確"
    exit 1
fi

echo "✅ 預檢查通過"

# ================================
# 顯示測試配置
# ================================

echo ""
echo "📋 測試配置："
echo "   音檔: $AUDIO_FILE"
echo "   大小: $(du -h "$AUDIO_FILE" | cut -f1)"
echo "   會談標題: $SESSION_TITLE"
echo "   API URL: $API_URL"
echo "   輸出檔案: $OUTPUT_FILE"
echo ""

# 詢問是否繼續
read -p "是否繼續執行測試？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消測試"
    exit 0
fi

# ================================
# 執行測試
# ================================

echo "🚀 開始執行LeMUR完整流程測試..."
echo "⏰ 開始時間: $(date)"
echo ""

# 計時開始
START_TIME=$(date +%s)

# 執行Python測試腳本
python3 "$SCRIPT_PATH" \
    --audio-file "$AUDIO_FILE" \
    --auth-token "$AUTH_TOKEN" \
    --session-title "$SESSION_TITLE" \
    --speaker-prompt "$SPEAKER_PROMPT" \
    --punctuation-prompt "$PUNCTUATION_PROMPT" \
    --api-url "$API_URL" \
    --output "$OUTPUT_FILE"

# 檢查執行結果
if [ $? -eq 0 ]; then
    # 計時結束
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "🎉 測試完成成功！"
    echo "⏰ 結束時間: $(date)"
    echo "⏱️  總耗時: ${DURATION} 秒 ($(($DURATION / 60))分 $(($DURATION % 60))秒)"
    echo ""
    
    # 顯示結果檔案信息
    if [ -f "$OUTPUT_FILE" ]; then
        echo "📄 結果已保存到: $OUTPUT_FILE"
        echo "📊 檔案大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
        
        # 顯示簡要結果
        echo ""
        echo "📋 簡要結果："
        python3 -c "
import json
try:
    with open('$OUTPUT_FILE', 'r') as f:
        data = json.load(f)
    print(f\"   會談ID: {data.get('session_id', 'Unknown')}\")
    print(f\"   原始段落數: {data.get('original_segment_count', 0)}\")
    print(f\"   優化段落數: {data.get('optimized_segment_count', 0)}\")
    
    comp = data.get('comparison', {})
    print(f\"   說話者變更: {comp.get('speaker_changes', 0)}\")
    print(f\"   內容變更: {comp.get('content_changes', 0)}\")
    
    speaker_map = data.get('speaker_mapping', {})
    if speaker_map:
        print(f\"   說話者映射: {speaker_map}\")
        
    improvements = data.get('punctuation_improvements', [])
    if improvements:
        print(f\"   改善項目: {', '.join(improvements)}\")
        
except Exception as e:
    print(f\"   無法解析結果檔案: {e}\")
"
        
        echo ""
        echo "💡 查看完整結果："
        echo "   cat $OUTPUT_FILE | jq ."
    fi
    
else
    echo ""
    echo "❌ 測試失敗，請檢查上方錯誤訊息"
    exit 1
fi