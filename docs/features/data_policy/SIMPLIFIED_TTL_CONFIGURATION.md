# Simplified TTL Configuration & Data Retention Policies

**Last Updated**: 2025-09-18
**Architecture Version**: Simplified Storage (Post WP6-Storage-Simplification)
**Status**: ✅ Active & Operational

## 📊 Overview

This document records the **simplified** Time-To-Live (TTL) configurations following the storage bucket simplification implementation. The new architecture consolidates all storage under a single audio bucket while maintaining comprehensive data governance.

## 🏗️ Architectural Change Summary

### Before: Complex Multi-Bucket Architecture
```
├── coaching-audio-dev/          # Audio files (5 files)
├── coaching-transcript-dev/     # Empty
├── coaching-audio-prod/         # Empty
├── coaching-transcript-prod/    # Empty
├── coaching-audio-prod-asia/    # Empty
├── coaching-transcript-prod-asia/ # Empty
└── coaching-transcript-terraform-state/ # State management
```

### After: Simplified Single-Purpose Architecture
```
├── coaching-audio-dev/
│   ├── audio-uploads/           # Original audio files (TTL: 1 day)
│   └── batch-results/           # STT temporary results (TTL: 1 day)
├── coaching-audio-prod-asia/
│   ├── audio-uploads/           # Original audio files (TTL: 1 day)
│   └── batch-results/           # STT temporary results (TTL: 1 day)
└── PostgreSQL Database          # All transcript data (permanent)
```

## 🪣 Simplified Storage Configuration

### Audio Storage Buckets (Unified Purpose)

| Bucket Name | Region | TTL Policy | Contents | File Count |
|------------|--------|------------|----------|------------|
| `coaching-audio-dev` | US-CENTRAL1 | **1 day auto-delete** | Audio files + STT results | 5 files |
| `coaching-audio-prod-asia` | ASIA-SOUTHEAST1 | **1 day auto-delete** | Audio files + STT results | 0 files |

**Unified Lifecycle Policy:**
```yaml
lifecycle_config:
  rule:
  - action:
      type: Delete
    condition:
      age: 1  # All files deleted after 1 day
```

### Database Storage (Permanent)

| Data Type | Storage Location | Retention Policy | Purpose |
|-----------|------------------|------------------|---------|
| Transcript Segments | PostgreSQL `transcript_segment` | Permanent | User access & analysis |
| Session Metadata | PostgreSQL `session` | Permanent | Session management |
| User Data | PostgreSQL `user` | Permanent | Account management |
| Usage Analytics | PostgreSQL `usage_log` | Permanent | Business intelligence |

## 📋 Data Flow (Simplified)

### 1. Audio Processing Flow
```
User Upload → audio-uploads/{user_id}/{session_id}.{ext}
     ↓
STT Processing → batch-results/{uuid}/ (temporary)
     ↓
Transcript Data → PostgreSQL Database (permanent)
     ↓
File Cleanup → TTL removes all GCS files after 1 day
```

### 2. Storage Lifecycle
1. **Upload**: Audio files stored in `audio-uploads/` folder
2. **Processing**: STT results temporarily stored in `batch-results/` folder
3. **Extraction**: Transcript segments extracted to database
4. **Cleanup**: All GCS files automatically deleted after 24 hours
5. **Access**: Users access transcripts from database only

## 🔧 Configuration Details

### Environment Variables (Simplified)
```bash
# Before (Complex)
AUDIO_STORAGE_BUCKET=coaching-audio-dev-asia
TRANSCRIPT_STORAGE_BUCKET=coaching-transcript-dev-asia

# After (Simplified)
AUDIO_STORAGE_BUCKET=coaching-audio-dev  # Handles both audio & STT results
# TRANSCRIPT_STORAGE_BUCKET removed - not needed
```

### Application Configuration
- **Google STT Service**: Uses `AUDIO_STORAGE_BUCKET` for batch results
- **File Upload**: Uses `AUDIO_STORAGE_BUCKET/audio-uploads/` folder
- **Transcript Storage**: PostgreSQL database only
- **Environment Validation**: Only validates `AUDIO_STORAGE_BUCKET`

## 📈 Benefits Achieved

### Infrastructure Simplification
- **Bucket Reduction**: 7 buckets → 2 buckets (-71%)
- **Configuration Variables**: Removed `TRANSCRIPT_STORAGE_BUCKET`
- **IAM Complexity**: Simplified permission management
- **Terraform Resources**: Removed 5 unused bucket definitions

### Operational Benefits
- **Unified TTL Management**: Single lifecycle policy for all GCS data
- **Simplified Monitoring**: Monitor only 2 buckets instead of 7
- **Cost Optimization**: Eliminated unused bucket costs
- **Maintenance Reduction**: Single bucket management workflow

### Compliance & Security
- **GDPR Compliance**: Maintained through aggressive 1-day TTL
- **Data Minimization**: No change - still automatic file deletion
- **Security**: Reduced attack surface through fewer storage endpoints
- **Audit Trail**: Simplified logging and monitoring

## 🔍 Current Status (Verified 2025-09-18)

### Production Buckets
- **coaching-audio-prod-asia**: 0 files ✅ (TTL working)
- **coaching-audio-dev**: 5 files ✅ (recent test uploads)

### Database Status
- **transcript_segment**: All transcript data stored here ✅
- **session**: Session metadata linked to transcript segments ✅
- **user**: User data properly maintained ✅

### Configuration Status
- **Application**: Uses simplified `AUDIO_STORAGE_BUCKET` only ✅
- **Terraform**: Removed all transcript bucket infrastructure ✅
- **Environment**: Updated all deployment configurations ✅

## 📊 Monitoring & Verification

### Weekly Monitoring Checklist
- [ ] Verify TTL policies functioning (expect low file counts)
- [ ] Check transcript data integrity in database
- [ ] Monitor storage costs (should be reduced)
- [ ] Validate simplified configuration deployment

### Key Metrics to Track
- **File Count**: Should remain low due to 1-day TTL
- **Storage Cost**: Should decrease due to bucket consolidation
- **Application Performance**: Should be unaffected
- **User Experience**: Should be identical to before

## 🚨 Important Notes

### Critical Success Factors
1. **Zero Functional Impact**: All user-facing features work identically
2. **No Data Loss**: Transcript data safely stored in database
3. **Cost Optimization**: Immediate infrastructure cost reduction
4. **Simplified Operations**: Easier monitoring and maintenance

### Migration Safety
- ✅ **No Breaking Changes**: All existing workflows preserved
- ✅ **Backward Compatibility**: Legacy configurations still work
- ✅ **Rollback Ready**: Can revert if necessary
- ✅ **Data Integrity**: No transcript data affected

## 🔄 Related Documentation

- [Storage Simplification Changes](../../STORAGE_SIMPLIFICATION_CHANGES.md) - Complete implementation details
- [Terraform README](../../../terraform/README.md) - Updated infrastructure documentation
- [Data Policy README](./README.md) - Overall data governance framework

---

**Conclusion**: The storage simplification successfully reduces infrastructure complexity by 71% while maintaining full functionality and improving operational efficiency. The new unified bucket approach simplifies data lifecycle management without compromising compliance or user experience.