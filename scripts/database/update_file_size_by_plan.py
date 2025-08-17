#!/usr/bin/env python3
"""
Update plan configurations to set appropriate file size limits by plan tier.

FREE: 60MB
PRO: 200MB  
ENTERPRISE: 500MB
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.plan_configuration import PlanConfiguration
from coaching_assistant.models.user import UserPlan

def update_file_size_by_plan():
    """Update file size limits to be appropriate for each plan tier."""
    
    with get_db_session() as db:
        # Get all plan configurations
        plans = db.query(PlanConfiguration).all()
        
        print(f"📋 Found {len(plans)} plan configurations to update")
        
        for plan in plans:
            old_file_size = plan.limits.get("maxFileSize", "not set")
            
            if plan.plan_type == UserPlan.FREE:
                new_file_size = 60  # 60MB for free plan
            elif plan.plan_type == UserPlan.PRO:
                new_file_size = 200  # 200MB for pro plan
            elif plan.plan_type == UserPlan.ENTERPRISE:
                new_file_size = 500  # 500MB for enterprise plan
            else:
                continue  # Skip unknown plan types
            
            # Update limits dictionary
            if plan.limits is None:
                plan.limits = {}
            
            plan.limits["maxFileSize"] = new_file_size
            
            print(f"✅ Updated {plan.plan_type.value} plan: {old_file_size}MB → {new_file_size}MB")
        
        print("🎉 Successfully updated all plan file size limits by tier")
        
        # Verify changes within the same transaction
        print("\n📊 New File Size Limits:")
        for plan in plans:
            file_size = plan.limits.get("maxFileSize", "not found")
            print(f"  {plan.plan_type.value.upper()}: {file_size}MB")
    
    return True

if __name__ == "__main__":
    print("🔄 Updating plan file size limits by tier...")
    success = update_file_size_by_plan()
    if not success:
        sys.exit(1)