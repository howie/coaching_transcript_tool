#!/usr/bin/env python3
"""
Update plan configurations to correct TWD pricing.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.plan_configuration import PlanConfiguration
from coaching_assistant.models.user import UserPlan


def update_plan_pricing():
    """Update TWD pricing for all plan configurations."""

    with get_db_session() as db:
        # Get all plan configurations
        plans = db.query(PlanConfiguration).all()

        print(f"📋 Found {len(plans)} plan configurations to update")

        for plan in plans:
            old_monthly = plan.monthly_price_twd_cents
            old_annual = plan.annual_price_twd_cents

            if plan.plan_type == UserPlan.FREE:
                plan.monthly_price_twd_cents = 0
                plan.annual_price_twd_cents = 0
            elif plan.plan_type == UserPlan.PRO:
                plan.monthly_price_twd_cents = 79000  # NT$790
                plan.annual_price_twd_cents = 63200  # NT$632
            elif plan.plan_type == UserPlan.ENTERPRISE:
                plan.monthly_price_twd_cents = 189000  # NT$1,890
                plan.annual_price_twd_cents = 157500  # NT$1,575

            print(f"✅ Updated {plan.plan_type.value} plan:")
            print(
                f"   Monthly: NT${old_monthly / 100} → NT${plan.monthly_price_twd_cents / 100}"
            )
            print(
                f"   Annual: NT${old_annual / 100} → NT${plan.annual_price_twd_cents / 100}"
            )

        print("🎉 Successfully updated all plan TWD pricing")

        # Verify changes within the same transaction
        print("\n📊 Verification:")
        for plan in plans:
            print(
                f"  {plan.plan_type.value}: Monthly NT${plan.monthly_price_twd_cents / 100}, Annual NT${plan.annual_price_twd_cents / 100}"
            )

    return True


if __name__ == "__main__":
    print("🔄 Updating plan TWD pricing...")
    success = update_plan_pricing()
    if not success:
        sys.exit(1)
