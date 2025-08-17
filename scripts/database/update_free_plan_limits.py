#!/usr/bin/env python3
"""
Update free plan limits to new values.
"""

import json
from datetime import datetime, UTC
from coaching_assistant.core.config import Settings
from sqlalchemy import create_engine, text

def update_free_plan_limits():
    """Update free plan limits to new configuration."""
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    
    # New free plan limits
    new_limits = {
        'maxSessions': 10,       # Updated: 10 sessions per month (was 3)
        'maxMinutes': 200,       # Updated: 200 min of transcription per month (was 60)
        'maxTranscriptions': 5,  # Same: 5 transcriptions per month
        'maxFileSize': 60,       # Updated: up to 40 min per recording (~60MB, was 25MB)
        'maxExports': 10,        # Same: Conservative limit
        'retentionDays': 30,     # Same
        'concurrentJobs': 1      # Same
    }
    
    with engine.connect() as conn:
        # Check if free plan exists
        result = conn.execute(text("SELECT id, limits FROM plan_configurations WHERE plan_name = 'free'"))
        free_plan = result.fetchone()
        
        if not free_plan:
            print("❌ Free plan not found in database")
            return
        
        # Show current limits  
        current_limits = free_plan.limits if isinstance(free_plan.limits, dict) else json.loads(free_plan.limits)
        print("📊 Current free plan limits:")
        for key, value in current_limits.items():
            print(f"  - {key}: {value}")
        
        # Update the limits
        conn.execute(text("""
            UPDATE plan_configurations 
            SET limits = :limits, updated_at = :updated_at
            WHERE plan_name = 'free'
        """), {
            'limits': json.dumps(new_limits),
            'updated_at': datetime.now(UTC)
        })
        
        conn.commit()
        
        # Verify update
        result = conn.execute(text("SELECT limits FROM plan_configurations WHERE plan_name = 'free'"))
        updated_plan = result.fetchone()
        updated_limits = updated_plan.limits if isinstance(updated_plan.limits, dict) else json.loads(updated_plan.limits)
        
        print("\n✅ Updated free plan limits:")
        for key, value in updated_limits.items():
            print(f"  - {key}: {value}")
        
        # Show the changes
        print(f"\n🔄 Changes made:")
        print(f"  - Sessions: {current_limits['maxSessions']} → {updated_limits['maxSessions']}")
        print(f"  - Minutes: {current_limits['maxMinutes']} → {updated_limits['maxMinutes']}")  
        print(f"  - File size: {current_limits['maxFileSize']}MB → {updated_limits['maxFileSize']}MB")
        print(f"  - Transcriptions: {current_limits['maxTranscriptions']} (unchanged)")

if __name__ == "__main__":
    update_free_plan_limits()