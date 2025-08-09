# Database Entity-Relationship Diagram

This document describes the database schema and entity relationships for the Coaching Assistant Platform.

## Overview

The database is designed to support a comprehensive coaching assistant platform with audio transcription, session management, coach profiles, and client management features.

## Core Tables

### 1. User
The main user table supporting authentication and subscription management.

```
User
├── id (UUID, PK)
├── email (String, unique, indexed)
├── hashed_password (String, nullable for SSO)
├── name (String)
├── avatar_url (String)
├── google_id (String, unique, indexed, nullable)
├── plan (Enum: FREE, PRO, ENTERPRISE)
├── usage_minutes (Integer)
├── preferences (JSON Text)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### 2. Session
Audio transcription sessions linked to users.

```
Session
├── id (UUID, PK)
├── user_id (UUID, FK -> User.id) [CASCADE DELETE]
├── title (String)
├── audio_filename (String)
├── duration_sec (Integer)
├── language (String, default: "auto")
├── status (Enum: UPLOADING, PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED)
├── gcs_audio_path (String)
├── transcription_job_id (String)
├── error_message (Text)
├── stt_cost_usd (String)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### 3. TranscriptSegment
Individual transcript segments from speech-to-text processing.

```
TranscriptSegment
├── id (UUID, PK)
├── session_id (UUID, FK -> Session.id) [CASCADE DELETE]
├── speaker_id (Integer) # 1, 2, 3...
├── start_sec (Float)
├── end_sec (Float)
├── content (Text)
├── confidence (Float) # 0.0-1.0
├── created_at (DateTime)
└── updated_at (DateTime)
```

### 4. SessionRole
Speaker role assignments for coaching sessions.

```
SessionRole
├── id (UUID, PK)
├── session_id (UUID, FK -> Session.id) [CASCADE DELETE]
├── speaker_id (Integer)
├── role (Enum: COACH, CLIENT, UNKNOWN)
├── created_at (DateTime)
├── updated_at (DateTime)
└── UNIQUE(session_id, speaker_id)
```

### 5. CoachProfile
Public coach profile information.

```
CoachProfile
├── id (UUID, PK)
├── user_id (UUID, FK -> User.id, unique)
├── display_name (String)
├── profile_photo_url (Text)
├── public_email (String)
├── phone_country_code (String)
├── phone_number (String)
├── country (String)
├── city (String)
├── timezone (String)
├── coaching_languages (JSON Text)
├── communication_tools (JSON Text)
├── line_id (String)
├── coach_experience (String)
├── training_institution (String)
├── certifications (JSON Text)
├── linkedin_url (String)
├── personal_website (String)
├── bio (Text)
├── specialties (JSON Text)
├── is_public (Boolean)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### 6. CoachingPlan
Coaching plans/packages offered by coaches.

```
CoachingPlan
├── id (UUID, PK)
├── coach_profile_id (UUID, FK -> CoachProfile.id)
├── plan_type (String)
├── title (String)
├── description (Text)
├── duration_minutes (Integer)
├── number_of_sessions (Integer, default: 1)
├── price (Float)
├── currency (String, default: 'NTD')
├── is_active (Boolean, default: true)
├── max_participants (Integer, default: 1)
├── booking_notice_hours (Integer, default: 24)
├── cancellation_notice_hours (Integer, default: 24)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### 7. Client
Client information managed by coaches.

```
Client
├── id (UUID, PK)
├── coach_id (UUID, FK -> User.id) [CASCADE DELETE]
├── name (String)
├── email (String, nullable)
├── phone (String, nullable)
├── memo (Text, nullable)
├── source (String, nullable) # referral, organic, friend, etc.
├── client_type (String, nullable) # paid, pro_bono, etc.
├── issue_types (Text, nullable) # comma-separated
├── client_status (String, default: 'first_session')
├── is_anonymized (Boolean, default: false)
├── anonymized_at (DateTime, nullable)
├── created_at (DateTime)
└── updated_at (DateTime)
```

### 8. CoachingSession
Actual coaching sessions between coaches and clients.

```
CoachingSession
├── id (UUID, PK)
├── coach_id (UUID, FK -> User.id) [CASCADE DELETE]
├── client_id (UUID, FK -> Client.id) [CASCADE DELETE]
├── session_date (Date)
├── source (Enum: CLIENT, FRIEND, CLASSMATE, SUBORDINATE)
├── duration_min (Integer) [CHECK: > 0]
├── fee_currency (String, default: "TWD")
├── fee_amount (Integer, default: 0) [CHECK: >= 0]
├── transcript_timeseq_id (UUID, nullable)
├── audio_timeseq_id (UUID, nullable)
├── notes (Text, nullable)
├── created_at (DateTime)
└── updated_at (DateTime)
```

## Association Tables

### coach_languages
Many-to-many relationship between CoachProfile and coaching languages.

```
coach_languages
├── coach_profile_id (UUID, FK -> CoachProfile.id, PK)
└── language (String, PK)
```

### coach_communication_tools
Many-to-many relationship between CoachProfile and communication tools.

```
coach_communication_tools
├── coach_profile_id (UUID, FK -> CoachProfile.id, PK)
└── tool (String, PK)
```

## Entity Relationships

### Primary Relationships

1. **User → Session** (1:N)
   - One user can have multiple transcription sessions
   - Sessions are cascade deleted when user is deleted

2. **Session → TranscriptSegment** (1:N)
   - One session contains multiple transcript segments
   - Segments ordered by `start_sec`
   - Segments are cascade deleted when session is deleted

3. **Session → SessionRole** (1:N)
   - One session can have multiple speaker roles
   - Unique constraint on `(session_id, speaker_id)`
   - Roles are cascade deleted when session is deleted

