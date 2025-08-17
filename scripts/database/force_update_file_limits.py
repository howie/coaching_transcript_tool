#!/usr/bin/env python3
"""
Force update plan configurations to set file size limit to 60MB using raw SQL.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from coaching_assistant.core.database import SessionLocal
from sqlalchemy import text

def force_update_file_limits():
    """Force update file limits using raw SQL."""
    
    db = SessionLocal()
    
    try:
        # Update each plan individually using raw SQL
        
        # Free plan
        db.execute(text("""
            UPDATE plan_configurations 
            SET limits = limits::jsonb || '{"maxFileSize": 60}'::jsonb
            WHERE plan_type = 'FREE'
        """))
        
        # Pro plan  
        db.execute(text("""
            UPDATE plan_configurations 
            SET limits = limits::jsonb || '{"maxFileSize": 60}'::jsonb
            WHERE plan_type = 'PRO'
        """))
        
        # Enterprise plan
        db.execute(text("""
            UPDATE plan_configurations 
            SET limits = limits::jsonb || '{"maxFileSize": 60}'::jsonb
            WHERE plan_type = 'ENTERPRISE'
        """))
        
        db.commit()
        print("✅ Successfully updated all plan file size limits using raw SQL")
        
        # Verify
        result = db.execute(text("""
            SELECT plan_type, limits->>'maxFileSize' as max_file_size 
            FROM plan_configurations 
            ORDER BY plan_type
        """))
        
        print("\n📊 Verification:")
        for row in result:
            print(f"  {row.plan_type}: maxFileSize = {row.max_file_size} MB")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating plan limits: {e}")
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("🔄 Force updating plan file size limits with raw SQL...")
    success = force_update_file_limits()
    if not success:
        sys.exit(1)