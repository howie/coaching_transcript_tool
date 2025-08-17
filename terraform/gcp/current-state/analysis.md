# Current GCP State Analysis

## Project Information
- **Project ID**: coachingassistant
- **Project Number**: 61531596587
- **Project Name**: CoachingAssistant
- **Organization ID**: 682717358496
- **Lifecycle State**: ACTIVE

## Service Accounts (Current)
1. **coachly@coachingassistant.iam.gserviceaccount.com**
   - Display Name: "coachly"
   - Status: Enabled
   - **Note**: This is NOT in our Terraform config

2. **coaching-storage@coachingassistant.iam.gserviceaccount.com** ✅
   - Display Name: "Coaching Assistant Storage Account"
   - Description: "Service account for audio file storage operations"
   - Status: Enabled
   - **Terraform Match**: YES - matches our config

## IAM Policy (Current)
Current bindings:
- `roles/logging.viewer` → coaching-storage@coachingassistant.iam.gserviceaccount.com
- `roles/owner` → howie@doxa.com.tw

**CRITICAL FINDING**: Missing required permissions!
- ❌ Missing `roles/speech.user` for Speech-to-Text API
- ❌ Missing `roles/storage.objectAdmin` for Cloud Storage
- ❌ Missing `roles/storage.legacyBucketWriter` for signed URLs

## Enabled APIs (Current)
Relevant APIs found:
- ✅ `speech.googleapis.com` - Speech-to-Text API
- ✅ `iam.googleapis.com` - IAM API  
- ✅ `serviceusage.googleapis.com` - Service Usage API
- ❌ Missing `storage-api.googleapis.com` - Cloud Storage API
- ❌ Missing `storage-component.googleapis.com` - Cloud Storage JSON API
- ❌ Missing `cloudresourcemanager.googleapis.com` - Cloud Resource Manager API

## Storage Buckets (Current)
- **Status**: Could not list buckets (permissions issue)
- **Expected**: Need audio and transcript storage buckets

## Comparison with Terraform Config

### ✅ Matches
- Project ID and basic info
- Service account `coaching-storage` exists
- Speech-to-Text API enabled

### ❌ Missing/Different
1. **IAM Permissions**: Critical permissions missing
2. **APIs**: Several required APIs not enabled
3. **Service Account**: Extra service account `coachly` exists
4. **Storage**: No buckets visible (may not exist)
5. **Custom IAM Role**: Not present

### 🔧 Action Required
1. Enable missing APIs
2. Add missing IAM permissions
3. Create storage buckets
4. Import existing service account to Terraform
5. Decide what to do with extra `coachly` service account

## Risk Assessment
- **HIGH**: Missing Speech-to-Text permissions explain 403 errors
- **HIGH**: Missing Storage APIs/permissions prevent file operations
- **LOW**: Extra service account (can be ignored or imported)