# ECPay SaaS Subscription Model - User Stories

## 🎯 Strategic Focus: Credit Card Subscription Only

基於 **深度思考** 的 SaaS 商業模式需求，我們專注於 **ECPay 信用卡定期定額** 服務，確保：
- **Monthly Recurring Revenue (MRR)**: 穩定的月經常性收入
- **Automatic Renewal**: 用戶一次授權，系統自動續費
- **Cash Flow Optimization**: 預付費模式改善現金流
- **Plan Flexibility**: 支援升級、降級、暫停等訂閱管理

## 📋 SaaS Subscription User Stories

### Core Subscription Flow (Week 1-2)

#### US-SUB-001: ECPay Credit Card Authorization
**Goal**: 建立信用卡定期定額授權  
**Priority**: P0 (Critical)  
**Points**: 13  
**Timeline**: Week 1 (Days 1-5)

**Key Features**:
- ECPay 定期定額 API 整合
- 信用卡授權流程
- 授權成功後立即創建訂閱
- 支援月繳/年繳週期
- 傳統中文界面

#### US-SUB-002: Subscription Management  
**Goal**: 完整的訂閱管理功能  
**Priority**: P0 (Critical)  
**Points**: 10  
**Timeline**: Week 1-2 (Days 6-10)

**Key Features**:
- 查看當前訂閱狀態
- 升級方案（立即生效 + 按比例計費）
- 降級方案（期末生效）
- 取消訂閱（立即或期末）
- 重新啟用訂閱
- 付款方式管理

#### US-SUB-003: Automatic Billing
**Goal**: 自動扣款和計費管理  
**Priority**: P0 (Critical)  
**Points**: 8  
**Timeline**: Week 2 (Days 6-8)

**Key Features**:
- ECPay 定期扣款 Webhook 處理
- 扣款失敗重試機制
- 過期訂閱處理
- 自動降級到免費方案
- 扣款通知系統

#### US-SUB-004: Plan Upgrades & Pricing
**Goal**: 方案升級和台灣定價顯示  
**Priority**: P1 (High)  
**Points**: 5  
**Timeline**: Week 2 (Days 9-10)

**Key Features**:
- 台灣市場優化定價
- 年繳優惠顯示
- 方案比較表
- 升級路徑引導
- 傳統中文定價顯示

## 🏗️ Technical Architecture

### ECPay 定期定額整合
```
User Authorization Flow:
用戶選擇方案 → ECPay授權表單 → 授權成功 → 創建訂閱 → 升級方案

Automatic Billing Flow:
ECPay定期扣款 → Webhook通知 → 延長訂閱期 → 用戶通知
```

### Database Schema
- `ecpay_credit_authorizations` - 信用卡授權記錄
- `saas_subscriptions` - SaaS 訂閱管理
- `subscription_payments` - 定期扣款記錄
- `subscription_pending_changes` - 待生效的方案變更

### API Endpoints
- `POST /api/v1/subscriptions/authorize` - 建立信用卡授權
- `GET /api/v1/subscriptions/current` - 取得當前訂閱
- `POST /api/v1/subscriptions/upgrade` - 升級方案
- `POST /api/v1/subscriptions/cancel` - 取消訂閱
- `POST /api/webhooks/ecpay-billing` - 自動扣款回調

## 📊 Story Dependencies & Timeline

### Week 1: Foundation (Days 1-5)
```
US-SUB-001: ECPay Credit Authorization
├── ECPay 定期定額 API 整合
├── 信用卡授權流程
├── 授權成功處理
└── 訂閱創建邏輯
```

### Week 1-2: Management (Days 6-10)
```
US-SUB-002: Subscription Management
├── 依賴: US-SUB-001 (授權基礎)
├── 訂閱查看和狀態管理
├── 方案升級/降級邏輯
├── 取消和重新啟用
└── 按比例計費處理
```

### Week 2: Automation (Days 6-8)
```
US-SUB-003: Automatic Billing
├── 依賴: US-SUB-001 (授權基礎)
├── ECPay Webhook 處理
├── 自動扣款邏輯
├── 失敗重試機制
└── 訂閱到期處理
```

### Week 2: Enhancement (Days 9-10)
```
US-SUB-004: Plan Upgrades & Pricing
├── 依賴: US-SUB-001, US-SUB-002
├── 台灣定價策略
├── 方案比較界面
├── 升級引導流程
└── 年繳優惠顯示
```

## 🎯 Success Metrics

### Business KPIs
- **MRR Growth**: 月經常性收入成長 >20%
- **Subscription Conversion**: 免費到付費轉換率 >15%
- **Churn Rate**: 月流失率 <5%
- **ARPU**: 每用戶平均收入 >NT$800
- **Payment Success Rate**: 扣款成功率 >98%

### Technical KPIs
- **Authorization Success**: 信用卡授權成功率 >95%
- **Webhook Processing**: 自動扣款處理時間 <30秒
- **API Response Time**: 訂閱管理 API <500ms
- **System Uptime**: 服務可用性 >99.9%

## 🚫 Removed Features (Non-SaaS)

### 已移除的付款方式
- ❌ **ATM 轉帳**: 無法支援自動續費
- ❌ **便利商店付款**: 需要手動付款，不適合 SaaS
- ❌ **一次性付款**: 不符合訂閱模式

### 移除原因
1. **SaaS 核心需求**: 需要自動續費確保 MRR
2. **用戶體驗**: 自動扣款避免服務中斷
3. **現金流管理**: 預付費模式優化財務
4. **運營效率**: 減少手動付款處理成本

## 📁 File Structure

```
user-stories/
├── README-subscription.md                 # 本文件 (SaaS 概覽)
├── US-SUB-001-credit-authorization.md     # 信用卡授權
├── US-SUB-002-subscription-management.md  # 訂閱管理
├── US-SUB-003-automatic-billing.md        # 自動扣款
└── US-SUB-004-plan-upgrades.md           # 方案升級和定價

# 已移除的檔案
├── ❌ US-ECPay-003-atm-transfer.md
├── ❌ US-ECPay-004-convenience-store.md
└── ❌ 其他非訂閱相關的 user stories
```

## 🎯 Taiwan Market Focus

### 定價策略
- **PRO 方案**: NT$899/月 (專業教練)
- **ENTERPRISE 方案**: NT$2,999/月 (教練機構)
- **年繳優惠**: 省 2 個月 (相當於 83 折)

### 在地化特色
- **繁體中文**: 完整的傳統中文界面
- **台灣信用卡**: 支援 Visa、Mastercard、JCB
- **本土習慣**: 符合台灣用戶付費習慣
- **客服支援**: 中文客服和技術支援

---

**下一步行動**: 開始實作 US-SUB-001 (ECPay Credit Card Authorization) 作為 SaaS 訂閱的基礎功能。