4. **User → CoachProfile** (1:1)
   - One user can have one coach profile
   - Profile is cascade deleted when user is deleted

5. **CoachProfile → CoachingPlan** (1:N)
   - One coach can offer multiple coaching plans
   - Plans are cascade deleted when profile is deleted

6. **User → Client** (1:N) [as Coach]
   - One coach can manage multiple clients
   - Clients are cascade deleted when coach is deleted

7. **User → CoachingSession** (1:N) [as Coach]
   - One coach can conduct multiple coaching sessions
   - Sessions are cascade deleted when coach is deleted

8. **Client → CoachingSession** (1:N)
   - One client can participate in multiple coaching sessions
   - Sessions are cascade deleted when client is deleted

## Enums

### UserPlan
- `FREE`: Free tier with limited features
- `PRO`: Professional tier with extended features  
- `ENTERPRISE`: Enterprise tier with unlimited features

### SessionStatus
- `UPLOADING`: User is uploading audio file
- `PENDING`: Audio uploaded, waiting for processing
- `PROCESSING`: Speech-to-text processing in progress
- `COMPLETED`: Processing completed successfully
- `FAILED`: Processing failed
- `CANCELLED`: User cancelled the session

### SpeakerRole
- `COACH`: Speaker identified as coach
- `CLIENT`: Speaker identified as client
- `UNKNOWN`: Speaker role not identified

### CoachingLanguage
Available coaching languages including Mandarin, English, Cantonese, Japanese, Korean, Spanish, French, German.

### CommunicationTool
Supported communication platforms including LINE, Zoom, Google Meet, MS Teams, Skype, WeChat, WhatsApp.

### CoachExperience
- `BEGINNER`: 0-1 years
- `INTERMEDIATE`: 1-3 years  
- `ADVANCED`: 3-5 years
- `EXPERT`: 5+ years

### CoachingPlanType
- `SINGLE_SESSION`: Individual session
- `PACKAGE`: Multi-session package
- `GROUP`: Group coaching
- `WORKSHOP`: Workshop format
- `CUSTOM`: Custom arrangement

### SessionSource
- `CLIENT`: Session sourced from direct client
- `FRIEND`: Session with a friend/peer
- `CLASSMATE`: Session with a classmate  
- `SUBORDINATE`: Session with a subordinate

## Key Features

### Audio Transcription Pipeline
1. User uploads audio → Session created with `UPLOADING` status
2. Audio stored in Google Cloud Storage → `PENDING` status
3. Google Speech-to-Text processes audio → `PROCESSING` status
4. Transcript segments and speaker roles created → `COMPLETED` status
5. Export formats: VTT, SRT, JSON

### Coach Management System
- Public coach profiles with contact information
- Multiple coaching plans with pricing
- Client relationship management
- Session tracking and billing

### GDPR Compliance
- Client anonymization features
- Data retention policies
- Audit trails with timestamps

### Usage Tracking
- Monthly usage limits by plan
- Cost tracking for transcription services
- Analytics and reporting capabilities

## Indexes

The following indexes are implemented for optimal performance:

### Primary Indexes
- `User.email` (unique)
- `User.google_id` (unique)
- `Session.user_id`
- `TranscriptSegment.session_id`
- `SessionRole.session_id`
- `CoachProfile.user_id` (unique)
- `Client.coach_id`
- `CoachingSession.coach_id`
- `CoachingSession.client_id`

### Composite Indexes
- `idx_clients_coach_name` on `(coach_id, name)` - Client lookup by coach
- `idx_sessions_coach_date` on `(coach_id, session_date DESC)` - Recent sessions by coach
- `idx_sessions_coach_currency_date` on `(coach_id, fee_currency, session_date)` - Financial reporting
- `uq_clients_coach_email` on `(coach_id, lower(email))` UNIQUE WHERE email IS NOT NULL - Unique client emails per coach

## Database Constraints

### Check Constraints
- `CoachingSession.duration_min > 0`
- `CoachingSession.fee_amount >= 0`

### Unique Constraints  
- `SessionRole(session_id, speaker_id)` - One role per speaker per session
- `CoachProfile.user_id` - One profile per user
- `Client(coach_id, lower(email))` WHERE email IS NOT NULL - Unique client emails per coach

### Foreign Key Constraints
All foreign keys include appropriate CASCADE DELETE behavior to maintain referential integrity.

## Data Types and Considerations

### UUID Usage
All primary keys use UUID v4 for better distribution and security.

### Monetary Fields
- `fee_amount` is stored as INTEGER to avoid floating-point precision issues
- Currency amounts should be stored in smallest units (e.g., cents for USD, 分 for TWD)

### JSON Storage
Several fields use JSON for flexible schema:
- `User.preferences` - User-specific settings and preferences
- `CoachProfile.coaching_languages` - Array of language codes
- `CoachProfile.communication_tools` - Object with tool configurations  
- `CoachProfile.certifications` - Array of certification objects
- `CoachProfile.specialties` - Array of specialty strings
- `Client.issue_types` - Comma-separated string (could be JSON array)

### Audio File Management
- `Session.gcs_audio_path` stores Google Cloud Storage paths
- Audio files are automatically deleted after 24 hours for GDPR compliance
- `Session.audio_filename` preserves original filename for user reference

### Timezone Considerations
- All timestamps stored in UTC
- `CoachProfile.timezone` stores coach's preferred timezone
- Session scheduling should account for timezone differences

## Migration History Notes

The schema has evolved through multiple migrations including:
- Addition of coach profiles and coaching plans
- Client management features  
- GDPR compliance fields (anonymization)
- Enhanced indexing for performance
- Session source tracking
- Communication tools and language preferences