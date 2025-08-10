# Terraform 配置比較分析

## 📊 概要比較

我們有兩個不同層級的 Terraform 配置：

1. **`terraform-preview-only/`** - 企業級 GCP Foundation Blueprint
2. **`terraform/gcp/`** - 應用程式專用資源配置

## 🏗️ 架構層級差異

### terraform-preview-only/ (企業級 Foundation)
- **目標**: 建立完整的 GCP 組織架構
- **範圍**: 組織級別、資料夾結構、多專案管理
- **複雜度**: 高 - 企業級最佳實踐
- **管理對象**: IT 基礎設施團隊

### terraform/gcp/ (應用程式級)
- **目標**: 為 Coaching Assistant 應用程式設定必要資源
- **範圍**: 單一專案內的服務和權限
- **複雜度**: 中等 - 應用程式特定需求
- **管理對象**: 開發團隊

## 📋 詳細比較表

| 項目 | terraform-preview-only/ | terraform/gcp/ |
|------|------------------------|----------------|
| **專案管理** | 多個專案 (prod1, prod2, nonprod1, nonprod2) | 單一專案 (coachingassistant) |
| **組織結構** | 資料夾階層 (Production, Non-Production, Development) | 無組織結構 |
| **VPC 網路** | Shared VPC 架構 | 無網路配置 |
| **IAM 管理** | 群組為基礎的權限管理 | 服務帳戶特定權限 |
| **服務範圍** | 基礎設施服務 (Compute, Container) | 應用程式服務 (Speech-to-Text, Storage) |
| **安全性** | 企業級安全政策 | 應用程式級最小權限 |
| **監控** | 集中化日誌和監控專案 | 基本監控 APIs |

## 🔍 具體差異分析

### 1. 專案架構

**terraform-preview-only/**:
```hcl
# 多個服務專案
module "cs-svc-coachly-prod1-svc-6j2w"
module "cs-svc-coachly-prod2-svc-6j2w" 
module "cs-svc-coachly-nonprod1-svc-6j2w"
module "cs-svc-coachly-nonprod2-svc-6j2w"

# VPC 主機專案
module "cs-project-vpc-host-prod"
module "cs-project-vpc-host-nonprod"

# 集中監控專案  
module "cs-project-logging-monitoring"
```

**terraform/gcp/**:
```hcl
# 使用現有專案
data "google_project" "project" {
  project_id = "coachingassistant"  # 單一專案
}
```

### 2. IAM 權限模型

**terraform-preview-only/**:
- 使用 Google Groups: `gcp-developers@doxa.com.tw`
- 資料夾級別權限繼承
- 角色: `compute.instanceAdmin.v1`, `container.admin`

**terraform/gcp/**:
- 服務帳戶直接權限: `coaching-storage@coachingassistant.iam.gserviceaccount.com`
- 專案級別權限
- 角色: `speech.user`, `storage.objectAdmin`, `storage.legacyBucketWriter`

### 3. 資源範圍

**terraform-preview-only/**:
```hcl
# 基礎設施導向
activate_apis = [
  "compute.googleapis.com",
  "monitoring.googleapis.com",
]
```

**terraform/gcp/**:
```hcl
# 應用程式導向
required_apis = [
  "speech.googleapis.com",           # Speech-to-Text API v2
  "storage-api.googleapis.com",      # Cloud Storage API  
  "storage-component.googleapis.com", # Cloud Storage JSON API
]
```

## 🤝 關係和相容性

### ✅ 相容性
- 兩個配置可以**共存**
- `terraform/gcp/` 可以在 `terraform-preview-only/` 建立的基礎上運行
- 沒有資源衝突

### 🔗 整合方式

**選項 1: 獨立運行 (目前狀況)**
- 各自管理不同層級的資源
- 簡單且直接

**選項 2: 整合到 Foundation**
- 將應用程式資源加入到企業級配置中
- 更好的治理和一致性

## 📊 組織 ID 對應

**重要發現**: 兩個配置使用相同的組織 ID:
- `org_id = "682717358496"`
- 這證實了兩者屬於同一個 GCP 組織

## 🎯 建議策略

### 🚀 立即執行 (推薦)
使用 `terraform/gcp/` 解決當前問題：
```bash
# 解決 Speech-to-Text v2 權限問題
cd terraform/gcp
make import-existing
make apply
```

### 📋 長期規劃
1. **評估企業需求**: 是否需要完整的 Foundation 架構
2. **考慮整合**: 將應用程式資源移到適當的企業專案中
3. **漸進遷移**: 逐步採用企業級最佳實踐

## ⚠️ 重要注意事項

### 專案對應關係
- `coachingassistant` (當前使用) ≠ Foundation 中的專案
- Foundation 創建了新的專案 ID: `coachly-prod1-svc-6j2w` 等
- 需要決定使用哪個專案架構

### 權限衝突風險
- Foundation 使用群組權限
- 應用程式使用服務帳戶權限
- 可能需要協調權限模型

## 🔄 行動建議

### 當前緊急修復
```bash
# 使用應用程式級配置解決 Speech-to-Text 問題
cd terraform/gcp
make import-existing && make apply
```

### 後續企業治理
1. 評估是否需要 Foundation 架構
2. 如需要，規劃應用程式遷移到企業專案
3. 統一權限管理模型

## 📝 結論

兩個 Terraform 配置服務於不同目的且可以共存。目前建議：

1. **立即使用** `terraform/gcp/` 解決應用程式問題
2. **長期評估** 是否採用 `terraform-preview-only/` 企業架構
3. **保持靈活性** 可以後續整合或遷移

當前的應用程式級配置完全滿足解決 Speech-to-Text v2 API 權限問題的需求。