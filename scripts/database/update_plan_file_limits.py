#!/usr/bin/env python3
"""
Update existing plan configurations to set file size limit to 60MB.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.plan_configuration import PlanConfiguration


def update_plan_file_limits():
    """Update all plan configurations to set max_file_size_mb to 60."""

    with get_db_session() as db:
        # Get all plan configurations
        plans = db.query(PlanConfiguration).all()

        print(f"📋 Found {len(plans)} plan configurations to update")

        for plan in plans:
            # Update limits dictionary
            if plan.limits is None:
                plan.limits = {}

            # Check both possible keys (existing format and new format)
            old_file_size = plan.limits.get(
                "maxFileSize", plan.limits.get("max_file_size_mb", "not set")
            )

            # Update to 60MB using the existing key format if it exists, otherwise use new format
            if "maxFileSize" in plan.limits:
                plan.limits["maxFileSize"] = 60
                key_used = "maxFileSize"
            else:
                plan.limits["max_file_size_mb"] = 60
                key_used = "max_file_size_mb"

            print(
                f"✅ Updated {plan.plan_type.value} plan ({key_used}): {old_file_size} → 60 MB"
            )

        print("🎉 Successfully updated all plan file size limits to 60MB")

        # Verify changes within the same transaction
        print("\n📊 Verification:")
        for plan in plans:
            file_size = plan.limits.get(
                "maxFileSize", plan.limits.get("max_file_size_mb", "not found")
            )
            print(f"  {plan.plan_type.value}: file_size = {file_size} MB")

    return True


if __name__ == "__main__":
    print("🔄 Updating plan file size limits...")
    success = update_plan_file_limits()
    if not success:
        sys.exit(1)
