# Speaker Role Analysis - Future Work

## Overview

This document outlines future improvements for the speaker role assignment system in coaching conversations. Currently, the system uses a simple speaking ratio approach, but there are opportunities for more sophisticated analysis.

## Current Implementation (August 2025)

### Simple Role Assignment (`SimpleRoleAssigner`)
- **Location**: `packages/core-logic/src/coaching_assistant/utils/simple_role_assigner.py`
- **Method**: Speaking time and word count ratios
- **Core Assumption**: Clients speak more than coaches in coaching conversations
- **Confidence**: Based on ratio differences (30%+ difference = 90% confidence)

### Performance
- Works well for clear coach-client conversations
- Simple, fast, and reliable
- Avoids complex pattern matching that can fail

## Future Enhancement Opportunities

### 1. NLP-Based Analysis

#### Option A: Traditional NLP Libraries
```python
# Using spaCy or NLTK for linguistic analysis
import spacy
from collections import Counter

def analyze_linguistic_patterns(segments):
    nlp = spacy.load("zh_core_web_sm")  # Chinese model
    
    features = {}
    for segment in segments:
        doc = nlp(segment.content)
        
        # Extract linguistic features
        features[segment.speaker_id] = {
            'question_count': len([sent for sent in doc.sents if sent.text.endswith('？')]),
            'sentence_types': analyze_sentence_types(doc),
            'named_entities': len(doc.ents),
            'pos_patterns': Counter([token.pos_ for token in doc]),
            'dependency_patterns': analyze_dependencies(doc)
        }
    
    return classify_speakers(features)
```

**Benefits:**
- More accurate question detection
- Sentence type analysis (questions vs statements)
- Named entity recognition (personal vs professional topics)
- Grammatical pattern analysis

**Challenges:**
- Requires language-specific models
- More complex setup and dependencies
- Performance overhead

#### Option B: Question Pattern Recognition
```python
# Enhanced question detection patterns
ADVANCED_QUESTION_PATTERNS = {
    'zh': {
        'direct_questions': [
            r'.*[？]$',  # Direct question marks
            r'.*(什麼|怎麼|為什麼|哪裡|誰|何時|如何).*',
        ],
        'coaching_questions': [
            r'.*(感覺如何|有什麼想法|你覺得|你認為).*',
            r'.*(如果|假設|想像一下).*會怎樣',
            r'.*(最重要的是|對你來說).*',
        ],
        'clarification': [
            r'.*(能否|可以|可不可以).*說明',
            r'.*(我想了解|幫我理解).*',
        ],
        'empowerment': [
            r'.*(你想要|你希望|你的目標).*',
            r'.*(下一步|接下來|你會).*',
        ]
    }
}
```

### 2. LLM-Based Semantic Analysis

#### Option A: Local LLM Integration
```python
# Using a local language model for role detection
from transformers import pipeline

class LLMRoleAnalyzer:
    def __init__(self):
        self.classifier = pipeline(
            "text-classification",
            model="hfl/chinese-bert-wwm-ext",
            tokenizer="hfl/chinese-bert-wwm-ext"
        )
    
    def analyze_segment(self, segment_text):
        # Classify each segment as coach-like or client-like
        result = self.classifier(segment_text)
        return {
            'role_probability': result[0]['score'],
            'predicted_role': result[0]['label'],
            'semantic_features': self.extract_features(segment_text)
        }
```

**Benefits:**
- Deep semantic understanding
- Context-aware analysis
- Can learn coaching-specific patterns

**Challenges:**
- Requires significant computational resources
- Model training/fine-tuning needed
- Privacy considerations for cloud LLMs

#### Option B: Cloud LLM API Integration
```python
# Using OpenAI/Claude API for analysis
async def analyze_conversation_with_llm(segments):
    prompt = f"""
    Analyze this coaching conversation and determine which speaker is the coach and which is the client.
    
    Conversation segments:
    {format_segments_for_llm(segments)}
    
    Return your analysis in JSON format with:
    - speaker_roles: {{speaker_id: "coach"|"client"}}
    - confidence: 0.0-1.0
    - reasoning: explanation of your decision
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return parse_llm_response(response)
```

