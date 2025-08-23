#!/bin/bash
#
# 資料庫處理測試範例腳本
# 
# 用途：測試對已存在逐字稿的LeMUR優化處理
# 
# 使用方法：
#   1. 設定環境變量
#   2. 執行腳本查看可用會談
#   3. 選擇會談ID進行測試
#

set -e  # 遇到錯誤立即退出

# ================================
# 設定區域 - 請修改以下參數  
# ================================

# API認證Token (必需)
AUTH_TOKEN="${AUTH_TOKEN:-your_token_here}"

# API URL (可選)
API_URL="${API_URL:-http://localhost:8000}"

# 會談ID (將由腳本協助選擇)
SESSION_ID="${SESSION_ID:-}"

# 自訂提示詞 (可選)
SPEAKER_PROMPT="請根據對話內容判斷誰是教練（通常會提問、引導、給予建議）、誰是客戶（通常會分享、回答、描述困擾）。請將說話者標記為「教練」或「客戶」。"

PUNCTUATION_PROMPT="請添加適當的標點符號來改善這段教練對話的可讀性：1) 在句子和片語間加上適當標點 2) 改善語氣詞的標點使用 3) 保持原始說話風格和語調 4) 確保對話易於閱讀理解。"

# 處理選項
SKIP_SPEAKER="${SKIP_SPEAKER:-false}"
SKIP_PUNCTUATION="${SKIP_PUNCTUATION:-false}"

# 結果輸出檔案
OUTPUT_FILE="results_database_$(date +%Y%m%d_%H%M%S).json"

# ================================
# 函數定義
# ================================

# 顯示使用說明
show_usage() {
    echo "用法："
    echo "  $0                    # 互動式選擇會談"
    echo "  $0 <session-id>      # 直接處理指定會談"
    echo ""
    echo "環境變量："
    echo "  AUTH_TOKEN           # API認證token (必需)"
    echo "  SESSION_ID           # 要處理的會談ID" 
    echo "  API_URL              # API URL (預設: http://localhost:8000)"
    echo "  SKIP_SPEAKER=true    # 跳過說話者識別"
    echo "  SKIP_PUNCTUATION=true # 跳過標點符號優化"
    echo ""
    echo "範例："
    echo "  export AUTH_TOKEN=\"your_token\""
    echo "  $0 e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9"
    echo "  SKIP_SPEAKER=true $0 <session-id>"
}

# 檢查依賴
check_dependencies() {
    echo "🔍 檢查依賴..."
    
    # 檢查Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ 錯誤：未找到python3"
        exit 1
    fi
    
    # 檢查測試腳本
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "❌ 錯誤：測試腳本不存在: $SCRIPT_PATH"
        exit 1
    fi
    
    echo "✅ 依賴檢查通過"
}

# 列出可用會談
list_sessions() {
    echo "📋 查詢可用會談..."
    
    python3 "$SCRIPT_PATH" \
        --list-sessions \
        --auth-token "$AUTH_TOKEN" \
        --api-url "$API_URL"
}

# 讀取用戶輸入的會談ID
read_session_id() {
    echo ""
    read -p "請輸入要處理的會談ID: " SESSION_ID
    
    if [ -z "$SESSION_ID" ]; then
        echo "❌ 未輸入會談ID，退出"
        exit 1
    fi
    
    echo "✅ 選擇會談: $SESSION_ID"
}

# 確認處理選項
confirm_options() {
    echo ""
    echo "📋 處理選項："
    
    if [ "$SKIP_SPEAKER" = "true" ]; then
        echo "   ⏭️  跳過說話者識別"
    else
        echo "   🎭 執行說話者識別"
    fi
    
    if [ "$SKIP_PUNCTUATION" = "true" ]; then
        echo "   ⏭️  跳過標點符號優化"
    else
        echo "   🔤 執行標點符號優化"
    fi
    
    echo "   📄 輸出檔案: $OUTPUT_FILE"
    echo ""
    
    read -p "是否繼續處理？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消處理"
        exit 0
    fi
}

