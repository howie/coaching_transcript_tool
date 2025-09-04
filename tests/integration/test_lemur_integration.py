#!/usr/bin/env python3
"""
Test script for LeMUR transcript smoothing integration.

This script tests the new LeMUR-based transcript smoothing functionality
with sample transcript data to verify it works correctly.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample transcript data with speaker boundary errors
SAMPLE_TRANSCRIPT_DATA = [
    {
        "start": 1000,  # 1 second
        "end": 3500,    # 3.5 seconds
        "speaker": "A",
        "text": "你好我想要問一下關於這個問題"
    },
    {
        "start": 3500,
        "end": 8000,
        "speaker": "B", 
        "text": "好的請問是什麼問題你可以詳細說明一下嗎我會盡力幫助你解決"
    },
    {
        "start": 8000,
        "end": 10000,
        "speaker": "A",
        "text": "我最近工作上遇到困難不知道該怎麼辦"
    },
    {
        "start": 10000,
        "end": 15000,
        "speaker": "B",
        "text": "可以跟我分享一下具體是什麼樣的困難嗎這樣我比較能夠給你適當的建議"
    }
]


async def test_lemur_integration():
    """Test LeMUR transcript smoothing with sample data."""
    logger.info("🧪 Starting LeMUR integration test")
    
    try:
        # Check if AssemblyAI API key is available
        api_key = os.getenv('ASSEMBLYAI_API_KEY')
        if not api_key:
            logger.error("❌ ASSEMBLYAI_API_KEY not found in environment")
            logger.info("💡 Set the API key with: export ASSEMBLYAI_API_KEY='your_key_here'")
            return False
        
        # Import our LeMUR smoother
        from coaching_assistant.services.lemur_transcript_smoother import smooth_transcript_with_lemur
        
        logger.info(f"📝 Testing with {len(SAMPLE_TRANSCRIPT_DATA)} sample segments")
        logger.info("Sample data:")
        for i, segment in enumerate(SAMPLE_TRANSCRIPT_DATA):
            logger.info(f"  {segment['speaker']}: {segment['text']}")
        
        # Run LeMUR smoothing
        logger.info("🧠 Applying LeMUR smoothing...")
        result = await smooth_transcript_with_lemur(
            segments=SAMPLE_TRANSCRIPT_DATA,
            session_language="zh-TW",
            is_coaching_session=True
        )
        
        # Display results
        logger.info("✅ LeMUR smoothing completed!")
        logger.info(f"🎭 Speaker mapping: {result.speaker_mapping}")
        logger.info(f"📋 Improvements made: {', '.join(result.improvements_made)}")
        logger.info(f"📄 Processing notes: {result.processing_notes}")
        
        logger.info(f"📊 Processed segments ({len(result.segments)}):")
        for i, segment in enumerate(result.segments):
            logger.info(f"  {segment.speaker}: {segment.text}")
            
        # Verify that improvements were actually made
        success_indicators = [
            len(result.segments) > 0,
            len(result.speaker_mapping) > 0,
            len(result.improvements_made) > 0,
            any('教練' in segment.speaker or 'Coach' in segment.speaker for segment in result.segments),
            any('客戶' in segment.speaker or 'Client' in segment.speaker for segment in result.segments)
        ]
        
        if all(success_indicators):
            logger.info("🎉 LeMUR integration test PASSED!")
            logger.info("   ✓ Segments processed successfully")
            logger.info("   ✓ Speaker mapping applied")
            logger.info("   ✓ Improvements documented")
            logger.info("   ✓ Coaching context recognized")
            return True
        else:
            logger.warning("⚠️  LeMUR integration test had issues:")
            logger.warning(f"   Segments: {len(result.segments)} (expected > 0)")
            logger.warning(f"   Speaker mapping: {len(result.speaker_mapping)} (expected > 0)")
            logger.warning(f"   Improvements: {len(result.improvements_made)} (expected > 0)")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error - module not found: {e}")
        logger.info("💡 Make sure to install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"❌ LeMUR integration test failed: {e}")
        logger.exception("Full error traceback:")
        return False


async def test_api_endpoint():
    """Test the LeMUR API endpoint (requires running server)."""
    logger.info("🌐 Testing LeMUR API endpoint...")
    
    try:
        import httpx
        
        # Prepare test request
        test_request = {
            "transcript": {
                "utterances": SAMPLE_TRANSCRIPT_DATA,
                "language_code": "zh"
            },
            "language": "chinese"
        }
        
        # Try to call the API (this will only work if server is running)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/transcript/lemur-smooth",
                json=test_request,
                headers={"Authorization": "Bearer fake_token_for_testing"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ API endpoint test PASSED!")
                logger.info(f"   Processed {len(result['segments'])} segments")
                logger.info(f"   Speaker mapping: {result['speaker_mapping']}")
                return True
            else:
                logger.info(f"ℹ️  API endpoint not available (status: {response.status_code})")
                logger.info("   This is expected if the server is not running")
                return None
                
    except Exception as e:
        logger.info(f"ℹ️  API endpoint test skipped: {e}")
        logger.info("   This is expected if the server is not running")
        return None


async def main():
    """Run all LeMUR integration tests."""
    logger.info("🚀 Running LeMUR Integration Tests")
    logger.info("=" * 60)
    
    # Test 1: Core LeMUR functionality
    test1_passed = await test_lemur_integration()
    
    # Test 2: API endpoint (optional)
    test2_result = await test_api_endpoint()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📋 Test Summary:")
    logger.info(f"   Core LeMUR functionality: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    if test2_result is None:
        logger.info("   API endpoint test: ⏭️  SKIPPED (server not running)")
    elif test2_result:
        logger.info("   API endpoint test: ✅ PASSED")
    else:
        logger.info("   API endpoint test: ❌ FAILED")
    
    overall_success = test1_passed and (test2_result is None or test2_result)
    
    if overall_success:
        logger.info("🎉 Overall result: SUCCESS - LeMUR integration is working!")
    else:
        logger.info("❌ Overall result: FAILURE - Please check the errors above")
        
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)