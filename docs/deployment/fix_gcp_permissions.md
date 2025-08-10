# 修復 Google Cloud Speech-to-Text v2 權限

## 問題
```
403 Permission 'speech.recognizers.recognize' denied on resource
```

## 解決方案

### 方法 1: 使用 Google Cloud Console

1. **前往 IAM 頁面**:
   - 開啟 [Google Cloud Console](https://console.cloud.google.com)
   - 選擇專案: `coachingassistant` 
   - 前往 "IAM & Admin" > "IAM"

2. **找到服務帳戶**:
   - 尋找: `coaching-storage@coachingassistant.iam.gserviceaccount.com`

3. **編輯權限**:
   - 點選該服務帳戶旁的編輯按鈕 ✏️
   - 添加以下角色之一:
     - **推薦**: `Cloud Speech-to-Text User` (roles/speech.user)
     - **或**: `Cloud Speech-to-Text Admin` (roles/speech.admin)

### 方法 2: 使用 gcloud 命令

```bash
# 設定專案
gcloud config set project coachingassistant

# 添加 Speech-to-Text User 權限 (推薦)
gcloud projects add-iam-policy-binding coachingassistant \
    --member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
    --role="roles/speech.user"

# 或者添加 Admin 權限 (如果需要更多功能)
gcloud projects add-iam-policy-binding coachingassistant \
    --member="serviceAccount:coaching-storage@coachingassistant.iam.gserviceaccount.com" \
    --role="roles/speech.admin"
```

### 方法 3: 檢查現有權限

```bash
# 檢查服務帳戶目前權限
gcloud projects get-iam-policy coachingassistant \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:coaching-storage@coachingassistant.iam.gserviceaccount.com"
```

## 需要的具體權限

Speech-to-Text v2 API 需要以下權限:
- `speech.recognizers.recognize` - 執行語音識別
- `speech.recognizers.get` - 取得識別器資訊  
- `speech.recognizers.list` - 列出識別器

這些權限包含在以下角色中:
- ✅ **roles/speech.user** (推薦)
- ✅ **roles/speech.admin** (如果需要管理功能)

## 驗證權限修復

修復權限後，重啟 Celery worker 並測試:

```bash
# 停止 Celery
Ctrl+C

# 重新啟動
make run-celery-debug
```

## 常見問題

**Q: 為什麼之前沒有這個權限問題？**
A: Speech-to-Text v2 API 使用不同的權限模型，需要 `speech.recognizers.recognize` 而不是 v1 的權限。

**Q: 我已經有 Storage 權限了？**
A: Google Cloud Storage 和 Speech-to-Text 是不同的服務，需要分別的權限。

**Q: 權限修改多久生效？**  
A: 通常立即生效，但可能需要等待 1-2 分鐘讓權限傳播。

## 安全建議

- 使用 `roles/speech.user` 而非 `roles/speech.admin`（最小權限原則）
- 定期檢查服務帳戶權限
- 考慮使用自訂角色來進一步限制權限