# 執行資料庫處理測試
run_database_test() {
    echo "🚀 開始執行LeMUR資料庫處理測試..."
    echo "⏰ 開始時間: $(date)"
    echo ""
    
    # 計時開始
    START_TIME=$(date +%s)
    
    # 構建參數
    ARGS=(
        --session-id "$SESSION_ID"
        --auth-token "$AUTH_TOKEN" 
        --api-url "$API_URL"
        --output "$OUTPUT_FILE"
    )
    
    # 添加自訂提示詞
    if [ "$SKIP_SPEAKER" != "true" ]; then
        ARGS+=(--speaker-prompt "$SPEAKER_PROMPT")
    fi
    
    if [ "$SKIP_PUNCTUATION" != "true" ]; then
        ARGS+=(--punctuation-prompt "$PUNCTUATION_PROMPT")
    fi
    
    # 添加跳過選項
    if [ "$SKIP_SPEAKER" = "true" ]; then
        ARGS+=(--skip-speaker)
    fi
    
    if [ "$SKIP_PUNCTUATION" = "true" ]; then
        ARGS+=(--skip-punctuation)
    fi
    
    # 執行測試
    python3 "$SCRIPT_PATH" "${ARGS[@]}"
    
    # 檢查結果
    if [ $? -eq 0 ]; then
        show_results
    else
        echo ""
        echo "❌ 測試失敗，請檢查上方錯誤訊息"
        exit 1
    fi
}

# 顯示測試結果
show_results() {
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "🎉 資料庫處理測試完成！"
    echo "⏰ 結束時間: $(date)"
    echo "⏱️  總耗時: ${DURATION} 秒"
    echo ""
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo "📄 結果已保存到: $OUTPUT_FILE"
        echo "📊 檔案大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
        
        # 顯示結果摘要
        echo ""
        echo "📋 結果摘要："
        python3 -c "
import json
try:
    with open('$OUTPUT_FILE', 'r') as f:
        data = json.load(f)
    
    session_details = data.get('session_details', {})
    analysis = data.get('overall_analysis', {})
    speaker_result = data.get('speaker_identification_result', {})
    punct_result = data.get('punctuation_optimization_result', {})
    
    print(f\"   會談: {session_details.get('title', 'Unknown')}\")
    print(f\"   總段落數: {analysis.get('total_segments', 0)}\")
    print(f\"   說話者變更: {analysis.get('speaker_changes', 0)}\")
    print(f\"   內容變更: {analysis.get('content_changes', 0)}\")
    print(f\"   未變更段落: {analysis.get('identical_segments', 0)}\")
    
    if speaker_result:
        speaker_updates = speaker_result.get('segment_updates', 0)
        speaker_mapping = speaker_result.get('speaker_mapping', {})
        print(f\"   說話者資料庫更新: {speaker_updates}\")
        if speaker_mapping:
            print(f\"   說話者映射: {speaker_mapping}\")
    
    if punct_result:
        punct_updates = punct_result.get('segment_updates', 0)
        improvements = punct_result.get('improvements_made', [])
        print(f\"   標點符號資料庫更新: {punct_updates}\")
        if improvements:
            print(f\"   改善項目: {', '.join(improvements)}\")
            
except Exception as e:
    print(f\"   無法解析結果檔案: {e}\")
"
        
        echo ""
        echo "💡 查看詳細結果："
        echo "   cat $OUTPUT_FILE | jq ."
        echo ""
        echo "💡 查看變更範例："
        echo "   cat $OUTPUT_FILE | jq '.overall_analysis.speaker_change_details'"
        echo "   cat $OUTPUT_FILE | jq '.overall_analysis.content_change_details'"
    fi
}

# ================================
# 主流程
# ================================

# 腳本路徑
SCRIPT_PATH="../test_lemur_database_processing.py"

# 處理命令行參數
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

# 如果提供了會談ID作為參數
if [ -n "$1" ]; then
    SESSION_ID="$1"
fi

# 檢查認證Token
if [ "$AUTH_TOKEN" = "your_token_here" ] || [ -z "$AUTH_TOKEN" ]; then
    echo "❌ 錯誤：請設定正確的AUTH_TOKEN"
    echo "   export AUTH_TOKEN=\"your_actual_token\""
    echo ""
    show_usage
    exit 1
fi

# 檢查依賴
check_dependencies

# 如果沒有提供會談ID，則查詢並選擇
if [ -z "$SESSION_ID" ]; then
    list_sessions
    read_session_id
fi

# 確認處理選項
confirm_options

# 執行測試
run_database_test