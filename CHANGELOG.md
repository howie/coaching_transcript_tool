# Changelog

All notable changes to the Coaching Assistant Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.0] - 2025-08-12

### ✨ Added
- **Intelligent Speaker Diarization**: Advanced speaker separation with automatic fallback mechanisms
- **Segment-level Role Assignment**: Individual editing of speaker roles for each transcript segment
- **Dual API Support**: Smart selection between `recognize` API (with diarization) and `batchRecognize` API (fallback)
- **Multi-language Optimization**: Language-specific model and region selection
- **New API Endpoint**: `PATCH /sessions/{id}/segment-roles` for granular role management
- **Enhanced Export Formats**: All export formats now include segment-level role information

### 🔧 Enhanced
- **Google STT v2 Integration**: Full support for latest Speech-to-Text API features
- **Error Resilience**: Graceful degradation when diarization is not supported
- **Configuration Validation**: Automatic detection of optimal settings per language/region
- **Real-time Statistics**: Live updates of speaking time distribution in frontend
- **Database Schema**: New `SegmentRole` table for per-segment speaker assignments

### 🐛 Fixed
- **Configuration Errors**: Resolved "Recognizer does not support feature: speaker_diarization" errors
- **Regional Compatibility**: Proper handling of diarization limitations across different Google Cloud regions
- **Model Selection**: Improved model matching for different languages
- **Frontend State Management**: Fixed issues with role editing state persistence

### 🏗️ Technical Details
- **New Environment Variables**:
  - `ENABLE_SPEAKER_DIARIZATION=true`
  - `MAX_SPEAKERS=2`
  - `MIN_SPEAKERS=2`
  - `USE_STREAMING_FOR_DIARIZATION=false`
- **Database Migration**: `2961da1deaa6_add_segment_level_role_assignments.py`
- **Language Support Matrix**: Documented diarization capabilities per language/region combination

### 📊 Language Support Matrix

| Language | Region | Diarization | Method |
|----------|--------|-------------|--------|
| English (en-US) | us-central1 | ✅ Automatic | recognize API |
| English (en-US) | asia-southeast1 | ❌ Manual | batchRecognize + manual editing |
| Chinese (cmn-Hant-TW) | asia-southeast1 | ❌ Manual | batchRecognize + manual editing |
| Japanese (ja) | asia-southeast1 | ❌ Manual | batchRecognize + manual editing |
| Korean (ko) | asia-southeast1 | ❌ Manual | batchRecognize + manual editing |

### 🎯 Usage Notes
- **For English coaching sessions**: Consider using `GOOGLE_STT_LOCATION=us-central1` for optimal automatic diarization
- **For Chinese/Asian language sessions**: Current `asia-southeast1` configuration provides excellent transcription quality with manual role assignment capabilities
- **Hybrid approach**: System automatically detects capabilities and provides the best available method for each language

### 📚 Documentation Updates
- Updated `CLAUDE.md` with comprehensive diarization configuration guide
- Added `docs/speaker-diarization-improvements.md` with technical implementation details
- Enhanced `README.md` with configuration examples and usage guidelines

---

## [2.6.0] - Previous Release
- Previous features and improvements...

---

## Contributing

When adding entries to this changelog:
1. Use the categories: Added, Changed, Deprecated, Removed, Fixed, Security
2. Include relevant technical details for developers
3. Provide configuration examples for new features
4. Document any breaking changes clearly