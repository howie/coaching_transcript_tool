#!/usr/bin/env python3
"""
Test script to verify beta limit enforcement is working correctly.
CRITICAL for preventing cost escalation during beta launch.
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from coaching_assistant.core.config import Settings
from coaching_assistant.core.database import get_db, engine
from coaching_assistant.models.user import User
from coaching_assistant.models.session import Session
from coaching_assistant.services.plan_limits import PlanLimits
from coaching_assistant.api.sessions import create_session, start_transcription, get_upload_url
from coaching_assistant.api.sessions import SessionCreate
from fastapi import HTTPException
from unittest.mock import Mock
import uuid

async def test_session_limit_enforcement():
    """Test that session creation is blocked when limit is reached."""
    print("🧪 Testing session limit enforcement...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find a test user
        user = db.query(User).first()
        if not user:
            print("❌ No users found for testing")
            return False
            
        # Set user to FREE plan and max out sessions
        user.plan = 'FREE'
        user.session_count = 3  # Beta limit for free plan
        db.commit()
        
        print(f"👤 Test user: {user.email}, Plan: {user.plan}, Sessions: {user.session_count}")
        
        # Try to create a session (should fail)
        session_data = SessionCreate(
            title="Test Beta Limit Session",
            language="en-US",
            stt_provider="google"
        )
        
        try:
            await create_session(session_data, db, user)
            print("❌ CRITICAL FAILURE: Session creation should have been blocked!")
            return False
        except HTTPException as e:
            if e.status_code == 403 and "session_limit_exceeded" in str(e.detail):
                print("✅ Session limit enforcement working correctly")
                return True
            else:
                print(f"❌ Wrong error type: {e.status_code} - {e.detail}")
                return False
    finally:
        # Clean up: reset user session count
        user.session_count = 0
        db.commit()
        db.close()

async def test_transcription_limit_enforcement():
    """Test that transcription is blocked when limit is reached."""
    print("🧪 Testing transcription limit enforcement...")
    
    db = next(get_db())
    
    try:
        # Find a test user and session
        user = db.query(User).first()
        session = db.query(Session).filter(Session.user_id == user.id).first()
        
        if not session:
            print("⚠️  No sessions found, creating test session...")
            # Create a test session first
            user.session_count = 0  # Reset to allow creation
            db.commit()
            
            session_data = SessionCreate(
                title="Test Transcription Limit Session",
                language="en-US",
                stt_provider="google"
            )
            
            session_response = await create_session(session_data, db, user)
            session = db.query(Session).filter(Session.id == session_response.id).first()
        
        # Set user to FREE plan and max out transcriptions
        user.plan = 'FREE'
        user.transcription_count = 5  # Beta limit for free plan
        db.commit()
        
        print(f"👤 Test user: {user.email}, Plan: {user.plan}, Transcriptions: {user.transcription_count}")
        
        # Try to start transcription (should fail)
        try:
            await start_transcription(session.id, db, user)
            print("❌ CRITICAL FAILURE: Transcription should have been blocked!")
            return False
        except HTTPException as e:
            if e.status_code == 403 and "transcription_limit_exceeded" in str(e.detail):
                print("✅ Transcription limit enforcement working correctly")
                return True
            else:
                print(f"❌ Wrong error type: {e.status_code} - {e.detail}")
                return False
    finally:
        # Clean up: reset user transcription count
        user.transcription_count = 0
        db.commit()
        db.close()

async def test_file_size_limit_enforcement():
    """Test that file upload is blocked when size exceeds limit."""
    print("🧪 Testing file size limit enforcement...")
    
    db = next(get_db())
    
    try:
        # Find a test user and session
        user = db.query(User).first()
        session = db.query(Session).filter(Session.user_id == user.id).first()
        
        if not session:
            print("⚠️  No sessions found for file size test")
            return False
        
        # Set user to FREE plan
        user.plan = 'FREE'
        db.commit()
        
        print(f"👤 Test user: {user.email}, Plan: {user.plan}")
        
        # Try to upload a file that exceeds the 25MB beta limit
        try:
            await get_upload_url(
                session_id=session.id,
                filename="large_file.mp3", 
                file_size_mb=30.0,  # Exceeds 25MB beta limit
                db=db,
                current_user=user
            )
            print("❌ CRITICAL FAILURE: Large file upload should have been blocked!")
            return False
        except HTTPException as e:
            if e.status_code == 413 and "file_size_exceeded" in str(e.detail):
                print("✅ File size limit enforcement working correctly")
                return True
            else:
                print(f"❌ Wrong error type: {e.status_code} - {e.detail}")
                return False
    finally:
        db.close()

def test_plan_limits_configuration():
    """Test that plan limits are correctly configured for beta safety."""
    print("🧪 Testing beta plan limits configuration...")
    
    # Test FREE plan beta limits
    free_limits = PlanLimits.from_user_plan('FREE')
    expected_free = {
        'sessions': 3,
        'transcriptions': 5, 
        'file_size': 25
    }
    
    actual_free = {
        'sessions': free_limits.max_sessions,
        'transcriptions': free_limits.max_transcriptions,
        'file_size': free_limits.max_file_size_mb
    }
    
    if actual_free == expected_free:
        print("✅ FREE plan beta limits correctly configured")
        success = True
    else:
        print(f"❌ FREE plan limits mismatch: expected {expected_free}, got {actual_free}")
        success = False
    
    # Test PRO plan beta limits
    pro_limits = PlanLimits.from_user_plan('PRO')
    expected_pro = {
        'sessions': 25,
        'transcriptions': 50,
        'file_size': 100
    }
    
    actual_pro = {
        'sessions': pro_limits.max_sessions,
        'transcriptions': pro_limits.max_transcriptions,
        'file_size': pro_limits.max_file_size_mb
    }
    
    if actual_pro == expected_pro:
        print("✅ PRO plan beta limits correctly configured")
    else:
        print(f"❌ PRO plan limits mismatch: expected {expected_pro}, got {actual_pro}")
        success = False
    
    return success

async def main():
    """Run all beta safety tests."""
    print("🚀 BETA SAFETY TEST SUITE")
    print("="*50)
    print("⚠️  CRITICAL: These tests verify cost control measures")
    print("="*50)
    
    all_tests_passed = True
    
    # Test 1: Plan limits configuration
    test1 = test_plan_limits_configuration()
    all_tests_passed = all_tests_passed and test1
    
    # Test 2: Session limit enforcement
    test2 = await test_session_limit_enforcement()
    all_tests_passed = all_tests_passed and test2
    
    # Test 3: Transcription limit enforcement  
    test3 = await test_transcription_limit_enforcement()
    all_tests_passed = all_tests_passed and test3
    
    # Test 4: File size limit enforcement
    test4 = await test_file_size_limit_enforcement()
    all_tests_passed = all_tests_passed and test4
    
    print("="*50)
    if all_tests_passed:
        print("✅ ALL BETA SAFETY TESTS PASSED")
        print("🚀 Ready for safe beta launch!")
        return 0
    else:
        print("❌ BETA SAFETY TESTS FAILED")
        print("🛑 DO NOT LAUNCH BETA - FIX ISSUES FIRST")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)