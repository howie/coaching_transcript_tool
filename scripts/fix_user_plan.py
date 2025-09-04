#!/usr/bin/env python3
"""
修復用戶方案的腳本
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from coaching_assistant.core.database import get_db
from coaching_assistant.models import User, SaasSubscription
from coaching_assistant.models.user import UserPlan

def fix_user_plan():
    """修復用戶方案"""
    
    db = next(get_db())
    
    try:
        # 找到有訂閱的用戶
        users_with_subscriptions = db.query(User).join(SaasSubscription).all()
        
        for user in users_with_subscriptions:
            subscription = db.query(SaasSubscription).filter(
                SaasSubscription.user_id == user.id,
                SaasSubscription.status.in_(["active", "past_due"])
            ).first()
            
            if subscription:
                print(f"🔧 修復用戶 {user.email}:")
                print(f"   - 當前方案: {user.plan}")
                print(f"   - 訂閱方案: {subscription.plan_id}")
                
                # 根據訂閱更新用戶方案
                if subscription.plan_id == "PRO":
                    user.plan = UserPlan.PRO
                elif subscription.plan_id == "ENTERPRISE":
                    user.plan = UserPlan.ENTERPRISE
                else:
                    user.plan = UserPlan.FREE
                
                print(f"   - 更新為: {user.plan}")
        
        db.commit()
        print("✅ 用戶方案修復完成")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_plan()