#!/usr/bin/env python3
"""
LeMUR Database Processing Verification Script

This script tests LeMUR optimization on existing database sessions:
1. Find existing session with completed transcript
2. Apply LeMUR speaker identification
3. Apply LeMUR punctuation optimization
4. Compare before and after results
5. Validate database updates

Usage:
    python test_lemur_database_processing.py --session-id <session_id> --auth-token <token>
    python test_lemur_database_processing.py --list-sessions --auth-token <token>

Requirements:
    - Valid authentication token
    - API server running on localhost:8000
    - Existing session with completed transcript
"""

import asyncio
import argparse
import json
import logging
import sys
from typing import Dict, List, Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000"


class LeMURDatabaseTester:
    """Test LeMUR processing on existing database sessions."""
    
    def __init__(self, auth_token: str, api_base_url: str = API_BASE_URL):
        self.auth_token = auth_token
        self.api_base_url = api_base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
    async def list_available_sessions(self, limit: int = 20) -> List[Dict]:
        """List available sessions with completed transcripts."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"📋 Fetching available sessions (limit: {limit})")
            response = await client.get(
                f"{self.api_base_url}/api/v1/sessions?page=1&page_size={limit}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get sessions: {response.status_code} - {response.text}")
                
            sessions_data = response.json()
            
            # Handle both list and object responses
            if isinstance(sessions_data, list):
                sessions = sessions_data
            else:
                sessions = sessions_data.get("sessions", sessions_data.get("data", []))
            
            # Filter for completed sessions
            completed_sessions = [s for s in sessions if s.get("status") == "completed"]
            
            logger.info(f"📊 Found {len(sessions)} total sessions, {len(completed_sessions)} completed")
            return completed_sessions
    
    async def get_session_details(self, session_id: str) -> Dict:
        """Get detailed information about a session."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"🔍 Getting session details: {session_id}")
            response = await client.get(
                f"{self.api_base_url}/api/v1/sessions/{session_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get session details: {response.status_code} - {response.text}")
                
            session_data = response.json()
            logger.info(f"✅ Session found - Title: {session_data.get('title', 'Untitled')}")
            logger.info(f"   Status: {session_data.get('status')}")
            logger.info(f"   Duration: {session_data.get('duration_seconds', 0)}s")
            logger.info(f"   Language: {session_data.get('language', 'auto')}")
            
            return session_data
    
    async def get_transcript_segments(self, session_id: str) -> List[Dict]:
        """Get transcript segments for a session."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"📋 Getting transcript segments for session: {session_id}")
            response = await client.get(
                f"{self.api_base_url}/api/v1/sessions/{session_id}/transcript?format=json",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get transcript: {response.status_code} - {response.text}")
                
            transcript_data = response.json()
            segments = transcript_data.get("segments", [])
            logger.info(f"📊 Retrieved {len(segments)} transcript segments")
            
            return segments
    
    async def apply_speaker_identification(self, session_id: str, custom_prompt: Optional[str] = None) -> Dict:
        """Apply LeMUR speaker identification to database segments."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "custom_prompts": {}
            }
            if custom_prompt:
                payload["custom_prompts"]["speakerPrompt"] = custom_prompt
                
            logger.info(f"🎭 Applying LeMUR speaker identification to session: {session_id}")
            response = await client.post(
                f"{self.api_base_url}/api/v1/transcript/session/{session_id}/lemur-speaker-identification",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to apply speaker identification: {response.status_code} - {response.text}")
                
            result = response.json()
            speaker_updates = result.get('segment_updates', 0)
            speaker_mapping = result.get('speaker_mapping', {})
            
            logger.info(f"✅ Speaker identification completed:")
            logger.info(f"   Database updates: {speaker_updates}")
            logger.info(f"   Speaker mapping: {speaker_mapping}")
            
            return result
    
    async def apply_punctuation_optimization(self, session_id: str, custom_prompt: Optional[str] = None) -> Dict:
        """Apply LeMUR punctuation optimization to database segments."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "custom_prompts": {}
            }
            if custom_prompt:
                payload["custom_prompts"]["punctuationPrompt"] = custom_prompt
                
            logger.info(f"🔤 Applying LeMUR punctuation optimization to session: {session_id}")
            response = await client.post(
                f"{self.api_base_url}/api/v1/transcript/session/{session_id}/lemur-punctuation-optimization",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to apply punctuation optimization: {response.status_code} - {response.text}")
                
            result = response.json()
            content_updates = result.get('segment_updates', 0)
            improvements = result.get('improvements_made', [])
            
            logger.info(f"✅ Punctuation optimization completed:")
            logger.info(f"   Database updates: {content_updates}")
            logger.info(f"   Improvements: {improvements}")
            
            return result
    
    def analyze_segment_changes(self, before_segments: List[Dict], after_segments: List[Dict]) -> Dict:
        """Analyze the changes between before and after segments."""
        logger.info("=" * 60)
        logger.info("📊 DETAILED SEGMENT ANALYSIS")
        logger.info("=" * 60)
        
        if len(before_segments) != len(after_segments):
            logger.warning(f"⚠️  Segment count mismatch: {len(before_segments)} → {len(after_segments)}")
        
        speaker_changes = []
        content_changes = []
        identical_segments = 0
        
        for i, (before, after) in enumerate(zip(before_segments, after_segments)):
            before_speaker = before.get('speaker_id', before.get('speaker'))
            after_speaker = after.get('speaker_id', after.get('speaker'))
            before_content = before.get('content', before.get('text', ''))
            after_content = after.get('content', after.get('text', ''))
            
            has_speaker_change = before_speaker != after_speaker
            has_content_change = before_content != after_content
            
            if has_speaker_change:
                speaker_changes.append({
                    'segment_index': i,
                    'before_speaker': before_speaker,
                    'after_speaker': after_speaker,
                    'content': before_content[:150] + "..." if len(before_content) > 150 else before_content
                })
            
            if has_content_change:
                content_changes.append({
                    'segment_index': i,
                    'before_content': before_content,
                    'after_content': after_content,
                    'speaker': after_speaker
                })
            
            if not has_speaker_change and not has_content_change:
                identical_segments += 1
        
        # Log detailed changes
        logger.info(f"📈 Total segments analyzed: {len(before_segments)}")
        logger.info(f"🎭 Speaker changes: {len(speaker_changes)}")
        logger.info(f"🔤 Content changes: {len(content_changes)}")
        logger.info(f"🔄 Identical segments: {identical_segments}")
        
        # Show speaker change examples
        if speaker_changes:
            logger.info(f"\n🎭 SPEAKER CHANGE EXAMPLES (first 3):")
            for change in speaker_changes[:3]:
                logger.info(f"   Segment {change['segment_index'] + 1}:")
                logger.info(f"     Speaker: {change['before_speaker']} → {change['after_speaker']}")
                logger.info(f"     Content: {change['content']}")
        
        # Show content change examples
        if content_changes:
            logger.info(f"\n🔤 CONTENT CHANGE EXAMPLES (first 3):")
            for change in content_changes[:3]:
                logger.info(f"   Segment {change['segment_index'] + 1} (Speaker {change['speaker']}):")
                logger.info(f"     Before: {change['before_content']}")
                logger.info(f"     After:  {change['after_content']}")
                logger.info(f"     Change: Punctuation/formatting improved")
        
        if not speaker_changes and not content_changes:
            logger.info("✨ No changes detected - segments were already optimal!")
        
        logger.info("=" * 60)
        
        return {
            'total_segments': len(before_segments),
            'speaker_changes': len(speaker_changes),
            'content_changes': len(content_changes),
            'identical_segments': identical_segments,
            'speaker_change_details': speaker_changes,
            'content_change_details': content_changes
        }
    
    async def test_database_processing(
        self, 
        session_id: str, 
        custom_speaker_prompt: Optional[str] = None,
        custom_punctuation_prompt: Optional[str] = None,
        skip_speaker_identification: bool = False,
        skip_punctuation_optimization: bool = False
    ) -> Dict:
        """Test LeMUR processing on an existing database session."""
        logger.info("🎯 STARTING LEMUR DATABASE PROCESSING TEST")
        logger.info(f"🔍 Session ID: {session_id}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Get session details
            session_details = await self.get_session_details(session_id)
            
            if session_details.get('status') != 'completed':
                raise ValueError(f"Session status is '{session_details.get('status')}', expected 'completed'")
            
            # Step 2: Get initial transcript segments
            initial_segments = await self.get_transcript_segments(session_id)
            
            if not initial_segments:
                raise ValueError("No transcript segments found for this session")
            
            # Step 3: Apply optimizations
            speaker_result = None
            punctuation_result = None
            
            if not skip_speaker_identification:
                speaker_result = await self.apply_speaker_identification(session_id, custom_speaker_prompt)
                
                # Get segments after speaker identification
                after_speaker_segments = await self.get_transcript_segments(session_id)
                speaker_analysis = self.analyze_segment_changes(initial_segments, after_speaker_segments)
                
                logger.info(f"\n🎭 SPEAKER IDENTIFICATION ANALYSIS:")
                logger.info(f"   Database updates made: {speaker_result.get('segment_updates', 0)}")
                logger.info(f"   Actual speaker changes detected: {speaker_analysis['speaker_changes']}")
            
            if not skip_punctuation_optimization:
                # Use segments after speaker identification as baseline for punctuation
                baseline_segments = after_speaker_segments if not skip_speaker_identification else initial_segments
                
                punctuation_result = await self.apply_punctuation_optimization(session_id, custom_punctuation_prompt)
                
                # Get final segments after punctuation optimization
                final_segments = await self.get_transcript_segments(session_id)
                punctuation_analysis = self.analyze_segment_changes(baseline_segments, final_segments)
                
                logger.info(f"\n🔤 PUNCTUATION OPTIMIZATION ANALYSIS:")
                logger.info(f"   Database updates made: {punctuation_result.get('segment_updates', 0)}")
                logger.info(f"   Actual content changes detected: {punctuation_analysis['content_changes']}")
            
            # Step 4: Final comparison
            final_segments = await self.get_transcript_segments(session_id)
            overall_analysis = self.analyze_segment_changes(initial_segments, final_segments)
            
            # Compile results
            results = {
                'session_id': session_id,
                'session_details': session_details,
                'initial_segment_count': len(initial_segments),
                'final_segment_count': len(final_segments),
                'speaker_identification_result': speaker_result,
                'punctuation_optimization_result': punctuation_result,
                'overall_analysis': overall_analysis,
                'success': True
            }
            
            logger.info("🎉 DATABASE PROCESSING TEST COMPLETED SUCCESSFULLY!")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Database processing test failed: {str(e)}")
            raise
    
    async def print_session_list(self, sessions: List[Dict]):
        """Print formatted list of available sessions."""
        if not sessions:
            logger.info("📭 No completed sessions found")
            return
            
        logger.info(f"📋 AVAILABLE COMPLETED SESSIONS ({len(sessions)}):")
        logger.info("=" * 80)
        
        for i, session in enumerate(sessions, 1):
            session_id = session.get('id', 'Unknown')
            title = session.get('title', 'Untitled')
            duration = session.get('duration_seconds', 0)
            language = session.get('language', 'auto')
            created_at = session.get('created_at', 'Unknown')
            
            logger.info(f"{i:2}. ID: {session_id}")
            logger.info(f"    Title: {title}")
            logger.info(f"    Duration: {duration}s ({duration//60}m {duration%60}s)")
            logger.info(f"    Language: {language}")
            logger.info(f"    Created: {created_at}")
            logger.info("-" * 80)


async def main():
    parser = argparse.ArgumentParser(description="Test LeMUR database processing on existing sessions")
    parser.add_argument("--auth-token", required=True, help="Authentication token")
    parser.add_argument("--session-id", help="Session ID to process")
    parser.add_argument("--list-sessions", action="store_true", help="List available completed sessions")
    parser.add_argument("--speaker-prompt", help="Custom speaker identification prompt")
    parser.add_argument("--punctuation-prompt", help="Custom punctuation optimization prompt")
    parser.add_argument("--skip-speaker", action="store_true", help="Skip speaker identification")
    parser.add_argument("--skip-punctuation", action="store_true", help="Skip punctuation optimization")
    parser.add_argument("--api-url", default=API_BASE_URL, help="API base URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    tester = LeMURDatabaseTester(args.auth_token, args.api_url)
    
    try:
        if args.list_sessions:
            # List available sessions
            sessions = await tester.list_available_sessions(50)
            await tester.print_session_list(sessions)
            return
        
        if not args.session_id:
            logger.error("❌ Please provide --session-id or use --list-sessions to see available sessions")
            sys.exit(1)
        
        # Test database processing
        results = await tester.test_database_processing(
            session_id=args.session_id,
            custom_speaker_prompt=args.speaker_prompt,
            custom_punctuation_prompt=args.punctuation_prompt,
            skip_speaker_identification=args.skip_speaker,
            skip_punctuation_optimization=args.skip_punctuation
        )
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"📄 Results saved to: {args.output}")
        else:
            print("\n" + "=" * 60)
            print("📋 FINAL RESULTS:")
            print("=" * 60)
            print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
            
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())