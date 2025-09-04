#!/usr/bin/env python3
"""
檢查所有用戶的腳本
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from coaching_assistant.core.database import get_db
from coaching_assistant.models import User, SaasSubscription

def check_all_users():
    """檢查所有用戶"""
    
    db = next(get_db())
    
    try:
        users = db.query(User).all()
        
        print(f"📊 總共有 {len(users)} 個用戶:")
        print("-" * 80)
        
        for i, user in enumerate(users, 1):
            print(f"{i}. 👤 用戶: {user.email}")
            print(f"   🆔 ID: {user.id}")
            print(f"   📋 方案: {user.plan}")
            print(f"   📅 創建時間: {user.created_at}")
            
            # 檢查訂閱
            subscription = db.query(SaasSubscription).filter(
                SaasSubscription.user_id == user.id
            ).first()
            
            if subscription:
                print(f"   💳 有訂閱: {subscription.plan_id} ({subscription.status})")
            else:
                print(f"   ❌ 無訂閱")
            
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_all_users()