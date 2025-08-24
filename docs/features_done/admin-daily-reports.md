# Admin Daily Reports Agent 📊

自動化管理後台日報系統，每天從 production 資料庫撈取數據生成綜合報表。

## 功能特色 ✨

### 🎯 核心功能
- **每日自動報表**: 每天 8:00 AM UTC 自動生成前一日報表
- **週報摘要**: 每週一 9:00 AM UTC 生成週報
- **即時 API 查詢**: 管理員可隨時查詢報表數據
- **郵件自動發送**: HTML 格式郵件 + JSON 附件
- **多層級權限控制**: STAFF (唯讀) / ADMIN (操作) / SUPER_ADMIN (配置)

### 📈 報表內容
- **用戶指標**: 總用戶數、新增用戶、活躍用戶
- **使用狀況**: Session 數量、成功率、錯誤率
- **計費數據**: 處理分鐘數、成本統計、方案分佈
- **系統健康**: 處理時間、錯誤分析
- **管理活動**: 管理員登錄、權限狀態
- **熱門用戶**: 最活躍用戶排行

## 技術架構 🏗️

### 主要組件
```
src/coaching_assistant/
├── core/services/admin_daily_report.py    # 報表生成服務
├── tasks/admin_report_tasks.py            # Celery 異步任務
├── api/admin_reports.py                   # REST API 端點
├── config/celery_schedule.py              # 排程配置
└── scripts/admin_report_setup.py          # 安裝測試工具
```

### 數據源
- **User 模型**: 用戶註冊、方案、使用量
- **Session 模型**: 轉錄會話、狀態、提供商
- **UsageAnalytics 模型**: 月度聚合數據
- **BillingAnalytics 模型**: 計費分析
- **ECPay 訂閱**: 付費方案狀態

## 快速開始 🚀

### 1. 環境配置
```bash
# 必需的環境變數
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"

# 可選配置
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="reports@yourcompany.com"
export ADMIN_REPORT_EMAILS="admin1@company.com,admin2@company.com"
```

### 2. 運行測試工具
```bash
# 檢查所有配置
python scripts/admin_report_setup.py --all

# 查看詳細使用說明
python scripts/admin_report_setup.py --usage
```

### 3. 啟動 Celery 服務
```bash
# 啟動 Worker (處理報表任務)
celery -A coaching_assistant.config.celery worker \
  --queues=admin_reports \
  --concurrency=2 \
  --loglevel=info

# 啟動 Beat Scheduler (定時任務)
celery -A coaching_assistant.config.celery beat \
  --scheduler=celery.beat:PersistentScheduler \
  --loglevel=info
```

## API 端點 🔌

### 查詢報表 (STAFF+)
```http
GET /admin/reports/daily?target_date=2024-01-15
```

### 發送日報 (ADMIN+)
```http
POST /admin/reports/daily/send
Content-Type: application/json

{
  "target_date": "2024-01-15",
  "recipient_emails": ["admin@company.com"],
  "send_email": true
}
```

### 發送週報 (ADMIN+)
```http
POST /admin/reports/weekly/send?week_start_date=2024-01-15
```

### 任務狀態查詢 (STAFF+)
```http
GET /admin/reports/task-status/{task_id}
```

### 管理員列表 (ADMIN+)
```http
GET /admin/reports/users/admin-list
```

### 郵件配置檢查 (ADMIN+)
```http
GET /admin/reports/config/email-settings
```

### 測試郵件 (SUPER_ADMIN)
```http
POST /admin/reports/test-email?recipient_email=test@company.com
```

## 排程配置 ⏰

### 自動排程
- **日報**: 每天 8:00 AM UTC
- **週報**: 每週一 9:00 AM UTC  
- **健康檢查**: 每 6 小時 (可選，預設關閉)

### 自訂排程
修改 `src/coaching_assistant/config/celery_schedule.py`:

```python
CELERYBEAT_SCHEDULE = {
    'daily-admin-report': {
        'task': 'coaching_assistant.tasks.admin_report_tasks.generate_and_send_daily_report',
        'schedule': crontab(hour=8, minute=0),  # 自訂時間
    }
}
```

## 報表範例 📋

### 每日報表內容
```
📊 Daily Admin Report - 2024-01-15

Key Metrics:
- 總用戶數: 1,234
- 新增用戶: 12 (+1.0%)
- 活躍用戶: 89
- 總 Sessions: 156
- 成功率: 94.2%
- 處理時間: 127.3 分鐘
- 總成本: $12.34

新用戶列表:
- user1@example.com (PRO, Google, 14:32)
- user2@example.com (FREE, Email, 16:45)

方案分佈:
- FREE: 892 (72.3%)
- PRO: 298 (24.1%) 
- ENTERPRISE: 44 (3.6%)

熱門用戶:
1. active@user.com - 15 sessions, 98.5 minutes
2. power@user.com - 12 sessions, 76.2 minutes
```

### JSON 數據結構
```json
{
  "report_date": "2024-01-15",
  "total_users": 1234,
  "new_users_count": 12,
  "active_users_count": 89,
  "total_sessions": 156,
  "completed_sessions": 147,
  "error_rate": 5.8,
  "total_minutes_processed": 127.3,
  "total_cost_usd": 12.3456,
  "users_by_plan": {
    "free": 892,
    "pro": 298,
    "enterprise": 44
  },
  "sessions_by_provider": {
    "google": 134,
    "assemblyai": 22
  },
  "new_users": [...],
  "top_users": [...],
  "admin_users": [...]
}
```

## 安全考量 🔒

### 權限控制
- **STAFF**: 只能查看報表數據
- **ADMIN**: 可以觸發報表生成和發送
- **SUPER_ADMIN**: 可以測試郵件配置

### 數據保護
- 敏感資訊 (密碼、金鑰) 不會出現在報表中
- 用戶郵件地址僅顯示管理員身份用戶
- IP 地址和詳細錯誤訊息僅限內部使用

### 速率限制
- 日報生成: 最多 10/分鐘
- 週報生成: 最多 2/小時
- API 查詢: 遵循一般 API 限制

## 故障排除 🔧

### 常見問題

**1. 郵件發送失敗**
```bash
# 檢查 SMTP 配置
python scripts/admin_report_setup.py --test-email

# 確認環境變數
echo $SMTP_USER
echo $SMTP_SERVER
```

**2. 資料庫連接錯誤**
```bash
# 測試資料庫連接
python scripts/admin_report_setup.py --test-db

# 檢查 DATABASE_URL
echo $DATABASE_URL
```

**3. Celery 任務失敗**
```bash
# 查看 Celery 日誌
celery -A coaching_assistant.config.celery events

# 檢查任務狀態
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/admin/reports/task-status/$TASK_ID
```

### 日誌位置
- **應用日誌**: `logs/admin_reports.log`
- **Celery 日誌**: stdout (或配置的日誌文件)
- **臨時報表**: `/tmp/daily_report_*.json`

## 監控與告警 📈

### 內建監控
- 任務執行狀態自動記錄
- 失敗時自動發送告警郵件
- 重試機制和指數退避

### 建議的外部監控
- **Celery Flower**: Web UI 監控 Celery 任務
- **健康檢查端點**: `/admin/reports/config/email-settings`
- **日誌監控**: 監控錯誤日誌中的 "admin_report" 關鍵字

## 未來增強 🚀

### 計畫功能
- [ ] 圖表和視覺化報表
- [ ] 自定義報表模板
- [ ] 更多匯出格式 (PDF, Excel)
- [ ] Slack/Teams 通知整合
- [ ] 多語言報表支援
- [ ] 歷史報表比較分析

### 效能優化
- [ ] 報表數據快取機制
- [ ] 分頁查詢大數據集
- [ ] 非同步報表生成進度條

---

**建立日期**: 2024-01-24  
**版本**: 1.0.0  
**維護者**: Admin Team