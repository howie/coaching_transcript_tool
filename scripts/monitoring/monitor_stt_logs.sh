#\!/bin/bash

echo "🔍 Monitoring Google STT API calls..."
echo "=================================="
echo ""

# 監控 API 日誌中的 STT 相關訊息
echo "📝 Recent STT-related logs from API:"
echo "-----------------------------------"

# 如果 API 正在運行，可以查看其輸出
if pgrep -f "coaching_assistant.main:app" > /dev/null; then
    echo "✅ API is running"
    echo "Check the API terminal for these log messages:"
    echo "  - 'Starting transcription for session'"
    echo "  - 'Sending audio to STT provider'"
    echo "  - 'Google STT client initialized'"
    echo "  - 'Transcription completed'"
else
    echo "⚠️  API is not running. Start it with: make run-api"
fi

echo ""
echo "📊 Google Cloud STT API Usage:"
echo "------------------------------"
echo "Run this command with your personal account:"
echo ""
echo "gcloud config set account your-email@gmail.com"
echo "gcloud logging read 'protoPayload.serviceName=\"speech.googleapis.com\"' \\"
echo "  --format=\"table(timestamp,protoPayload.methodName,protoPayload.resourceName)\" \\"
echo "  --limit=10"

echo ""
echo "🔍 Check specific session transcription:"
echo "----------------------------------------"
echo "Replace SESSION_ID with actual session ID:"
echo ""
echo "# Check in database"
echo "psql \$DATABASE_URL -c \"SELECT * FROM session WHERE id = 'SESSION_ID';\""
echo ""
echo "# Check Celery task"
echo "celery -A coaching_assistant.core.celery_app inspect active | grep SESSION_ID"
