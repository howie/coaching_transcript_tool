# GCS Storage Monitor Workflow Pattern 📋 PLANNED

**Status**: Workflow Pattern (Not an Invokable Agent)
**Type**: Manual Process Following Best Practices

## Overview

This document outlines a systematic approach to monitoring Google Cloud Storage usage, particularly for audio file uploads in the Coaching Transcript Tool. Follow this workflow to analyze storage consumption, track file uploads, and optimize storage costs.

## Purpose

Provide a structured process for:
- **Storage monitoring** - Track bucket usage and file upload patterns
- **Cost optimization** - Identify storage inefficiencies and costs
- **Usage analytics** - Understand user behavior and system performance
- **Capacity planning** - Predict storage needs and scale accordingly
- **Compliance tracking** - Monitor file lifecycle and deletion policies

## When to Use This Pattern

### ✅ Ideal Scenarios
- **Monthly storage reviews** - Regular assessment of storage usage
- **Cost optimization initiatives** - Reducing storage-related expenses
- **System performance analysis** - Understanding upload patterns and bottlenecks
- **Compliance audits** - Verifying file retention and deletion policies
- **Capacity planning** - Forecasting storage requirements

### ✅ Monitoring Scenarios
- Audio file upload volume tracking
- Storage cost analysis
- File lifecycle management
- Regional storage distribution
- User upload behavior patterns

## Prerequisites

### Required Tools
- Google Cloud CLI (`gcloud`) installed and configured
- Appropriate IAM permissions for GCS monitoring
- Access to the coaching transcript tool's GCS buckets
- Optional: `gsutil` for advanced operations

### Required Permissions
- `storage.objects.list` - List bucket contents
- `storage.buckets.get` - Get bucket metadata
- `monitoring.metricDescriptors.list` - Access Cloud Monitoring metrics
- `monitoring.timeSeries.list` - Query monitoring data

## Step-by-Step Workflow

### Phase 1: Environment Setup (5 minutes)

1. **Authenticate with Google Cloud**
   ```bash
   # Login to Google Cloud
   gcloud auth login

   # Set the project (replace with actual project ID)
   gcloud config set project coaching-transcript-tool

   # Verify authentication
   gcloud auth list
   ```

2. **Verify Bucket Access**
   ```bash
   # List all storage buckets in the project
   gcloud storage buckets list

   # Check specific bucket (replace with actual bucket name)
   gcloud storage ls gs://coaching-transcript-audio-uploads
   ```

### Phase 2: Storage Usage Analysis (10-15 minutes)

1. **Bucket Overview**
   ```bash
   # Get bucket details and configuration
   gcloud storage buckets describe gs://coaching-transcript-audio-uploads

   # Check bucket size and object count
   gcloud storage du gs://coaching-transcript-audio-uploads
   ```

2. **File Inventory**
   ```bash
   # List all files with details (size, date, type)
   gcloud storage ls -l -h gs://coaching-transcript-audio-uploads/**

   # Count files by date (last 7 days)
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk -v cutoff_date="$(date -d '7 days ago' '+%Y-%m-%d')" \
   '$2 >= cutoff_date {count++} END {print "Files uploaded in last 7 days: " count}'

   # List largest files (top 20)
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   sort -k1 -hr | head -20
   ```

3. **Storage Metrics by File Type**
   ```bash
   # Count and size by file extension
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk '{
     if ($1 ~ /^[0-9]+$/) {
       ext = substr($3, index($3, "."))
       count[ext]++
       size[ext] += $1
     }
   } END {
     for (e in count) {
       printf "Extension: %s, Count: %d, Total Size: %.2f MB\n",
              e, count[e], size[e]/1024/1024
     }
   }'
   ```

### Phase 3: Time-Based Analysis (10 minutes)

1. **Upload Pattern Analysis**
   ```bash
   # Files uploaded by month
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk '{
     if ($1 ~ /^[0-9]+$/) {
       month = substr($2, 1, 7)  # YYYY-MM format
       count[month]++
       size[month] += $1
     }
   } END {
     for (m in count) {
       printf "Month: %s, Uploads: %d, Size: %.2f GB\n",
              m, count[m], size[m]/1024/1024/1024
     }
   }' | sort
   ```

2. **Recent Activity Analysis**
   ```bash
   # Files uploaded today
   TODAY=$(date '+%Y-%m-%d')
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   grep "^[0-9].*$TODAY" | wc -l

   # Files uploaded this week
   WEEK_AGO=$(date -d '7 days ago' '+%Y-%m-%d')
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk -v cutoff="$WEEK_AGO" '$2 >= cutoff {count++; size+=$1}
        END {printf "This week: %d files, %.2f MB\n", count, size/1024/1024}'
   ```

### Phase 4: Cost and Lifecycle Analysis (10 minutes)

1. **Storage Class Distribution**
   ```bash
   # Check storage classes used
   gcloud storage ls -L gs://coaching-transcript-audio-uploads/** | \
   grep "Storage class:" | sort | uniq -c
   ```

2. **Lifecycle Policy Status**
   ```bash
   # Check bucket lifecycle configuration
   gcloud storage buckets describe gs://coaching-transcript-audio-uploads \
   --format="value(lifecycle)"
   ```