### 3. Conversation Flow Analysis

#### Turn-Taking Patterns
```python
def analyze_turn_taking(segments):
    """Analyze conversation dynamics."""
    patterns = {
        'interruptions': count_interruptions(segments),
        'response_times': calculate_response_intervals(segments),
        'initiative_taking': count_topic_initiations(segments),
        'follow_up_questions': count_follow_ups(segments)
    }
    
    # Coaches typically:
    # - Ask more follow-up questions
    # - Take initiative in guiding conversation
    # - Have shorter speaking turns
    return classify_by_patterns(patterns)
```

#### Sentiment and Emotional Flow
```python
from textblob import TextBlob

def analyze_emotional_patterns(segments):
    """Analyze emotional content and flow."""
    for segment in segments:
        sentiment = TextBlob(segment.content).sentiment
        
        # Coaches might show:
        # - More neutral sentiment (professional distance)
        # - Encouraging/supportive language
        # Clients might show:
        # - More emotional variability
        # - Personal/vulnerable content
```

### 4. Multi-Modal Analysis

#### Audio Feature Integration
```python
def analyze_audio_features(audio_segments):
    """Extract paralinguistic features from audio."""
    features = {}
    
    for segment in audio_segments:
        # Extract audio features that might indicate role
        features[segment.speaker_id] = {
            'speaking_rate': calculate_wpm(segment),
            'pitch_variation': analyze_prosody(segment),
            'pause_patterns': analyze_pauses(segment),
            'volume_dynamics': analyze_volume(segment)
        }
    
    # Coaches might have:
    # - More consistent speaking patterns
    # - Strategic use of pauses
    # - Calmer vocal tone
    return features
```

## Implementation Roadmap

### Phase 1: Enhanced Pattern Recognition (Short-term)
- [ ] Implement advanced question pattern detection
- [ ] Add coaching-specific language patterns
- [ ] Improve confidence scoring based on multiple factors

### Phase 2: NLP Integration (Medium-term)
- [ ] Integrate spaCy for Chinese text analysis
- [ ] Implement sentence type classification
- [ ] Add named entity recognition for context

### Phase 3: LLM Integration (Long-term)
- [ ] Evaluate local vs cloud LLM options
- [ ] Implement privacy-preserving analysis
- [ ] Fine-tune models on coaching conversation data

### Phase 4: Multi-Modal Analysis (Future)
- [ ] Integrate audio feature analysis
- [ ] Combine text and audio signals
- [ ] Real-time conversation analysis

## Technical Considerations

### Performance Requirements
- Real-time analysis for live sessions
- Batch processing for recorded sessions
- Minimal impact on transcription speed

### Privacy and Security
- Local processing for sensitive conversations
- Encrypted data handling for cloud services
- Compliance with coaching ethics and regulations

### Scalability
- Support for multiple languages
- Handling of group coaching sessions
- Integration with existing STT pipeline

### Quality Metrics
- Accuracy benchmarking against human annotations
- False positive/negative rate tracking
- User feedback integration

## Research Questions

1. **Linguistic Patterns**: What linguistic markers most reliably distinguish coaches from clients across different coaching styles?

2. **Cultural Variations**: How do role indicators vary across different cultural contexts and languages?

3. **Session Types**: How do patterns differ between initial sessions, regular sessions, and crisis interventions?

4. **Individual Differences**: How can the system adapt to different coaching styles and client personalities?

## Success Metrics

### Accuracy Targets
- 95% accuracy for clear coach-client conversations
- 85% accuracy for complex multi-party sessions
- <5% false positive rate for role misassignment

### Performance Targets
- <2 seconds additional processing time per session
- Memory usage <100MB for analysis models
- Real-time analysis capability for live sessions

## Conclusion

The current simple role assignment system provides a solid foundation, but there are significant opportunities for improvement through advanced NLP and AI techniques. The roadmap prioritizes practical enhancements while building toward more sophisticated analysis capabilities.

Future implementations should balance accuracy improvements with system complexity, ensuring that enhancements provide clear value to users while maintaining the reliability and simplicity of the current approach.