"""
LeMUR-based transcript smoothing service.

Uses AssemblyAI's LeMUR (Large Language Model) to intelligently improve transcript quality
by correcting speaker identification and adding proper punctuation, rather than using
rule-based heuristics.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import assemblyai as aai
from pydantic import BaseModel, Field

from ..core.config import settings

logger = logging.getLogger(__name__)


class TranscriptSegment(BaseModel):
    """A segment of transcript with speaker and text."""
    start: int = Field(description="Start time in milliseconds")
    end: int = Field(description="End time in milliseconds") 
    speaker: str = Field(description="Speaker identifier (e.g., 'A', 'B', '教練', '客戶')")
    text: str = Field(description="Transcript text for this segment")


class LeMURSmoothedTranscript(BaseModel):
    """Result of LeMUR-based transcript smoothing."""
    segments: List[TranscriptSegment] = Field(description="Improved transcript segments")
    speaker_mapping: Dict[str, str] = Field(description="Original to corrected speaker mapping")
    improvements_made: List[str] = Field(description="List of improvements applied")
    processing_notes: str = Field(description="Notes about the processing")


@dataclass
class SmoothingContext:
    """Context information for transcript smoothing."""
    session_language: str
    is_coaching_session: bool = True
    expected_speakers: List[str] = None
    audio_duration_minutes: Optional[float] = None

    def __post_init__(self):
        if self.expected_speakers is None:
            # Default expected speakers for coaching sessions
            if self.session_language.startswith('zh') or 'chinese' in self.session_language.lower():
                self.expected_speakers = ['教練', '客戶']
            else:
                self.expected_speakers = ['Coach', 'Client']


class LeMURTranscriptSmoother:
    """
    LeMUR-based transcript smoother using AssemblyAI's LLM capabilities.
    
    This service replaces rule-based heuristics with intelligent LLM processing
    to handle complex tasks like speaker identification and punctuation correction.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LeMUR transcript smoother."""
        self.api_key = api_key or settings.ASSEMBLYAI_API_KEY
        if not self.api_key:
            raise ValueError("AssemblyAI API key is required for LeMUR processing")
        
        # Set the global API key for assemblyai library
        aai.settings.api_key = self.api_key
        self.lemur = aai.Lemur()
        
    async def smooth_transcript(
        self,
        segments: List[Dict],
        context: SmoothingContext,
        custom_prompts: Optional[Dict[str, str]] = None
    ) -> LeMURSmoothedTranscript:
        """
        Smooth transcript using LeMUR for intelligent processing.
        
        Args:
            segments: Original transcript segments with speaker labels
            context: Context information for smoothing
            
        Returns:
            LeMURSmoothedTranscript with improved segments and metadata
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info(f"🧠 STARTING LEMUR-BASED TRANSCRIPT SMOOTHING")
        logger.info(f"⏰ START TIME: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        logger.info("=" * 80)
        logger.info(f"📊 INPUT SEGMENTS COUNT: {len(segments)}")
        logger.info(f"🌐 SESSION LANGUAGE: {context.session_language}")
        logger.info(f"🏫 IS COACHING SESSION: {context.is_coaching_session}")
        logger.info(f"🎯 CUSTOM PROMPTS PROVIDED: {custom_prompts is not None}")
        if custom_prompts:
            logger.info(f"📝 CUSTOM PROMPT KEYS: {list(custom_prompts.keys())}")
        logger.info("=" * 80)
        
        # Debug: Log input segments
        logger.info("📥 INPUT SEGMENTS:")
        for i, segment in enumerate(segments[:3]):  # Log first 3 segments as sample
            logger.info(f"  Segment {i}: Speaker={segment.get('speaker')}, "
                       f"Start={segment.get('start')}ms, End={segment.get('end')}ms, "
                       f"Text='{segment.get('text', '')[:100]}{'...' if len(segment.get('text', '')) > 100 else ''}'")
        if len(segments) > 3:
            logger.info(f"  ... and {len(segments) - 3} more segments")
        logger.info("=" * 80)
        
        try:
            # Convert segments to format suitable for LeMUR processing
            transcript_text = self._prepare_transcript_for_lemur(segments)
            logger.info(f"📝 PREPARED TRANSCRIPT TEXT FOR LEMUR:")
            logger.info(f"   Length: {len(transcript_text)} characters")
            logger.info(f"   First 500 chars: {transcript_text[:500]}...")
            logger.info("=" * 80)
            
            # Step 1: Correct speaker identification
            logger.info("🎭 Correcting speaker identification with LeMUR")
            speaker_corrections = await self._correct_speakers_with_lemur(
                transcript_text, context, custom_prompts
            )
            
            # Step 2: Add internal punctuation and improve structure (batch processing)
            logger.info("🔤 Adding punctuation and improving structure with LeMUR (batch processing)")
            improved_segments = await self._improve_punctuation_batch_with_lemur(
                segments, context, speaker_corrections, custom_prompts
            )
            
            result = LeMURSmoothedTranscript(
                segments=improved_segments,
                speaker_mapping=speaker_corrections,
                improvements_made=[
                    "Speaker identification corrected using LeMUR",
                    "Internal punctuation added within long segments", 
                    "Text structure and readability improved"
                ],
                processing_notes=f"Processed {len(segments)} segments using AssemblyAI LeMUR"
            )
            
            # Debug: Log final results
            end_time = time.time()
            processing_time = end_time - start_time
            logger.info("=" * 80)
            logger.info("✅ LEMUR-BASED TRANSCRIPT SMOOTHING COMPLETED")
            logger.info(f"⏰ END TIME: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
            logger.info(f"⏱️ TOTAL PROCESSING TIME: {processing_time:.2f} seconds")
            logger.info("=" * 80)
            logger.info(f"📊 FINAL RESULTS SUMMARY:")
            logger.info(f"   Input segments: {len(segments)}")
            logger.info(f"   Output segments: {len(improved_segments)}")
            logger.info(f"   Speaker mapping: {speaker_corrections}")
            logger.info(f"   Improvements made: {len(result.improvements_made)}")
            logger.info(f"   Processing time: {processing_time:.2f}s")
            logger.info("=" * 80)
            
            # Debug: Log sample output segments
            logger.info("📤 SAMPLE OUTPUT SEGMENTS:")
            for i, segment in enumerate(improved_segments[:3]):  # Log first 3 segments
                logger.info(f"  Segment {i}: Speaker='{segment.speaker}', "
                           f"Start={segment.start}ms, End={segment.end}ms, "
                           f"Text='{segment.text[:100]}{'...' if len(segment.text) > 100 else ''}'")
            if len(improved_segments) > 3:
                logger.info(f"  ... and {len(improved_segments) - 3} more segments")
            logger.info("=" * 80)
            
            logger.info("🎉 LeMUR-based transcript smoothing completed successfully!")
            return result
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            logger.error("=" * 80)
            logger.error("❌ LEMUR TRANSCRIPT SMOOTHING FAILED")
            logger.error(f"⏰ FAILURE TIME: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
            logger.error(f"⏱️ TIME BEFORE FAILURE: {processing_time:.2f} seconds")
            logger.error("=" * 80)
            logger.error(f"💥 ERROR TYPE: {type(e).__name__}")
            logger.error(f"💥 ERROR MESSAGE: {str(e)}")
            logger.error(f"📊 PROCESSING STATE:")
            logger.error(f"   Input segments: {len(segments)}")
            logger.error(f"   Custom prompts: {custom_prompts is not None}")
            logger.error(f"   Session language: {context.session_language}")
            logger.error("=" * 80)
            logger.exception("Full error traceback:")
            raise
    
    def _prepare_transcript_for_lemur(self, segments: List[Dict]) -> str:
        """Convert transcript segments to text format suitable for LeMUR."""
        text_parts = []
        
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            text = segment.get('text', '').strip()
            if text:
                text_parts.append(f"{speaker}: {text}")
        
        return '\n\n'.join(text_parts)
    
    async def _correct_speakers_with_lemur(
        self, 
        transcript_text: str, 
        context: SmoothingContext,
        custom_prompts: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Use LeMUR to correct speaker identification in coaching context."""
        
        # Use custom prompt if provided, otherwise use default
        if custom_prompts and custom_prompts.get('speakerPrompt'):
            custom_speaker_prompt = custom_prompts['speakerPrompt']
            logger.info("🎯 Using custom speaker identification prompt")
            prompt = f"""{custom_speaker_prompt}

逐字稿內容：
{transcript_text}"""
        elif context.is_coaching_session and context.session_language.startswith('zh'):
            # Chinese coaching session prompt
            prompt = f"""
你是一個專業的教練對話分析師。請分析以下教練對話逐字稿，並識別說話者身份。

這是一段教練(Coach)與客戶(Client)的對話。請判斷每個說話者是「教練」還是「客戶」。

教練的特徵：
- 會問開放性問題（如「你可以多說一點嗎？」「你覺得呢？」）
- 會引導對話方向和深入探索
- 會提供反饋、觀察和建議
- 語調通常比較引導性和支持性
- 會使用教練技巧如重述、澄清、挑戰

客戶的特徵：
- 主要分享自己的情況、感受和經歷
- 回答教練的問題和探索
- 尋求幫助、建議或解決方案
- 語調比較敘述性和個人化
- 會表達困惑、糾結或需要支持的狀況

逐字稿內容：
{transcript_text}

請回覆一個JSON格式的說話者對應表，將原始說話者標籤對應到正確的角色（使用繁體中文）：
例如：{{"A": "教練", "B": "客戶"}} 或 {{"Speaker A": "教練", "Speaker B": "客戶"}}

只回覆JSON，不要其他說明，請確保使用繁體中文。
"""
        else:
            # English coaching session prompt
            prompt = f"""
You are a professional coaching conversation analyst. Please analyze the following coaching transcript and identify the speakers.

This is a conversation between a Coach and a Client. Please determine which speaker is the "Coach" and which is the "Client".

Coach characteristics:
- Asks open-ended questions
- Guides conversation direction
- Provides feedback and suggestions
- Uses guiding tone

Client characteristics:
- Shares personal situations and feelings
- Responds to coach's questions
- Seeks help or advice
- Uses descriptive tone

Transcript:
{transcript_text}

Please respond with a JSON mapping of original speaker labels to correct roles:
Example: {{"A": "Coach", "B": "Client"}} or {{"Speaker A": "Coach", "Speaker B": "Client"}}

Respond with JSON only, no other explanation.
"""
        
        try:
            # Debug: Log the complete prompt being sent to LeMUR
            logger.info("=" * 80)
            logger.info("🔍 SPEAKER IDENTIFICATION PROMPT SENT TO LeMUR:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            logger.info(f"📝 INPUT TEXT LENGTH: {len(transcript_text)} characters")
            logger.info(f"🧠 MODEL: claude3_5_sonnet")
            
            # For speaker identification, we only need a small JSON response
            speaker_output_size = 1000  # Should be enough for speaker mapping JSON
            logger.info(f"📏 SPEAKER OUTPUT SIZE: {speaker_output_size} characters")
            logger.info("=" * 80)
            
            # Use LeMUR task endpoint for speaker identification
            speaker_start_time = time.time()
            result = await asyncio.to_thread(
                self.lemur.task,
                prompt,
                input_text=transcript_text,
                final_model=aai.LemurModel.claude3_5_sonnet,
                max_output_size=speaker_output_size
            )
            speaker_end_time = time.time()
            logger.info(f"⏱️ SPEAKER IDENTIFICATION TIME: {speaker_end_time - speaker_start_time:.2f} seconds")
            
            # Debug: Log the complete response from LeMUR
            logger.info("=" * 80)
            logger.info("📥 LEMUR SPEAKER IDENTIFICATION RESPONSE:")
            logger.info("=" * 80)
            logger.info(f"RAW RESPONSE: {result.response}")
            logger.info(f"RESPONSE TYPE: {type(result.response)}")
            logger.info(f"RESPONSE LENGTH: {len(result.response)} characters")
            logger.info("=" * 80)
            
            # Parse JSON response
            import json
            speaker_mapping = json.loads(result.response.strip())
            logger.info(f"🎭 PARSED SPEAKER MAPPING: {speaker_mapping}")
            logger.info(f"📊 MAPPING KEYS: {list(speaker_mapping.keys())}")
            logger.info(f"📊 MAPPING VALUES: {list(speaker_mapping.values())}")
            return speaker_mapping
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ SPEAKER IDENTIFICATION WITH LEMUR FAILED")
            logger.error("=" * 80)
            logger.error(f"💥 ERROR TYPE: {type(e).__name__}")
            logger.error(f"💥 ERROR MESSAGE: {str(e)}")
            logger.error(f"📝 INPUT TEXT LENGTH: {len(transcript_text)}")
            logger.error(f"🌐 SESSION LANGUAGE: {context.session_language}")
            logger.error(f"🎯 CUSTOM PROMPTS: {custom_prompts is not None}")
            logger.error("=" * 80)
            logger.exception("Full speaker identification error traceback:")
            logger.warning(f"⚠️ Falling back to empty speaker mapping")
            # Return empty mapping as fallback
            return {}
    
    async def _improve_punctuation_batch_with_lemur(
        self,
        segments: List[Dict],
        context: SmoothingContext,
        speaker_corrections: Dict[str, str],
        custom_prompts: Optional[Dict[str, str]] = None
    ) -> List[TranscriptSegment]:
        """Use LeMUR to improve punctuation by processing segments in batches."""
        
        logger.info("=" * 80)
        logger.info("🔤 STARTING BATCH PUNCTUATION IMPROVEMENT WITH LEMUR")
        logger.info("=" * 80)
        logger.info(f"📊 TOTAL SEGMENTS TO PROCESS: {len(segments)}")
        
        # Determine batch size based on content length
        # Adaptive batch sizing based on total content volume
        total_chars = sum(len(seg.get('text', '')) for seg in segments)
        
        if total_chars > 15000:
            # Large transcript: smaller batches for safety
            max_batch_chars = 2500
            max_batch_size = 8
        elif total_chars > 8000:
            # Medium transcript: balanced batches
            max_batch_chars = 3000
            max_batch_size = 10
        else:
            # Small transcript: larger batches for efficiency
            max_batch_chars = 4000
            max_batch_size = 15
            
        min_batch_size = 1  # At least 1 segment per batch
        
        logger.info(f"📏 ADAPTIVE BATCH SIZING: {total_chars} chars → max_batch_chars={max_batch_chars}, max_batch_size={max_batch_size}")
        
        batches = self._create_segment_batches(segments, max_batch_chars, min_batch_size, max_batch_size)
        logger.info(f"📦 CREATED {len(batches)} BATCHES FOR PROCESSING")
        
        improved_segments = []
        
        # Process batches with limited concurrency to avoid API rate limits
        max_concurrent_batches = min(3, len(batches))  # Max 3 concurrent requests
        
        if len(batches) > 1 and max_concurrent_batches > 1:
            logger.info(f"🚀 PROCESSING {len(batches)} BATCHES WITH {max_concurrent_batches} CONCURRENT WORKERS")
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(max_concurrent_batches)
            
            async def process_single_batch(batch_idx: int, batch: List[Dict]) -> Tuple[int, List[TranscriptSegment]]:
                async with semaphore:
                    logger.info(f"🔄 PROCESSING BATCH {batch_idx + 1}/{len(batches)} ({len(batch)} segments)")
                    
                    try:
                        batch_result = await self._process_punctuation_batch(
                            batch, context, speaker_corrections, custom_prompts, batch_idx + 1
                        )
                        logger.info(f"✅ BATCH {batch_idx + 1} COMPLETED: {len(batch_result)} segments processed")
                        return batch_idx, batch_result
                        
                    except Exception as e:
                        logger.error(f"❌ BATCH {batch_idx + 1} FAILED: {e}")
                        # Fallback: use original segments for this batch
                        fallback_segments = self._create_fallback_segments(batch, speaker_corrections)
                        logger.warning(f"⚠️ USING ORIGINAL SEGMENTS FOR BATCH {batch_idx + 1}")
                        return batch_idx, fallback_segments
            
            # Process all batches concurrently
            tasks = [process_single_batch(idx, batch) for idx, batch in enumerate(batches)]
            batch_results = await asyncio.gather(*tasks)
            
            # Sort results by original batch order and combine
            batch_results.sort(key=lambda x: x[0])  # Sort by batch index
            for _, batch_segments in batch_results:
                improved_segments.extend(batch_segments)
        else:
            # Sequential processing for single batch or when concurrency disabled
            logger.info(f"📚 PROCESSING {len(batches)} BATCHES SEQUENTIALLY")
            
            for batch_idx, batch in enumerate(batches):
                logger.info(f"🔄 PROCESSING BATCH {batch_idx + 1}/{len(batches)} ({len(batch)} segments)")
                
                try:
                    batch_result = await self._process_punctuation_batch(
                        batch, context, speaker_corrections, custom_prompts, batch_idx + 1
                    )
                    improved_segments.extend(batch_result)
                    logger.info(f"✅ BATCH {batch_idx + 1} COMPLETED: {len(batch_result)} segments processed")
                    
                except Exception as e:
                    logger.error(f"❌ BATCH {batch_idx + 1} FAILED: {e}")
                    # Fallback: use original segments for this batch
                    fallback_segments = self._create_fallback_segments(batch, speaker_corrections)
                    improved_segments.extend(fallback_segments)
                    logger.warning(f"⚠️ USING ORIGINAL SEGMENTS FOR BATCH {batch_idx + 1}")
        
        logger.info("=" * 80)
        logger.info(f"🎉 BATCH PUNCTUATION IMPROVEMENT COMPLETED")
        logger.info(f"📊 TOTAL PROCESSED SEGMENTS: {len(improved_segments)}")
        logger.info("=" * 80)
        
        return improved_segments
    
    def _create_segment_batches(
        self, 
        segments: List[Dict], 
        max_chars: int, 
        min_size: int, 
        max_size: int
    ) -> List[List[Dict]]:
        """Create batches of segments with character limits."""
        batches = []
        current_batch = []
        current_chars = 0
        
        for segment in segments:
            segment_text = segment.get('text', '')
            segment_chars = len(segment_text)
            
            # If adding this segment would exceed limits, start new batch
            if (current_batch and 
                (current_chars + segment_chars > max_chars or len(current_batch) >= max_size)):
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            
            current_batch.append(segment)
            current_chars += segment_chars
            
            # If single segment is too large, process it alone
            if segment_chars > max_chars and len(current_batch) == 1:
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
        
        # Add final batch
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    async def _process_punctuation_batch(
        self,
        batch: List[Dict],
        context: SmoothingContext,
        speaker_corrections: Dict[str, str],
        custom_prompts: Optional[Dict[str, str]],
        batch_num: int
    ) -> List[TranscriptSegment]:
        """Process a single batch of segments for punctuation improvement."""
        
        # Create batch text for LeMUR
        batch_text = self._prepare_batch_for_lemur(batch, speaker_corrections)
        batch_chars = len(batch_text)
        
        logger.info(f"📝 BATCH {batch_num} TEXT LENGTH: {batch_chars} characters")
        logger.debug(f"📝 BATCH {batch_num} CONTENT: {batch_text[:200]}...")
        
        # Build prompt for this batch
        if custom_prompts and custom_prompts.get('punctuationPrompt'):
            custom_punctuation_prompt = custom_prompts['punctuationPrompt']
            logger.info(f"🎯 BATCH {batch_num}: Using custom punctuation prompt")
            prompt = f"""{custom_punctuation_prompt}

說話者對應：{speaker_corrections}

請改善以下逐字稿：
{batch_text}"""
        elif context.session_language.startswith('zh'):
            # Use simplified Chinese prompt for batch processing
            prompt = f"""你是一個專業的繁體中文文本編輯師。請改善以下教練對話逐字稿的標點符號和斷句。

重要格式要求：
1. 必須使用繁體中文字（Traditional Chinese）輸出
2. 中文字之間不要加空格，保持中文連續書寫習慣
3. 保持說話者標籤和對話結構不變
4. 使用繁體中文全形標點符號（，。？！）

標點符號改善任務：
1. 在長段落內部添加適當的逗號、句號、問號、驚嘆號
2. 每個完整的思想或意思單元要用逗號分隔
3. 每個完整的句子要用句號結尾
4. 疑問句要用問號結尾
5. 轉折詞（但是、然後、所以、因為）前後要加逗號

說話者對應：{speaker_corrections}

請改善以下逐字稿：
{batch_text}

回覆改善後的逐字稿，嚴格保持相同格式（說話者: 內容），只改善標點符號，不要在中文字之間加空格。"""
        else:
            # English version
            prompt = f"""You are a professional English text editor. Please improve the punctuation of the following coaching transcript.

Format Requirements:
1. Maintain proper English spacing
2. Keep original speaker labels unchanged
3. Follow standard English punctuation rules

Improve the following transcript:
{batch_text}

Reply with improved transcript, maintaining the same format (Speaker: content)."""
        
        # Calculate output size for this batch
        estimated_output_size = max(1000, int(batch_chars * 1.3))  # 30% buffer
        
        try:
            # Process with LeMUR
            batch_start_time = time.time()
            result = await asyncio.to_thread(
                self.lemur.task,
                prompt,
                input_text=batch_text,
                final_model=aai.LemurModel.claude3_5_sonnet,
                max_output_size=estimated_output_size
            )
            batch_end_time = time.time()
            
            logger.info(f"⏱️ BATCH {batch_num} PROCESSING TIME: {batch_end_time - batch_start_time:.2f} seconds")
            logger.debug(f"📥 BATCH {batch_num} RESPONSE: {result.response[:200]}...")
            
            # Parse response and create segments
            improved_text = result.response.strip()
            
            # Apply Traditional Chinese conversion if needed
            if context.session_language.startswith('zh'):
                try:
                    from ..utils.chinese_converter import convert_to_traditional
                    improved_text = convert_to_traditional(improved_text)
                    logger.debug(f"✅ BATCH {batch_num}: Applied Traditional Chinese conversion")
                except ImportError:
                    logger.warning(f"⚠️ BATCH {batch_num}: Chinese converter not available")
            
            # Convert improved text back to segments
            return self._parse_batch_response_to_segments(improved_text, batch, speaker_corrections)
            
        except Exception as e:
            logger.error(f"❌ BATCH {batch_num} LEMUR PROCESSING FAILED: {e}")
            raise
    
    def _prepare_batch_for_lemur(self, batch: List[Dict], speaker_corrections: Dict[str, str]) -> str:
        """Prepare a batch of segments for LeMUR processing."""
        text_parts = []
        
        for segment in batch:
            original_speaker = segment.get('speaker', 'Unknown')
            corrected_speaker = speaker_corrections.get(original_speaker, original_speaker)
            text = segment.get('text', '').strip()
            
            if text:
                text_parts.append(f"{corrected_speaker}: {text}")
        
        return '\n\n'.join(text_parts)
    
    def _parse_batch_response_to_segments(
        self, 
        improved_text: str, 
        original_batch: List[Dict], 
        speaker_corrections: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Parse LeMUR batch response back to TranscriptSegment objects."""
        
        lines = improved_text.split('\n')
        improved_segments = []
        segment_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to parse speaker and text
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    text = parts[1].strip()
                    
                    # Get timing from original segment if available
                    if segment_index < len(original_batch):
                        original_segment = original_batch[segment_index]
                        start_time = int(round(original_segment.get('start', 0)))
                        end_time = int(round(original_segment.get('end', 0)))
                    else:
                        # Use last segment timing as fallback
                        start_time = 0
                        end_time = 0
                    
                    improved_segments.append(TranscriptSegment(
                        start=start_time,
                        end=end_time,
                        speaker=speaker,
                        text=text
                    ))
                    
                    segment_index += 1
        
        # If we have fewer improved segments than original, fill in the gaps
        while segment_index < len(original_batch):
            original_segment = original_batch[segment_index]
            speaker_raw = original_segment.get('speaker', 'Unknown')
            speaker_corrected = speaker_corrections.get(speaker_raw, speaker_raw)
            
            improved_segments.append(TranscriptSegment(
                start=int(round(original_segment.get('start', 0))),
                end=int(round(original_segment.get('end', 0))),
                speaker=speaker_corrected,
                text=original_segment.get('text', '')
            ))
            segment_index += 1
        
        return improved_segments
    
    def _create_fallback_segments(
        self, 
        batch: List[Dict], 
        speaker_corrections: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Create fallback segments when LeMUR processing fails."""
        fallback_segments = []
        
        for segment in batch:
            speaker_raw = segment.get('speaker', 'Unknown')
            speaker_corrected = speaker_corrections.get(speaker_raw, speaker_raw)
            
            fallback_segments.append(TranscriptSegment(
                start=int(round(segment.get('start', 0))),
                end=int(round(segment.get('end', 0))),
                speaker=speaker_corrected,
                text=segment.get('text', '')
            ))
        
        return fallback_segments
    
    async def _improve_punctuation_with_lemur(
        self,
        transcript_text: str,
        context: SmoothingContext, 
        speaker_corrections: Dict[str, str],
        custom_prompts: Optional[Dict[str, str]] = None
    ) -> str:
        """Use LeMUR to add internal punctuation and improve text structure."""
        
        # Use custom prompt if provided, otherwise use default
        if custom_prompts and custom_prompts.get('punctuationPrompt'):
            custom_punctuation_prompt = custom_prompts['punctuationPrompt']
            logger.info("🎯 Using custom punctuation improvement prompt")
            prompt = f"""{custom_punctuation_prompt}

說話者對應：{speaker_corrections}

請改善以下逐字稿：
{transcript_text}"""
        elif context.session_language.startswith('zh'):
            # Chinese punctuation improvement prompt
            prompt = f"""
你是一個專業的繁體中文文本編輯師。請改善以下教練對話逐字稿的標點符號和斷句。

重要格式要求：
1. 必須使用繁體中文字（Traditional Chinese）輸出
2. 中文字之間不要加空格，保持中文連續書寫習慣
3. 只在標點符號後面可以有空格（如果需要的話）
4. 保持說話者標籤和對話結構不變
5. 使用繁體中文全形標點符號（，。？！）

標點符號改善任務：
1. 在長段落內部添加適當的逗號、句號、問號、驚嘆號
2. 每個完整的思想或意思單元要用逗號分隔
3. 每個完整的句子要用句號結尾
4. 疑問句要用問號結尾
5. 感嘆或強調要用驚嘆號
6. 轉折詞（但是、然後、所以、因為）前後要加逗號
7. 列舉項目之間要用逗號分隔
8. 將所有簡體中文轉換為繁體中文

說話者對應：{speaker_corrections}

請改善以下逐字稿：
{transcript_text}

範例格式：
教練: 好，Lisha你好，我是你今天的教練，那我待會錄音，並且會做一些筆記，你OK嗎？

回覆改善後的逐字稿，嚴格保持相同格式（說話者: 內容），只改善標點符號，不要在中文字之間加空格，並確保使用繁體中文。
"""
        else:
            # English punctuation improvement prompt  
            prompt = f"""
You are a professional English text editor. Please improve the punctuation and sentence structure of the following coaching conversation transcript.

Format Requirements:
1. Maintain proper English spacing (spaces between words)
2. Keep original speaker labels and dialogue structure unchanged
3. Follow standard English punctuation rules

Punctuation Improvement Tasks:
1. Add appropriate punctuation within long paragraphs (periods, commas, question marks, exclamation marks)
2. Separate complete thoughts and ideas with commas
3. End complete sentences with periods
4. Use question marks for questions
5. Use exclamation marks for emphasis
6. Add commas before and after transition words (but, then, so, because)
7. Separate list items with commas

Speaker mapping: {speaker_corrections}

Please improve the following transcript:
{transcript_text}

Example format:
Coach: Good, Lisha hello, I am your coach today, so I will record later, and will take some notes, are you OK?

Reply with the improved transcript, maintaining the same format (Speaker: content), only improving punctuation.
"""
        
        try:
            # Debug: Log the complete prompt being sent to LeMUR
            logger.info("=" * 80)
            logger.info("🔍 PUNCTUATION IMPROVEMENT PROMPT SENT TO LeMUR:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            logger.info(f"📝 INPUT TEXT LENGTH: {len(transcript_text)} characters")
            logger.info(f"📝 SPEAKER CORRECTIONS: {speaker_corrections}")
            logger.info(f"🧠 MODEL: claude3_5_sonnet")
            logger.info("=" * 80)
            
            # Calculate appropriate output size based on input length
            estimated_output_size = max(4000, int(len(transcript_text) * 1.5))  # 50% buffer for punctuation
            logger.info(f"📏 ESTIMATED OUTPUT SIZE NEEDED: {estimated_output_size} characters")
            
            # Use LeMUR task endpoint for punctuation improvement
            punctuation_start_time = time.time()
            result = await asyncio.to_thread(
                self.lemur.task,
                prompt,
                input_text=transcript_text,
                final_model=aai.LemurModel.claude3_5_sonnet,
                max_output_size=estimated_output_size
            )
            punctuation_end_time = time.time()
            logger.info(f"⏱️ PUNCTUATION IMPROVEMENT TIME: {punctuation_end_time - punctuation_start_time:.2f} seconds")
            
            # Debug: Log the complete response from LeMUR
            logger.info("=" * 80)
            logger.info("📥 LEMUR PUNCTUATION IMPROVEMENT RESPONSE:")
            logger.info("=" * 80)
            logger.info(f"RAW RESPONSE: {result.response}")
            logger.info(f"RESPONSE TYPE: {type(result.response)}")
            logger.info(f"RESPONSE LENGTH: {len(result.response)} characters")
            logger.info("=" * 80)
            
            improved_text = result.response.strip()
            
            # Debug: Log text after initial processing
            logger.info(f"📝 STRIPPED RESPONSE LENGTH: {len(improved_text)} characters")
            
            # Ensure Traditional Chinese output for Chinese sessions
            if context.session_language.startswith('zh'):
                # Import Traditional Chinese converter
                try:
                    from ..utils.chinese_converter import convert_to_traditional
                    original_length = len(improved_text)
                    improved_text = convert_to_traditional(improved_text)
                    logger.info(f"✅ Applied Traditional Chinese conversion: {original_length} -> {len(improved_text)} chars")
                except ImportError:
                    logger.warning("⚠️ Chinese converter not available, using LeMUR output as-is")
            
            # Debug: Log final processed text
            logger.info("=" * 80)
            logger.info("📤 FINAL PUNCTUATION IMPROVED TEXT:")
            logger.info("=" * 80)
            logger.info(improved_text)
            logger.info("=" * 80)
            
            logger.info(f"🔤 LeMUR punctuation improvement completed successfully")
            return improved_text
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ PUNCTUATION IMPROVEMENT WITH LEMUR FAILED")
            logger.error("=" * 80)
            logger.error(f"💥 ERROR TYPE: {type(e).__name__}")
            logger.error(f"💥 ERROR MESSAGE: {str(e)}")
            logger.error(f"📝 INPUT TEXT LENGTH: {len(transcript_text)}")
            logger.error(f"📝 SPEAKER CORRECTIONS: {speaker_corrections}")
            logger.error(f"🌐 SESSION LANGUAGE: {context.session_language}")
            logger.error(f"🎯 CUSTOM PROMPTS: {custom_prompts is not None}")
            logger.error("=" * 80)
            logger.exception("Full punctuation improvement error traceback:")
            logger.warning(f"⚠️ Falling back to original transcript text")
            # Return original text as fallback
            return transcript_text
    
    def _parse_lemur_output_to_segments(
        self,
        improved_transcript: str,
        original_segments: List[Dict],
        speaker_corrections: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Parse LeMUR improved text back into transcript segments."""
        
        # Split improved transcript by lines and parse speaker segments
        lines = improved_transcript.split('\n')
        improved_segments = []
        
        # Create a mapping of original segment order
        segment_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to parse speaker and text
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker_raw = parts[0].strip()
                    text_improved = parts[1].strip()
                    
                    # Use corrected speaker if available
                    speaker_corrected = speaker_corrections.get(speaker_raw, speaker_raw)
                    
                    # Get timing from original segment if available
                    if segment_index < len(original_segments):
                        original_segment = original_segments[segment_index]
                        start_time = int(round(original_segment.get('start', 0)))
                        end_time = int(round(original_segment.get('end', 0)))
                    else:
                        # Use last segment timing as fallback
                        start_time = 0
                        end_time = 0
                    
                    improved_segments.append(TranscriptSegment(
                        start=start_time,
                        end=end_time,
                        speaker=speaker_corrected,
                        text=text_improved
                    ))
                    
                    segment_index += 1
        
        # If we have fewer improved segments than original, fill in the gaps
        while segment_index < len(original_segments):
            original_segment = original_segments[segment_index]
            speaker_raw = original_segment.get('speaker', 'Unknown')
            speaker_corrected = speaker_corrections.get(speaker_raw, speaker_raw)
            
            improved_segments.append(TranscriptSegment(
                start=int(round(original_segment.get('start', 0))),
                end=int(round(original_segment.get('end', 0))),
                speaker=speaker_corrected,
                text=original_segment.get('text', '')
            ))
            segment_index += 1
        
        logger.info(f"📊 Parsed {len(improved_segments)} improved segments from LeMUR output")
        return improved_segments


async def smooth_transcript_with_lemur(
    segments: List[Dict],
    session_language: str = "zh-TW",
    is_coaching_session: bool = True,
    custom_prompts: Optional[Dict[str, str]] = None
) -> LeMURSmoothedTranscript:
    """
    Convenience function to smooth transcript using LeMUR.
    
    Args:
        segments: Original transcript segments
        session_language: Language of the session  
        is_coaching_session: Whether this is a coaching session
        
    Returns:
        LeMURSmoothedTranscript with improved quality
    """
    smoother = LeMURTranscriptSmoother()
    context = SmoothingContext(
        session_language=session_language,
        is_coaching_session=is_coaching_session
    )
    
    return await smoother.smooth_transcript(segments, context, custom_prompts)