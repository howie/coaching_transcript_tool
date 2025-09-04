#!/usr/bin/env python3
"""
為 howie.yu@gmail.com 創建訂閱數據
"""

import os
import sys
from datetime import datetime, date, timedelta
from uuid import uuid4

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from coaching_assistant.core.database import get_db
from coaching_assistant.models import (
    User, 
    SaasSubscription, 
    ECPayCreditAuthorization,
    SubscriptionStatus,
    ECPayAuthStatus,
    SubscriptionPayment,
    PaymentStatus
)
from coaching_assistant.models.user import UserPlan

def setup_howie_subscription():
    """為 howie.yu@gmail.com 設定訂閱"""
    
    db = next(get_db())
    
    try:
        # 找到 howie 的帳號
        user = db.query(User).filter(User.email == "howie.yu@gmail.com").first()
        
        if not user:
            print("❌ 沒有找到 howie.yu@gmail.com 用戶")
            return
            
        print(f"✅ 找到用戶: {user.email} (ID: {user.id})")
        
        # 檢查是否已有訂閱
        existing_subscription = db.query(SaasSubscription).filter(
            SaasSubscription.user_id == user.id
        ).first()
        
        if existing_subscription:
            print(f"⚠️  用戶已有訂閱: {existing_subscription.plan_id} ({existing_subscription.status})")
            return
        
        # 創建 ECPay 信用卡授權記錄
        print("💳 創建信用卡授權記錄...")
        auth_record = ECPayCreditAuthorization(
            user_id=user.id,
            merchant_member_id=f"USER{str(user.id).replace('-', '')[:8].upper()}{int(datetime.now().timestamp())}",
            gwsr=f"ecpay_{uuid4().hex[:10]}",
            auth_code=f"AUTH{uuid4().hex[:6].upper()}",
            auth_amount=89900,  # NT$899 in cents
            period_type="M",  # Monthly
            frequency=1,
            period_amount=89900,  # NT$899 per period in cents
            exec_times=0,  # Current executions
            exec_times_limit=999,  # Max executions
            card_last4="4242",
            card_brand="VISA",
            card_type="CREDIT",
            auth_status=ECPayAuthStatus.ACTIVE.value,
            auth_date=datetime.now(),
            next_pay_date=date.today() + timedelta(days=30),
            description="Howie 測試訂閱 - 專業方案"
        )
        
        db.add(auth_record)
        db.flush()  # 獲取 auth_record.id
        
        # 創建 SaaS 訂閱
        print("📋 創建訂閱記錄...")
        subscription = SaasSubscription(
            user_id=user.id,
            auth_id=auth_record.id,
            plan_id="PRO",
            plan_name="專業方案",
            billing_cycle="monthly",
            amount_twd=89900,  # 899.00 TWD in cents
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=date.today(),
            current_period_end=date.today() + timedelta(days=30),
            cancel_at_period_end=False
        )
        
        db.add(subscription)
        db.flush()  # 獲取 subscription.id
        
        # 創建成功付款記錄
        print("💰 創建付款記錄...")
        payment = SubscriptionPayment(
            subscription_id=subscription.id,
            auth_id=auth_record.id,
            gwsr=auth_record.gwsr,
            amount=89900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            processed_at=datetime.now(),
            failure_reason=None
        )
        
        db.add(payment)
        
        # 更新用戶方案
        print("👤 更新用戶方案...")
        user.plan = UserPlan.PRO
        
        # 提交所有變更
        db.commit()
        
        print("\n🎉 Howie 的訂閱數據創建完成!")
        print(f"📧 用戶: {user.email}")
        print(f"📋 訂閱方案: {subscription.plan_id} ({subscription.plan_name})")
        print(f"💳 付款方式: VISA ****{auth_record.card_last4}")
        print(f"📅 下次付款: {auth_record.next_pay_date}")
        print(f"💰 月費: NT${subscription.amount_twd / 100}")
        print(f"📊 狀態: {subscription.status}")
        
        print("\n🧪 測試建議:")
        print("1. 使用 howie.yu@gmail.com 登入前端")
        print("2. 重新載入付款設定頁面")
        print("3. 檢查訂閱資訊是否正確顯示")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_howie_subscription()