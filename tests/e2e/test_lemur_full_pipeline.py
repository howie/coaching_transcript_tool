#!/usr/bin/env python3
"""
LeMUR Full Pipeline Verification Script

This script tests the complete pipeline:
1. Upload audio file
2. Start transcription (Google STT or AssemblyAI)
3. Apply LeMUR optimization for speaker identification and punctuation
4. Verify the improvements

Usage:
    python test_lemur_full_pipeline.py --audio-file path/to/audio.mp3 --user-email user@example.com

Requirements:
    - Valid authentication token
    - Audio file to upload
    - API server running on localhost:8000
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from pathlib import Path
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
TIMEOUT_SECONDS = 600  # 10 minutes for full pipeline


class LeMURPipelineTester:
    """Test the complete LeMUR processing pipeline."""
    
    def __init__(self, auth_token: str, api_base_url: str = API_BASE_URL):
        self.auth_token = auth_token
        self.api_base_url = api_base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
    async def create_session(self, title: str, language: str = "zh-TW") -> str:
        """Create a new transcription session."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "title": title,
                "language": language,
                "stt_provider": "google"  # or "assemblyai"
            }
            
            logger.info(f"🚀 Creating new session: {title}")
            response = await client.post(
                f"{self.api_base_url}/api/v1/sessions",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code not in [200, 201]:
                raise RuntimeError(f"Failed to create session: {response.status_code} - {response.text}")
                
            session_data = response.json()
            session_id = session_data["id"]
            logger.info(f"✅ Created session: {session_id}")
            return session_id
    
    async def upload_audio(self, session_id: str, audio_file_path: Path) -> str:
        """Upload audio file to the session."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get file info
            file_size_bytes = audio_file_path.stat().st_size
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            filename = audio_file_path.name
            
            # Get signed upload URL
            logger.info(f"📤 Getting upload URL for session: {session_id}")
            logger.info(f"   File: {filename} ({file_size_mb}MB)")
            
            response = await client.post(
                f"{self.api_base_url}/api/v1/sessions/{session_id}/upload-url",
                params={
                    "filename": filename,
                    "file_size_mb": file_size_mb
                },
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get upload URL: {response.status_code} - {response.text}")
                
            upload_data = response.json()
            upload_url = upload_data["upload_url"]
            
            # Upload file
            logger.info(f"📤 Uploading audio file: {audio_file_path}")
            
            # Determine content type based on file extension
            content_type = "video/mp4"  # Default for .mp4 files
            if filename.lower().endswith(('.mp3', '.wav', '.m4a')):
                content_type = "audio/mpeg" if filename.lower().endswith('.mp3') else "audio/wav"
            
            with open(audio_file_path, 'rb') as f:
                upload_response = await client.put(
                    upload_url, 
                    content=f.read(),
                    headers={"Content-Type": content_type}
                )
                
            if upload_response.status_code not in [200, 204]:
                raise RuntimeError(f"Failed to upload audio: {upload_response.status_code}")
                
            logger.info(f"✅ Audio uploaded successfully")
            return filename
    
    async def start_transcription(self, session_id: str) -> bool:
        """Start the transcription process."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"🎵 Starting transcription for session: {session_id}")
            response = await client.post(
                f"{self.api_base_url}/api/v1/sessions/{session_id}/start-transcription",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to start transcription: {response.status_code} - {response.text}")
                
            logger.info(f"✅ Transcription started successfully")
            return True
    
    async def wait_for_transcription_completion(self, session_id: str, timeout_seconds: int = TIMEOUT_SECONDS) -> bool:
        """Wait for transcription to complete."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"⏳ Waiting for transcription completion (timeout: {timeout_seconds}s)")
            
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/sessions/{session_id}/status",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get session status: {response.status_code}")
                    await asyncio.sleep(5)
                    continue
                    
                status_data = response.json()
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                logger.info(f"📊 Transcription progress: {progress}% - Status: {status}")
                
                if status == "completed":
                    logger.info(f"✅ Transcription completed successfully!")
                    return True
                elif status == "failed":
                    logger.error(f"❌ Transcription failed: {status_data.get('message', 'Unknown error')}")
                    return False
                    
                await asyncio.sleep(10)  # Check every 10 seconds
                
            logger.error(f"❌ Transcription timeout after {timeout_seconds} seconds")
            return False
    
    async def get_original_transcript(self, session_id: str) -> List[Dict]:
        """Get the original transcript segments before LeMUR processing."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_base_url}/api/v1/sessions/{session_id}/transcript?format=json",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get transcript: {response.status_code} - {response.text}")
                
            transcript_data = response.json()
            segments = transcript_data.get("segments", [])
            logger.info(f"📋 Retrieved {len(segments)} original transcript segments")
            return segments
    
    async def apply_lemur_speaker_identification(self, session_id: str, custom_prompt: Optional[str] = None) -> Dict:
        """Apply LeMUR speaker identification optimization."""
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
            logger.info(f"✅ Speaker identification completed - Speaker mapping: {result.get('speaker_mapping', {})}")
            return result
    
    async def apply_lemur_punctuation_optimization(self, session_id: str, custom_prompt: Optional[str] = None) -> Dict:
        """Apply LeMUR punctuation optimization."""
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
            logger.info(f"✅ Punctuation optimization completed - Improvements: {result.get('improvements_made', [])}")
            return result
    
    async def get_optimized_transcript(self, session_id: str) -> List[Dict]:
        """Get the transcript segments after LeMUR processing."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_base_url}/api/v1/sessions/{session_id}/transcript?format=json",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to get optimized transcript: {response.status_code} - {response.text}")
                
            transcript_data = response.json()
            segments = transcript_data.get("segments", [])
            logger.info(f"📋 Retrieved {len(segments)} optimized transcript segments")
            return segments
    
    def compare_transcripts(self, original_segments: List[Dict], optimized_segments: List[Dict]) -> Dict:
        """Compare original and optimized transcripts."""
        logger.info("=" * 60)
        logger.info("📊 TRANSCRIPT COMPARISON ANALYSIS")
        logger.info("=" * 60)
        
        speaker_changes = 0
        content_changes = 0
        examples = []
        
        for i, (orig, opt) in enumerate(zip(original_segments, optimized_segments)):
            orig_speaker = orig.get('speaker_id', orig.get('speaker'))
            opt_speaker = opt.get('speaker_id', opt.get('speaker'))
            orig_content = orig.get('content', orig.get('text', ''))
            opt_content = opt.get('content', opt.get('text', ''))
            
            if orig_speaker != opt_speaker:
                speaker_changes += 1
                if len(examples) < 3:
                    examples.append({
                        'type': 'speaker',
                        'segment': i + 1,
                        'original': f"Speaker {orig_speaker}",
                        'optimized': f"Speaker {opt_speaker}",
                        'content': orig_content[:100] + "..." if len(orig_content) > 100 else orig_content
                    })
            
            if orig_content != opt_content:
                content_changes += 1
                if len(examples) < 5:
                    examples.append({
                        'type': 'content',
                        'segment': i + 1,
                        'original': orig_content[:100] + "..." if len(orig_content) > 100 else orig_content,
                        'optimized': opt_content[:100] + "..." if len(opt_content) > 100 else opt_content
                    })
        
        # Print results
        logger.info(f"📈 Total segments: {len(original_segments)}")
        logger.info(f"🎭 Speaker changes: {speaker_changes}")
        logger.info(f"🔤 Content changes: {content_changes}")
        
        if examples:
            logger.info("\n📋 EXAMPLE CHANGES:")
            for example in examples:
                logger.info(f"\n{example['type'].upper()} CHANGE - Segment {example['segment']}:")
                logger.info(f"  Original: {example['original']}")
                logger.info(f"  Optimized: {example['optimized']}")
                if example['type'] == 'speaker':
                    logger.info(f"  Content: {example['content']}")
        
        logger.info("=" * 60)
        
        return {
            'total_segments': len(original_segments),
            'speaker_changes': speaker_changes,
            'content_changes': content_changes,
            'examples': examples
        }
    
    async def run_full_pipeline_test(
        self, 
        audio_file_path: Path, 
        session_title: Optional[str] = None,
        custom_speaker_prompt: Optional[str] = None,
        custom_punctuation_prompt: Optional[str] = None
    ) -> Dict:
        """Run the complete pipeline test."""
        if not audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
        if not session_title:
            session_title = f"LeMUR Pipeline Test - {audio_file_path.name}"
            
        logger.info("🎯 STARTING LEMUR FULL PIPELINE TEST")
        logger.info(f"📁 Audio file: {audio_file_path}")
        logger.info(f"📝 Session title: {session_title}")
        logger.info("=" * 60)
        
        try:
            # Step 1: Create session
            session_id = await self.create_session(session_title)
            
            # Step 2: Upload audio
            await self.upload_audio(session_id, audio_file_path)
            
            # Step 3: Start transcription
            await self.start_transcription(session_id)
            
            # Step 4: Wait for completion
            if not await self.wait_for_transcription_completion(session_id):
                raise RuntimeError("Transcription failed or timed out")
            
            # Step 5: Get original transcript
            original_segments = await self.get_original_transcript(session_id)
            
            # Step 6: Apply LeMUR optimizations
            speaker_result = await self.apply_lemur_speaker_identification(session_id, custom_speaker_prompt)
            punctuation_result = await self.apply_lemur_punctuation_optimization(session_id, custom_punctuation_prompt)
            
            # Step 7: Get optimized transcript
            optimized_segments = await self.get_optimized_transcript(session_id)
            
            # Step 8: Compare results
            comparison = self.compare_transcripts(original_segments, optimized_segments)
            
            # Final results
            results = {
                'session_id': session_id,
                'audio_file': str(audio_file_path),
                'session_title': session_title,
                'original_segment_count': len(original_segments),
                'optimized_segment_count': len(optimized_segments),
                'speaker_mapping': speaker_result.get('speaker_mapping', {}),
                'punctuation_improvements': punctuation_result.get('improvements_made', []),
                'comparison': comparison,
                'success': True
            }
            
            logger.info("🎉 FULL PIPELINE TEST COMPLETED SUCCESSFULLY!")
            logger.info(f"📊 Session ID: {session_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Pipeline test failed: {str(e)}")
            raise


async def main():
    parser = argparse.ArgumentParser(description="Test LeMUR full pipeline processing")
    parser.add_argument("--audio-file", required=True, help="Path to audio file")
    parser.add_argument("--auth-token", required=True, help="Authentication token")
    parser.add_argument("--session-title", help="Custom session title")
    parser.add_argument("--speaker-prompt", help="Custom speaker identification prompt")
    parser.add_argument("--punctuation-prompt", help="Custom punctuation optimization prompt")
    parser.add_argument("--api-url", default=API_BASE_URL, help="API base URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    audio_file = Path(args.audio_file)
    
    tester = LeMURPipelineTester(args.auth_token, args.api_url)
    
    try:
        results = await tester.run_full_pipeline_test(
            audio_file_path=audio_file,
            session_title=args.session_title,
            custom_speaker_prompt=args.speaker_prompt,
            custom_punctuation_prompt=args.punctuation_prompt
        )
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 Results saved to: {args.output}")
        else:
            print("\n" + "=" * 60)
            print("📋 FINAL RESULTS:")
            print("=" * 60)
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())