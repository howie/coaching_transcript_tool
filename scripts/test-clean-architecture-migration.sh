#!/bin/bash
# Test Clean Architecture Migration Script
# 測試 Clean Architecture 遷移腳本
#
# 使用方式:
# ./scripts/test-clean-architecture-migration.sh [module_name]
#
# 範例:
# ./scripts/test-clean-architecture-migration.sh clients
# ./scripts/test-clean-architecture-migration.sh coaching_sessions

set -e

MODULE_NAME=${1:-"clients"}
BASE_URL="http://localhost:8000"

echo "🚀 開始測試 Clean Architecture 遷移: $MODULE_NAME"
echo "============================================"

# 1. 檢查環境配置
echo "📋 檢查環境配置..."
if ! grep -q "TEST_MODE=true" .env; then
    echo "❌ TEST_MODE 未設置為 true，請檢查 .env 檔案"
    exit 1
fi

if ! grep -q "RECAPTCHA_ENABLED=false" .env; then
    echo "❌ RECAPTCHA_ENABLED 未設置為 false，請檢查 .env 檔案"
    exit 1
fi

echo "✅ 環境配置正確"

# 2. 檢查伺服器是否已運行
echo "🔍 檢查伺服器狀態..."
if curl -s "$BASE_URL/api/health" >/dev/null 2>&1; then
    echo "✅ 伺服器已運行"
    SERVER_RUNNING=true
else
    echo "⚠️  伺服器未運行，正在啟動..."
    SERVER_RUNNING=false

    # 啟動伺服器
    uv run python apps/api-server/main.py &
    SERVER_PID=$!

    # 等待伺服器啟動
    echo "⏳ 等待伺服器啟動..."
    for i in {1..30}; do
        if curl -s "$BASE_URL/api/health" >/dev/null 2>&1; then
            echo "✅ 伺服器已啟動"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ 伺服器啟動超時"
            exit 1
        fi
        sleep 1
    done
fi

# 3. 測試特定模組的端點
echo "🧪 測試 $MODULE_NAME 模組端點..."

case $MODULE_NAME in
    "clients")
        echo "Testing clients module..."

        # 測試靜態端點
        echo "  📊 測試靜態端點..."
        endpoints=(
            "/api/v1/clients/options/sources"
            "/api/v1/clients/options/types"
            "/api/v1/clients/options/statuses"
        )

        for endpoint in "${endpoints[@]}"; do
            response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
            if [ "$response" = "200" ]; then
                echo "    ✅ $endpoint"
            else
                echo "    ❌ $endpoint (HTTP $response)"
            fi
        done

        # 測試動態端點
        echo "  🔄 測試動態端點..."

        # GET /api/v1/clients
        response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/clients")
        if [ "$response" = "200" ]; then
            echo "    ✅ GET /api/v1/clients"
        else
            echo "    ❌ GET /api/v1/clients (HTTP $response)"
        fi

        # POST /api/v1/clients
        response=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "$BASE_URL/api/v1/clients" \
            -H "Content-Type: application/json" \
            -d '{
                "name": "Migration Test Client",
                "email": "migration-test@example.com",
                "source": "referral",
                "client_type": "paid",
                "status": "first_session"
            }')

        if [ "$response" = "200" ] || [ "$response" = "201" ]; then
            echo "    ✅ POST /api/v1/clients"
        else
            echo "    ❌ POST /api/v1/clients (HTTP $response)"
        fi
        ;;

    "coaching_sessions")
        echo "Testing coaching sessions module..."
        # TODO: 添加 coaching sessions 測試
        echo "    ⚠️  Coaching sessions 測試尚未實作"
        ;;

    "transcript_smoothing")
        echo "Testing transcript smoothing module..."
        # TODO: 添加 transcript smoothing 測試
        echo "    ⚠️  Transcript smoothing 測試尚未實作"
        ;;

    *)
        echo "    ⚠️  未知模組: $MODULE_NAME"
        echo "    支援的模組: clients, coaching_sessions, transcript_smoothing"
        ;;
esac

# 4. 測試 TEST_MODE 功能
echo "🔐 驗證 TEST_MODE 功能..."
test_response=$(curl -s "$BASE_URL/api/v1/auth/me")
if echo "$test_response" | grep -q "test@example.com"; then
    echo "✅ TEST_MODE 正常工作，使用測試用戶"
else
    echo "❌ TEST_MODE 可能未正常工作"
fi

# 5. 清理
if [ "$SERVER_RUNNING" = false ] && [ -n "$SERVER_PID" ]; then
    echo "🧹 清理資源..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
fi

echo "============================================"
echo "🎉 Clean Architecture 遷移測試完成: $MODULE_NAME"
echo ""
echo "📋 下一步:"
echo "1. 檢查伺服器日誌確認沒有錯誤"
echo "2. 驗證資料庫操作正確執行"
echo "3. 測試錯誤處理情況"
echo "4. 執行完整的單元測試套件"
echo ""
echo "📖 詳細指南: docs/features/test-improvement/api-testing-guide.md"