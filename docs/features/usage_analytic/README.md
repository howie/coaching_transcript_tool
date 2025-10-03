# Usage Analytics Feature (Enterprise Only)

This directory contains documentation for usage analytics and history tracking features.

## Overview

The usage analytics feature provides **Enterprise plan users** with comprehensive insights into their platform usage patterns, trends, and predictions to help optimize their subscription plans and usage patterns.

> **⚠️ Enterprise Feature**: This feature is exclusively available to Enterprise plan subscribers as part of advanced analytics capabilities.

## Features Included

### Core Features
- **Usage History Dashboard**: Historical usage data with time range selection
- **Trend Visualization**: Charts and graphs showing usage patterns over time
- **Predictive Analytics**: Forecast future usage and plan limit warnings
- **Insights & Recommendations**: Personalized suggestions for optimization

### Key Components
- **Frontend**: React components with interactive charts (LineChart, BarChart, PieChart)
- **Data Visualization**: Usage trends, breakdown analysis, and insights panels
- **Mock Data**: Development-friendly mock data generation for frontend testing

## Implementation Status

✅ **Completed**
- Frontend UsageHistory component with comprehensive analytics
- Chart components (LineChart, BarChart, PieChart) 
- Mock data generation for development
- Internationalization (i18n) support for Chinese and English
- Integration with billing dashboard

🚧 **In Development**
- Backend API endpoints for real usage data
- Database schema for usage history tracking (see `schema-migration-needed.md`)
- Scheduled aggregation jobs

⚠️ **Known Issues**
- Database schema mismatch blocking usage insights AND predictions API (see `schema-migration-needed.md`)
- Missing columns: `billable`, `cost_cents` in `usage_logs` table
- Temporary workarounds in place, requires database migration
- Frontend hidden from production (dev-only with DEV label)

✅ **Recent Fixes** (2025-10-03)
- Added i18n translation for error messages (`common.failedToLoadData`)
- Hidden usage history tab from production (dev-only visibility)

📝 **Planned**
- Advanced prediction algorithms
- Email usage reports
- Data export functionality
- Performance optimization

## Files

- `US005-usage-history-analytics.md` - Complete technical specification and implementation plan
- `schema-migration-needed.md` - Database schema migration issue and workarounds
- `README.md` - This overview document

## Related Features

This feature is part of the broader billing and subscription management system but has been separated into its own module for better organization and maintainability.

## Technical Notes

This feature was moved from the `plan_limitation` directory as it represents a standalone analytics capability that extends beyond basic plan enforcement, making it more suitable as a dedicated usage analytics module.