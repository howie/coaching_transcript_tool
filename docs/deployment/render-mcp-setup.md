# Render MCP Setup and Usage Guide

**Purpose**: Access Render.com production database and services via MCP (Model Context Protocol)

## Installation

### Step 1: Install Render MCP Server

```bash
# Add Render MCP server to Claude Code
claude mcp add render-mcp
```

Follow the prompts to configure the server.

### Step 2: Configure Authentication

The Render MCP will use your existing Render CLI authentication:

```bash
# Verify you're logged in
render whoami

# If not logged in:
render login
```

## Production Database Access

### Database Information

- **Service ID**: `dpg-d27igr7diees73cla8og-a`
- **Name**: `Coachly-db-production`
- **Database**: `coachly`
- **User**: `coachly_user`
- **Region**: Singapore
- **Version**: PostgreSQL 17

### Common Queries

#### Check Plan Configurations

```sql
-- Count plans
SELECT COUNT(*) FROM plan_configurations;

-- List all plans
SELECT plan_type, plan_name, display_name, is_active, is_visible, sort_order
FROM plan_configurations
ORDER BY sort_order;

-- Check specific plan details
SELECT * FROM plan_configurations WHERE plan_type = 'PRO';
```

#### Verify Database State

```sql
-- Check table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_name = 'plan_configurations'
);

-- Get table structure
\d plan_configurations

-- Check for any data
SELECT
    COUNT(*) as total_plans,
    COUNT(*) FILTER (WHERE is_active = true) as active_plans,
    COUNT(*) FILTER (WHERE is_visible = true) as visible_plans
FROM plan_configurations;
```

#### Subscription Data

```sql
-- Count subscriptions
SELECT COUNT(*) FROM subscriptions;

-- Check user subscriptions
SELECT u.email, s.plan_id, s.status, s.created_at
FROM subscriptions s
JOIN "user" u ON s.user_id = u.id
ORDER BY s.created_at DESC
LIMIT 10;
```

## Using MCP for Deployment

### Pre-Deployment Verification

```sql
-- 1. Verify database is empty
SELECT COUNT(*) FROM plan_configurations;
-- Expected: 0 (before seeding)

-- 2. Check no active subscriptions will be affected
SELECT COUNT(*) FROM subscriptions WHERE status = 'active';
```

### Post-Deployment Verification

```sql
-- 1. Verify 4 plans seeded
SELECT COUNT(*) FROM plan_configurations;
-- Expected: 4

-- 2. Verify all plans are active
SELECT plan_name, is_active, is_visible
FROM plan_configurations
WHERE is_active = false OR is_visible = false;
-- Expected: 0 rows (all should be active)

-- 3. Check plan pricing
SELECT plan_type,
       monthly_price_twd_cents / 100 as monthly_twd,
       annual_price_twd_cents / 100 as annual_twd
FROM plan_configurations
ORDER BY sort_order;
```

## Production Services via MCP

### API Server Logs

Use MCP to query logs for the production API server:

- **Service ID**: `srv-d2sndkh5pdvs739lqq0g`
- **Name**: `Coachly-api-production`

Example queries:
```
Show recent logs with "Retrieved" and "plans"
Show errors in last hour
Show 500 status codes
```

### Environment Variables

Query production environment configuration (sensitive data will be masked):

```
List environment variables for srv-d2sndkh5pdvs739lqq0g
Show DATABASE_URL configuration
```

## Troubleshooting

### MCP Connection Issues

```bash
# Check MCP status
claude mcp list

# Restart MCP server
claude mcp restart render-mcp

# Remove and re-add if needed
claude mcp remove render-mcp
claude mcp add render-mcp
```

### Database Access Issues

If you can't access the database via MCP:

1. **Check Render CLI authentication**:
   ```bash
   render whoami
   ```

2. **Verify database service is running**:
   ```bash
   render services list | grep -i database
   ```

3. **Fallback to direct psql** (if MCP fails):
   ```bash
   # Get connection string from Render dashboard
   # Then use deployment script
   export DATABASE_URL="postgresql://..."
   ./scripts/deployment/seed_production_plans.sh
   ```

## Security Notes

- MCP has read-only access to logs by default
- Database queries via MCP should be read-only for verification
- Use deployment scripts for write operations
- Never expose DATABASE_URL or sensitive credentials

## Related Documentation

- **Production Issue**: `@docs/issues/production-no-plan.md`
- **Deployment Script**: `@scripts/deployment/seed_production_plans.sh`
- **Seed Script**: `@scripts/database/seed_plan_configurations_v2.py`
- **Render MCP Docs**: https://github.com/render-com/mcp-server-render (if available)

## Quick Reference Commands

### After Installing Render MCP

1. **Check database state**:
   ```
   Query Render database dpg-d27igr7diees73cla8og-a:
   SELECT COUNT(*) FROM plan_configurations;
   ```

2. **View plan details**:
   ```
   Query Render database dpg-d27igr7diees73cla8og-a:
   SELECT * FROM plan_configurations ORDER BY sort_order;
   ```

3. **Check recent logs**:
   ```
   Show logs for srv-d2sndkh5pdvs739lqq0g with "plans"
   ```

4. **Verify seeding success**:
   ```
   Query Render database dpg-d27igr7diees73cla8og-a:
   SELECT plan_type, is_active, is_visible FROM plan_configurations;
   ```