3. **File Age Analysis for Cleanup**
   ```bash
   # Files older than 30 days (candidates for deletion)
   THIRTY_DAYS_AGO=$(date -d '30 days ago' '+%Y-%m-%d')
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk -v cutoff="$THIRTY_DAYS_AGO" '$2 < cutoff {count++; size+=$1}
        END {printf "Files older than 30 days: %d files, %.2f GB\n", count, size/1024/1024/1024}'
   ```

### Phase 5: Report Generation (5 minutes)

1. **Create Summary Report**
   ```bash
   # Generate comprehensive report
   echo "=== GCS Storage Report - $(date) ===" > /tmp/gcs_report.txt
   echo "" >> /tmp/gcs_report.txt

   echo "Bucket Overview:" >> /tmp/gcs_report.txt
   gcloud storage du gs://coaching-transcript-audio-uploads >> /tmp/gcs_report.txt
   echo "" >> /tmp/gcs_report.txt

   echo "File Count by Type:" >> /tmp/gcs_report.txt
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk '{ext = substr($3, index($3, ".")); count[ext]++}
        END {for (e in count) printf "%s: %d files\n", e, count[e]}' >> /tmp/gcs_report.txt

   echo "" >> /tmp/gcs_report.txt
   echo "Report saved to /tmp/gcs_report.txt"
   ```

## Advanced Monitoring Commands

### Storage Monitoring with Cloud SDK

1. **Regional Distribution**
   ```bash
   # Check multi-regional distribution if applicable
   gcloud storage buckets describe gs://coaching-transcript-audio-uploads \
   --format="value(location)"
   ```

2. **Access Patterns**
   ```bash
   # Get bucket access logs if enabled
   gcloud logging read "resource.type=gcs_bucket AND
                      resource.labels.bucket_name=coaching-transcript-audio-uploads" \
   --limit=50 --format=json
   ```

3. **Performance Metrics**
   ```bash
   # Query Cloud Monitoring for storage metrics
   gcloud monitoring metrics list --filter="storage.googleapis.com"
   ```

## Quality Checklist

### ✅ Data Verification
- [ ] Bucket access confirmed and authenticated
- [ ] File counts match expected usage patterns
- [ ] Storage sizes are reasonable for audio files
- [ ] No unexpected file types or sizes detected

### ✅ Security Review
- [ ] No sensitive data exposed in file names
- [ ] Proper IAM permissions verified
- [ ] Lifecycle policies properly configured
- [ ] Access logging enabled if required

### ✅ Cost Optimization
- [ ] Lifecycle rules configured for automatic cleanup
- [ ] Appropriate storage class usage
- [ ] Regional storage costs optimized
- [ ] Old files identified for cleanup

## Integration with Coaching Transcript Tool

### Application-Specific Checks

1. **Audio File Patterns**
   ```bash
   # Check for expected audio formats
   gcloud storage ls gs://coaching-transcript-audio-uploads/** | \
   grep -E '\.(mp3|wav|m4a|webm)$' | wc -l
   ```

2. **Session-Based Organization**
   ```bash
   # If files are organized by session IDs
   gcloud storage ls gs://coaching-transcript-audio-uploads/*/ | \
   head -10
   ```

3. **User Upload Verification**
   ```bash
   # Check recent uploads (last 24 hours)
   YESTERDAY=$(date -d '1 day ago' '+%Y-%m-%d')
   gcloud storage ls -l gs://coaching-transcript-audio-uploads/** | \
   awk -v cutoff="$YESTERDAY" '$2 > cutoff {print $3}' | \
   head -10
   ```

## Common Issues and Troubleshooting

### Authentication Problems
```bash
# Re-authenticate if needed
gcloud auth application-default login

# Check project configuration
gcloud config list
```

### Permission Issues
```bash
# Verify service account permissions
gcloud projects get-iam-policy coaching-transcript-tool \
--flatten="bindings[].members" \
--filter="bindings.members:$(gcloud config get-value account)"
```

### Large Dataset Handling
```bash
# For buckets with millions of files, use parallel operations
gcloud storage ls -l gs://coaching-transcript-audio-uploads/** \
--parallel-operations=10
```

## Best Practices

1. **Regular Monitoring** - Run weekly reports during low-traffic periods
2. **Cost Optimization** - Review storage classes and lifecycle policies monthly
3. **Security** - Audit access patterns and permissions quarterly
4. **Performance** - Monitor upload/download patterns for optimization
5. **Compliance** - Ensure file retention policies align with business requirements

## Sample Output Templates

### Daily Report Template
```
=== Daily GCS Storage Report ===
Date: $(date)
Bucket: coaching-transcript-audio-uploads

Files uploaded today: X files
Storage used today: X.XX MB
Total bucket size: X.XX GB
Files pending cleanup: X files

Top file types:
- .mp3: X files (X.XX MB)
- .wav: X files (X.XX MB)
```

### Weekly Summary Template
```
=== Weekly GCS Storage Summary ===
Week ending: $(date)

Upload activity: X files, X.XX GB
Storage growth: +X.XX% from last week
Cost estimate: $X.XX (based on standard pricing)
Cleanup actions: X files deleted

Recommendations:
- [ ] Action item 1
- [ ] Action item 2
```

---

**Status**: 📋 Workflow Pattern (Not Invokable Agent)
**Usage**: Manual GCS monitoring implementation
**Integration**: Can be automated via scripts or integrated with `general-purpose` agent for complex analysis