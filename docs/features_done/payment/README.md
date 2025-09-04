# ECPay SaaS Subscription System

## 🎯 Overview

基於深度思考的 SaaS 商業模式，本系統專注於 **ECPay 信用卡定期定額** 服務，實現穩定的月經常性收入 (MRR)。

## 📋 Strategic Focus

### ✅ SaaS 訂閱模式 (保留)
- **信用卡定期定額**: 用戶一次授權，系統自動扣款
- **Monthly Recurring Revenue**: 穩定的月經常性收入
- **自動續費**: 無需用戶手動付款
- **訂閱管理**: 升級、降級、暫停、取消
- **台灣市場優化**: TWD 定價，繁體中文界面

### ❌ 非訂閱付款 (已移除)
- ~~ATM 轉帳~~: 無法支援自動續費
- ~~便利商店付款~~: 需要手動操作
- ~~一次性付款~~: 不符合 SaaS 模式

## 🏗️ System Architecture

### Core Components
```
ECPay 定期定額授權 → 自動扣款 → 訂閱延長 → 用戶通知
     ↓
   訂閱管理 → 方案升級/降級 → 按比例計費
     ↓
   失敗處理 → 重試機制 → 寬限期 → 自動降級
```

### Technical Stack
- **Payment Provider**: ECPay 定期定額 (信用卡)
- **Supported Cards**: Visa, Mastercard, JCB
- **Currency**: TWD (新台幣)
- **Billing Cycles**: Monthly, Annual
- **Database**: PostgreSQL (subscription management)

## 📊 Taiwan Market Pricing

### Subscription Plans
```
FREE 方案: NT$0/月
├── 60MB 檔案限制
├── 3個會談記錄
└── 基本轉錄功能

PRO 方案: NT$899/月 (最受歡迎)
├── 200MB 檔案限制
├── 無限會談記錄
├── 角色識別功能
└── 專業分析報告

ENTERPRISE 方案: NT$2,999/月
├── 500MB 檔案限制
├── 團隊管理功能
├── API 整合
└── 專屬客戶經理
```

### Annual Savings
- **年繳優惠**: 所有付費方案省 2 個月 (相當於 83 折)
- **PRO 年繳**: NT$8,999 (平均每月 NT$750)
- **ENTERPRISE 年繳**: NT$29,999 (平均每月 NT$2,500)

## 📁 Documentation Structure

### Core Documents
- **`ecpay-saas-subscription.md`** - SaaS 訂閱系統完整架構
- **`stripe-secondary.md`** - Stripe 作為未來國際市場備選方案

### User Stories (Implementation Guide)
```
user-stories/
├── README-subscription.md              # SaaS 訂閱概覽
├── US-SUB-001-credit-authorization.md  # 信用卡授權 (Week 1)
├── US-SUB-002-subscription-management.md # 訂閱管理 (Week 1-2)
├── US-SUB-003-automatic-billing.md     # 自動扣款 (Week 2)
└── US-SUB-004-plan-upgrades.md        # 方案升級定價 (Week 2)
```

## 🚀 Implementation Timeline

### Week 1: Foundation
- **US-SUB-001**: ECPay 信用卡定期定額授權
- **US-SUB-002**: 基礎訂閱管理功能

### Week 2: Automation & Enhancement  
- **US-SUB-002**: 完整訂閱管理 (升級/降級/取消)
- **US-SUB-003**: 自動扣款與失敗處理
- **US-SUB-004**: 台灣定價顯示與升級引導

## 🎯 Success Metrics

### Business KPIs
- **MRR Growth**: 月經常性收入成長 >20%
- **Conversion Rate**: 免費轉付費 >15%
- **Churn Rate**: 月流失率 <5%
- **ARPU**: 每用戶平均收入 >NT$800

### Technical KPIs
- **Payment Success**: 扣款成功率 >98%
- **Authorization Success**: 信用卡授權成功率 >95%
- **API Response Time**: 訂閱管理 <500ms
- **System Uptime**: >99.9%

## 🔧 Key Features

### 1. 信用卡定期定額授權
- ECPay 整合的自動扣款授權
- 支援月繳和年繳週期
- 安全的 PCI 合規處理

### 2. 智能訂閱管理
- 即時升級 + 按比例計費
- 期末降級避免用戶損失
- 靈活的取消和重新啟用

### 3. 自動扣款系統
- ECPay Webhook 自動處理
- 3次重試 + 7天寬限期
- 自動降級到免費方案

### 4. 台灣市場優化
- 新台幣定價策略
- 繁體中文完整界面
- 符合台灣付費習慣

## 🛡️ Security & Compliance

### Payment Security
- PCI DSS 合規信用卡處理
- ECPay CheckMacValue 驗證
- 敏感資料加密存儲

### Data Protection
- 符合台灣個資法
- 信用卡資訊遮罩顯示
- 安全的 Webhook 端點

## 📞 Support & Maintenance

### Customer Support
- 繁體中文客服支援
- 訂閱管理自助服務
- 付款問題快速處理

### Technical Maintenance
- 自動化扣款監控
- 失敗付款警報
- 系統健康度檢查

## 🚨 Current Status (2025-08-20)

### ✅ Completed Components
- Frontend subscription management UI
- Backend API endpoints (`/api/v1/subscriptions/*`, `/api/v1/plans`)
- Database schema and data models
- Security compliance framework

### 🔴 Critical Issue
**ECPay CheckMacValue Error (10200073)** - 需要聯繫 ECPay 技術支援
- 所有定期定額授權請求都失敗
- 已修正所有已知參數問題
- 可能是測試商店設定問題

### 📋 Immediate Actions Required
1. **聯繫 ECPay 技術支援** - 驗證測試商店 3002607 狀態
2. **獲取詳細錯誤診斷** - 請求具體失敗原因
3. **準備替代方案** - 考慮新測試商店或臨時支付方案

詳細狀態請參考：`status-update-2025-08-20.md`

---

## 🔗 Related Documentation

- **Current Status**: `status-update-2025-08-20.md` - 最新進度和問題追蹤
- **Technical Architecture**: `ecpay-saas-subscription.md`
- **Troubleshooting**: `ecpay-troubleshooting-guide.md` - 包含 CheckMacValue 問題診斷
- **Testing Guide**: `testing-guide.md` - 測試工具和腳本使用指南
- **Implementation Guide**: `user-stories/README-subscription.md`
- **Future Expansion**: `stripe-secondary.md` (國際市場)
- **Admin Token Guide**: `webhook-admin-token-guide.md` - 管理員令牌使用指南 🆕
- **Webhook Processing**: `webhook-processing-summary.md` - 增強 Webhook 處理實作總結 🆕

## 🧪 Testing Resources

### Test Files
- **Integration Test**: `@tests/integration/test_ecpay_basic.py` - ECPay 基本連線和檢驗工具
- **Testing Guide**: `testing-guide.md` - 完整測試流程和故障排除

### Quick Test Commands
```bash
# 執行 ECPay 基本連線測試
cd tests/integration
python test_ecpay_basic.py
```

詳細測試說明請參考：`testing-guide.md`