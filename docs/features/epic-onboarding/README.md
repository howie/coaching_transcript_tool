# Coachly Onboarding Improvement Plan

## Objectives
- Accelerate new coaches from signup to their first actionable insight.
- Highlight the three core actions: create a session, upload a recording for transcript generation, and meet the AI Mentor.
- Reduce drop-off by building trust through transparent privacy and data handling messaging.

## Audience & Entry Points
- **New coach accounts** on first login to the dashboard.
- **Returning coaches** who have not yet completed the Quick Start checklist.
- **Invited team members** with limited access who still need guidance on creating their first session.

## Experience Blueprint

### 1. Dashboard Quick Start Guide
- **Surface**: Persistent onboarding panel at the top of the dashboard for incomplete checklists; collapsible once complete.
- **Structure**: Three-step horizontal checklist with progress indicator and contextual helper text.
  1. **Create your first coaching session** – primary CTA opens the session creation modal.
  2. **Upload a session recording** – secondary CTA opens the upload drawer once a session exists.
  3. **Explore the AI Mentor** – tertiary CTA launches the mentor with a guided prompt library.
- **Support Elements**:
  - Brief welcome message linking to a longer "How Coachly Works" article.
  - Inline privacy tooltip icon that links to the Privacy & Data Safeguards section below.
  - "Remind me later" option that snoozes the panel for 24 hours but keeps checklist state.

### 2. Session Creation & Recording Upload Flow
- **Session creation modal** collects session title, coachee name, and tags; upon save, automatically advances to the upload step.
- **Upload step** lives inside the session detail drawer with drag-and-drop plus file selector (audio/video formats supported).
- **Transcript progress feedback**: real-time status bar with estimated completion time; success state drops the user into the transcript view.
- **Post-upload action card** introduces key transcript features (highlights, timeline, comments) and reaffirms that the raw file is deleted once transcription completes.

### 3. AI Mentor Introduction
- **Trigger**: Available after the first transcript is ready; Quick Start step 3 becomes active.
- **Guided entry**: Pre-populated starter prompts such as "Summarize key coaching opportunities" and "Suggest follow-up questions" to demonstrate value quickly.
- **In-product education**: Contextual tooltip explaining that Mentor responses are based solely on the retained transcript, not the deleted raw recording.
- **Next-step CTA**: Encourage saving mentor insights into session notes or sharing with coachee.

## Privacy & Data Safeguards Messaging
- **Upload modal microcopy**: "We process your recording securely and delete the original file immediately after transcription."
- **Transcript view alert**: Dismissible banner reminding users they can delete the transcript at any time while keeping the session history and logged hours.
- **Help article link**: Inline link to the broader data policy (`docs/features/data_policy/`) from both the Quick Start card and the transcript banner.
- **Audit log reminder**: Note in session settings that deletions are recorded in the audit log for compliance, reinforcing trust without overloading the main flow.

## Content & UX Deliverables
- Updated dashboard hero copy and checklist UI specs.
- Step-by-step screenshots or short Loom demo embedded in the help center.
- Tooltip and banner microcopy localized for supported languages.
- Notification template for "Transcript ready" with privacy reassurance snippet.

## Implementation Considerations
- Gate the Quick Start panel behind a feature flag to allow gradual rollout and A/B testing.
- Track analytics events for each checklist step completion and tooltip interaction.
- Ensure upload infrastructure surfaces failures gracefully and offers re-upload without losing input data.
- Sync AI Mentor availability with transcript readiness to prevent empty states.

## Success Metrics
- % of new coaches completing all three Quick Start steps within 48 hours.
- Drop-off rate between session creation and recording upload.
- AI Mentor first-session engagement rate (sent at least one prompt).
- User-reported confidence in data privacy (post-onboarding NPS question).
