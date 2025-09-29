#!/usr/bin/env python3
"""
創建測試訂閱數據的腳本

用於在開發環境中測試付款設定頁面的訂閱功能
"""

import os
import sys
from datetime import date, datetime, timedelta
from uuid import uuid4

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from coaching_assistant.core.database import get_db
from coaching_assistant.models import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    PaymentStatus,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
    User,
)


def setup_test_subscription_data():
    """設定測試訂閱數據"""

    db = next(get_db())

    try:
        print("🔍 檢查現有用戶...")

        # 查找現有用戶（可以使用任何已存在的用戶）
        user = db.query(User).first()

        if not user:
            print("❌ 沒有找到用戶，請先創建用戶")
            return

        print(f"✅ 找到用戶: {user.email} (ID: {user.id})")

        # 檢查是否已有訂閱
        existing_subscription = (
            db.query(SaasSubscription)
            .filter(SaasSubscription.user_id == user.id)
            .first()
        )

        if existing_subscription:
            print(
                f"⚠️  用戶已有訂閱: {existing_subscription.plan_id} ({existing_subscription.status})"
            )

            # 詢問是否要重新創建
            response = input("是否要重新創建測試訂閱? (y/N): ")
            if response.lower() != "y":
                return

            # 刪除現有訂閱數據
            db.query(SubscriptionPayment).filter(
                SubscriptionPayment.subscription_id == existing_subscription.id
            ).delete()

            db.query(SaasSubscription).filter(
                SaasSubscription.user_id == user.id
            ).delete()

            db.query(ECPayCreditAuthorization).filter(
                ECPayCreditAuthorization.user_id == user.id
            ).delete()

            db.commit()
            print("🗑️  已清除現有訂閱數據")

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
            description="測試訂閱 - 專業方案",
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
            cancel_at_period_end=False,
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
            failure_reason=None,
        )

        db.add(payment)

        # 更新用戶方案
        print("👤 更新用戶方案...")
        from coaching_assistant.models.user import UserPlan

        user.plan = UserPlan.PRO

        # 提交所有變更
        db.commit()

        print("\n🎉 測試訂閱數據創建完成!")
        print(f"📧 用戶: {user.email}")
        print(f"📋 訂閱方案: {subscription.plan_id} ({subscription.plan_name})")
        print(f"💳 付款方式: VISA ****{auth_record.card_last4}")
        print(f"📅 下次付款: {auth_record.next_pay_date}")
        print(f"💰 月費: NT${subscription.amount_twd / 100}")
        print(f"📊 狀態: {subscription.status}")

        # 建議測試步驟
        print("\n🧪 測試建議:")
        print("1. 重新載入付款設定頁面")
        print("2. 檢查訂閱資訊是否正確顯示")
        print("3. 測試取消/重新啟用功能")
        print("4. 查看付款方式資訊")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def show_current_subscriptions():
    """顯示當前所有訂閱"""

    db = next(get_db())

    try:
        print("📋 當前所有訂閱:")
        print("-" * 80)

        subscriptions = db.query(SaasSubscription).join(User).all()

        if not subscriptions:
            print("沒有找到任何訂閱記錄")
            return

        for sub in subscriptions:
            print(f"👤 用戶: {sub.user.email}")
            print(f"📋 方案: {sub.plan_id} ({sub.plan_name})")
            print(f"📊 狀態: {sub.status}")
            print(f"💰 金額: NT${sub.amount_twd / 100}")
            print(f"🔄 週期: {sub.billing_cycle}")
            print(f"📅 期間: {sub.current_period_start} → {sub.current_period_end}")
            print(f"🆔 ID: {sub.id}")
            print("-" * 40)

    except Exception as e:
        print(f"❌ 錯誤: {e}")
    finally:
        db.close()


def clean_all_subscriptions():
    """清理所有訂閱數據（謹慎使用）"""

    print("⚠️  這會刪除所有訂閱相關數據!")
    response = input("確定要繼續嗎? (yes/N): ")
    if response.lower() != "yes":
        print("已取消")
        return

    db = next(get_db())

    try:
        # 刪除付款記錄
        payment_count = db.query(SubscriptionPayment).count()
        db.query(SubscriptionPayment).delete()

        # 刪除訂閱記錄
        subscription_count = db.query(SaasSubscription).count()
        db.query(SaasSubscription).delete()

        # 刪除授權記錄
        auth_count = db.query(ECPayCreditAuthorization).count()
        db.query(ECPayCreditAuthorization).delete()

        # 重設用戶方案為 FREE
        db.query(User).update({"plan": "FREE"})

        db.commit()

        print("🗑️  已刪除:")
        print(f"   - {payment_count} 筆付款記錄")
        print(f"   - {subscription_count} 筆訂閱記錄")
        print(f"   - {auth_count} 筆授權記錄")
        print("   - 所有用戶重設為 FREE 方案")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="管理測試訂閱數據")
    parser.add_argument(
        "action",
        choices=["setup", "show", "clean"],
        help="操作: setup=創建測試數據, show=顯示當前數據, clean=清理所有數據",
    )

    args = parser.parse_args()

    if args.action == "setup":
        setup_test_subscription_data()
    elif args.action == "show":
        show_current_subscriptions()
    elif args.action == "clean":
        clean_all_subscriptions()
