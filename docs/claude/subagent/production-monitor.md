# Production Monitor Subagent

**Purpose**: Monitor and debug production API server using Render CLI

**When to Use**:
- Investigating production errors
- Verifying deployment success
- Monitoring real-time API behavior
- Debugging subscription/payment issues
- Checking database seed status

## Capabilities

### 1. Service Discovery
- List all Render services
- Identify API server service ID
- Check service status and deployment state

### 2. Log Monitoring
- Stream real-time logs
- Filter by status code, text, time range
- Search for specific errors or patterns
- Monitor subscription endpoint behavior

### 3. Error Analysis
- Identify Pydantic validation errors
- Track 500 error rates
- Analyze error patterns over time
- Correlate errors with deployments

### 4. Database Verification
- Check if plan data is seeded
- Verify subscription state
- Monitor database query logs

## Usage Examples

### Example 1: Check Production API Server Status

**User Request**: "Check if the subscription endpoint fix is deployed"

**Agent Actions**:
```bash
# 1. List services to find API server
render services -o json

# 2. Get recent logs for subscription endpoint
render logs -r <api-service-id> --limit 200 --text "subscriptions/current"

# 3. Check for Pydantic errors
render logs -r <api-service-id> --limit 100 --text "ValidationError"

# 4. Check 500 errors
render logs -r <api-service-id> --status-code 500 --limit 50
```

**Expected Output**:
```
✅ No Pydantic ValidationError found
✅ Subscription endpoint returning 200
⚠️  Still seeing "Retrieved 0 plans" - need to run seed script
```

### Example 2: Monitor Real-Time Errors

**User Request**: "Monitor production logs for any errors"

**Agent Actions**:
```bash
# Stream real-time logs with error filtering
render logs -r <api-service-id> --tail --level error

# Or filter by status codes
render logs -r <api-service-id> --tail --status-code 500,502,503
```

### Example 3: Verify Plan Seeding

**User Request**: "Check if plan configurations are in the database"

**Agent Actions**:
```bash
# Check for plan retrieval logs
render logs -r <api-service-id> --limit 100 --text "Retrieved" --text "plans"

# Look for plan-related errors
render logs -r <api-service-id> --limit 100 --text "plan_configurations"
```

**Expected Output**:
```
Before seeding: "Retrieved 0 plans for user..."
After seeding: "Retrieved 4 plans for user..."
```

### Example 4: Debug Subscription Errors

**User Request**: "Why are users getting 500 errors on subscription page?"

**Agent Actions**:
```bash
# 1. Get recent subscription endpoint logs
render logs -r <api-service-id> --limit 200 --path "/api/v1/subscriptions/current"

# 2. Filter for errors
render logs -r <api-service-id> --limit 100 --status-code 500 --path "/api/v1/subscriptions/current"

# 3. Look for Pydantic validation errors
render logs -r <api-service-id> --text "CurrentSubscriptionResponse" --text "validation errors"

# 4. Check service layer logs
render logs -r <api-service-id> --text "get_current_subscription"
```

## Available Render CLI Commands

### Core Commands

```bash
# List all services
render services -o json

# View logs (last 100 entries)
render logs -r <service-id> --limit 100

# Stream real-time logs
render logs -r <service-id> --tail

# Filter by text
render logs -r <service-id> --text "subscription" --text "error"

# Filter by status code
render logs -r <service-id> --status-code 500

# Filter by time range
render logs -r <service-id> --start "2025-10-04T06:00:00Z" --end "2025-10-04T07:00:00Z"

# Filter by log level
render logs -r <service-id> --level error

# Filter by HTTP method
render logs -r <service-id> --method GET,POST

# Filter by path
render logs -r <service-id> --path "/api/v1/subscriptions/current"

# Get logs in JSON format
render logs -r <service-id> --limit 50 -o json
```

### Session Commands

```bash
# Open psql session to production database
render psql -r <database-id>

# SSH into service instance
render ssh -r <service-id>
```

### Deployment Commands

```bash
# List recent deploys
render deploys -r <service-id>

# Restart service
render restart -r <service-id>
```

## Common Patterns

### Pattern 1: Post-Deployment Verification

```bash
# 1. Check deployment status
render deploys -r <api-service-id> -o json | jq '.[0]'

# 2. Monitor for errors in last 10 minutes
render logs -r <api-service-id> --start "$(date -u -v-10M +%Y-%m-%dT%H:%M:%SZ)" --level error

# 3. Verify specific endpoint works
render logs -r <api-service-id> --limit 50 --path "/api/v1/subscriptions/current" --status-code 200,500
```

### Pattern 2: Error Rate Analysis

```bash
# Count 500 errors in last hour
render logs -r <api-service-id> --status-code 500 --start "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" --limit 1000 -o json | jq 'length'

# Get unique error messages
render logs -r <api-service-id> --level error --limit 200 --text "ERROR"
```

### Pattern 3: Database State Verification

```bash
# 1. Check plan seeding logs
render logs -r <api-service-id> --text "plan_configurations" --limit 100

# 2. Open psql to verify directly
render psql -r <database-id>
# Then in psql:
# SELECT COUNT(*) FROM plan_configurations;
# SELECT plan_name, is_active FROM plan_configurations ORDER BY sort_order;
```

## Troubleshooting Guide

### Issue: Cannot Find Service ID

```bash
# List all services with details
render services -o json | jq '.[] | {id, name, type, status}'

# Or in interactive mode
render services
```

### Issue: Too Many Logs

```bash
# Use more specific filters
render logs -r <service-id> --limit 50 --text "specific_error_message"

# Use time range
render logs -r <service-id> --start "2025-10-04T06:00:00Z" --limit 100
```

### Issue: Need to See Full Request/Response

```bash
# Filter by specific path and status
render logs -r <service-id> --path "/api/v1/subscriptions/current" --status-code 500 --limit 20

# Look for request IDs in logs
render logs -r <service-id> --text "request_id"
```

## Response Format

When responding to user queries, provide:

1. **Current Status Summary**
   ```
   ✅ Service: running
   ✅ Recent deployments: successful
   ⚠️  Issues found: [list]
   ```

2. **Relevant Log Excerpts**
   - Show timestamps
   - Highlight error messages
   - Include request/response details

3. **Root Cause Analysis**
   - Identify patterns
   - Correlate with deployments
   - Link to related errors

4. **Actionable Recommendations**
   - Specific fixes needed
   - Scripts to run
   - Verification steps

## Important Notes

- **Read-Only Operations**: All log viewing is read-only and safe
- **Rate Limits**: Render CLI has rate limits, use appropriate --limit values
- **Time Zones**: Logs use UTC timestamps
- **Service IDs**: Cache service IDs to avoid repeated lookups
- **Sensitive Data**: Be careful not to expose secrets in log output

## Integration with Other Subagents

- **Error Analyzer**: Pass log excerpts for detailed analysis
- **Debugger**: Use logs to identify failing code paths
- **Performance Optimizer**: Monitor response times and slow queries
- **Security Auditor**: Check for security-related errors

## Related Documentation

- **Render CLI Docs**: https://docs.render.com/cli
- **API Standards**: `@docs/claude/api-standards.md`
- **Production Issues**: `@docs/issues/`
- **Testing Guide**: `@docs/claude/testing.md`
