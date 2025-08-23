# LeMUR Testing Guide

This document describes the testing tools and scripts available for the LeMUR transcript optimization feature.

## Test Files Location

### Integration Tests
- **Location**: `/tests/integration/test_lemur_integration.py`
- **Purpose**: Comprehensive LeMUR functionality testing with sample coaching data
- **Type**: Integration test for LeMUR service

### Unit Tests
- **Location**: `/tests/unit/test_lemur_simple.py`
- **Purpose**: Simple LeMUR punctuation and Traditional Chinese testing
- **Type**: Unit test for core LeMUR functionality

### E2E Tests
- **Location**: `/tests/e2e/test_lemur_*.py`
- **Purpose**: End-to-end pipeline and database processing tests
- **Type**: End-to-end workflow validation

## Test Scripts Overview

### test_lemur_integration.py

**Purpose**: Comprehensive integration testing of LeMUR transcript smoothing

**Key Features**:
- Tests core LeMUR functionality with sample coaching dialogue
- Verifies speaker identification (教練 vs 客戶)
- Validates punctuation improvements
- Tests API endpoint integration (optional)
- Comprehensive result validation

**Sample Test Data**:
```python
SAMPLE_TRANSCRIPT_DATA = [
    {
        "start": 1000,
        "end": 3500,
        "speaker": "A",
        "text": "你好我想要問一下關於這個問題"
    },
    # ... more coaching dialogue segments
]
```

**Test Functions**:
- `test_lemur_integration()` - Core LeMUR service testing
- `test_api_endpoint()` - API endpoint validation (requires running server)
- `main()` - Complete test suite execution

### test_lemur_simple.py

**Purpose**: Simple focused testing of LeMUR improvements

**Key Features**:
- Tests improved LeMUR prompts
- Validates Traditional Chinese output
- Checks punctuation quality
- Verifies speaker mapping
- Quality assurance checks

**Quality Checks**:
```python
# Automated validation
has_punctuation = any('，' in seg.text or '。' in seg.text for seg in result.segments)
no_extra_spaces = all('我 是' not in seg.text for seg in result.segments)
has_traditional = any('學' in seg.text or '們' in seg.text for seg in result.segments)
no_simplified = all('学' not in seg.text for seg in result.segments)
```

## Usage Instructions

### Prerequisites

```bash
# Install dependencies
pip install -r tests/e2e/requirements.txt

# Set AssemblyAI API key
export ASSEMBLYAI_API_KEY="your_api_key_here"
```

### Running Integration Tests

```bash
# Comprehensive LeMUR integration test
cd tests/integration
python test_lemur_integration.py
```

**Expected Output**:
- ✅ API key validation
- 📝 Sample data processing
- 🧠 LeMUR smoothing execution
- 🎭 Speaker mapping results
- 📊 Processed segment display
- 🎉 Success/failure summary

### Running Unit Tests

```bash
# Simple LeMUR functionality test
cd tests/unit
python test_lemur_simple.py
```

**Expected Output**:
- 🧪 Input/output text comparison
- ✓ Quality check results
- 🎉 Success/improvement recommendations

### Running E2E Tests

```bash
# Full pipeline test
cd tests/e2e
python test_lemur_full_pipeline.py --audio-file /path/to/audio.mp3 --auth-token $TOKEN

# Database processing test
python test_lemur_database_processing.py --list-sessions --auth-token $TOKEN
```

## Test Coverage

### Integration Test Coverage
- ✅ LeMUR service initialization
- ✅ Sample data processing
- ✅ Speaker identification accuracy
- ✅ Punctuation improvement validation
- ✅ API endpoint integration (optional)
- ✅ Result structure validation

### Unit Test Coverage
- ✅ Traditional Chinese character preservation
- ✅ Punctuation quality improvements
- ✅ Space handling in Chinese text
- ✅ Speaker mapping functionality
- ✅ Quality assurance metrics

### E2E Test Coverage
- ✅ Complete audio → transcript → LeMUR pipeline
- ✅ Database session processing
- ✅ Custom prompt integration
- ✅ Batch processing capabilities

## Success Criteria

### For test_lemur_integration.py
- ✓ Segments processed successfully (count > 0)
- ✓ Speaker mapping applied (mapping exists)
- ✓ Improvements documented (improvements_made not empty)
- ✓ Coaching context recognized (教練/客戶 speakers identified)

### For test_lemur_simple.py
- ✓ Has punctuation (，。？ characters present)
- ✓ No extra spaces in Chinese text
- ✓ Speaker mapping exists
- ✓ Traditional Chinese preserved (學們會 not 学们会)

## Troubleshooting

### Common Issues

**❌ ASSEMBLYAI_API_KEY not found**
```bash
export ASSEMBLYAI_API_KEY="your_actual_api_key"
```

**❌ Import error - module not found**
```bash
pip install -r requirements.txt
# Ensure you're in the correct directory with src/ path
```

**❌ API endpoint not available**
- Expected when server is not running
- Integration test will still pass if core functionality works

### Quality Issues

**⚠️ Poor punctuation quality**
- Check if Traditional Chinese is properly detected
- Verify coaching context in prompts
- Consider custom prompt adjustments

**⚠️ Incorrect speaker mapping**
- Verify coaching dialogue context in test data
- Check if speaker roles are clearly distinguishable
- Consider prompt engineering improvements

## Custom Prompt Testing

### Using Custom Prompts
```bash
# Test with custom speaker prompt
python test_lemur_integration.py --speaker-prompt "你的自訂說話者提示詞"

# Test with custom punctuation prompt  
python test_lemur_simple.py --punctuation-prompt "你的自訂標點符號提示詞"
```

### Prompt Examples
Reference: `/tests/e2e/lemur_examples/sample_custom_prompts.py`

- **BASIC_COACH_CLIENT** - Basic coaching dialogue identification
- **DETAILED_PUNCTUATION** - Comprehensive punctuation improvement
- **CHINESE_DIALOGUE** - Chinese-specific punctuation handling
- **COMPREHENSIVE_PROCESSING** - Combined speaker + punctuation optimization

## Integration with Main System

### Environment Configuration
```env
# Required for LeMUR testing
ASSEMBLYAI_API_KEY=your_api_key_here
STT_PROVIDER=assemblyai
```

### API Endpoints Tested
- `POST /lemur-speaker-identification` - Speaker optimization
- `POST /lemur-punctuation-optimization` - Punctuation optimization
- `POST /session/{session_id}/lemur-speaker-identification` - Database-based speaker optimization
- `POST /session/{session_id}/lemur-punctuation-optimization` - Database-based punctuation optimization

## References

- **LeMUR Feature Implementation**: `@src/coaching_assistant/services/lemur_transcript_smoother.py`
- **API Endpoints**: `@src/coaching_assistant/api/transcript_smoothing.py`
- **Custom Prompts**: `@tests/e2e/lemur_examples/sample_custom_prompts.py`
- **Main Feature Documentation**: `@docs/features/improve-assembly-with-lemur/README.md`
- **Session ID Mapping**: `@docs/claude/session-id-mapping.md`