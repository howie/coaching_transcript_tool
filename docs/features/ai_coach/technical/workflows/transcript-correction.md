# Tier 1 Workflow: Transcript Correction

## 1. Overview

This document details the technical workflow for **Epic 1.1: Automatic Transcript Correction**. This workflow supports the user story: *"As a coach, I want my raw transcripts automatically corrected so that I can focus on coaching insights rather than fixing typos."*

The primary goal is to automate the process of cleaning and standardizing raw speech-to-text (STT) output to produce a clean, readable, and accurate transcript.

**Related User Story**: [Epic 1.1 in user-stories.md](../../user-stories.md#user-story-11-automatic-transcript-correction)

## 2. Workflow Diagram

```mermaid
graph TD
    A[Raw Transcript Input] --> B{Validation & Pre-processing};
    B --> C[LLM Router Service];
    C -- Route to Cost-Effective Model --> D[Selected LLM (e.g., Claude Haiku, GPT-3.5)];
    D -- Correction Prompt --> E[LLM Processes Transcript];
    E --> F{Post-processing & Validation};
    F -- Formatted Output --> G[Corrected Transcript];
    F -- Generates Diff --> H[Correction Diff View];
    G --> I[Save to Database];
    H --> J[User Review Interface];
```

## 3. Step-by-Step Process

### Step 1: Input & Pre-processing
- **Trigger**: A new raw transcript is available from the STT service.
- **Input**: JSON object containing transcript text, speaker labels, and timestamps.
- **Action**:
    1.  Validate the input format.
    2.  Concatenate speaker turns into a single text block, preserving speaker labels (e.g., `[Coach]: Hello. [Client]: Hi there.`).
    3.  Apply any initial rule-based text normalization (e.g., removing filler words like "umm").

### Step 2: LLM Routing
- **Action**: The LLM Router Service receives the pre-processed text.
- **Logic**:
    1.  Identify the task as `transcript_correction`.
    2.  Select the most cost-effective and fastest model designated for this task. The default recommendation is **Claude 3 Haiku** or **GPT-3.5 Turbo**. AssemblyAI LeMUR is a strong candidate if integrated directly with the STT pipeline.
    3.  The system can be configured to use a specific provider based on user subscription plan (e.g., Enterprise plans might use GPT-4o for higher accuracy).

### Step 3: Prompt Engineering & LLM Processing
- **Action**: Construct a detailed prompt for the selected LLM.
- **Prompt Template**:
    ```
    You are an expert in editing coaching conversation transcripts. Your task is to correct the following transcript.

    **Instructions:**
    1.  Correct spelling mistakes and typos.
    2.  Add appropriate punctuation (commas, periods, question marks).
    3.  Ensure consistent speaker labels ("[Coach]:" and "[Client]:").
    4.  Do NOT change the meaning of the sentences.
    5.  Format the output as a clean, readable dialogue.
    6.  Maintain the original speaker turn structure.

    **Transcript to Correct:**
    [Insert pre-processed transcript here]

    **Corrected Transcript:**
    ```
- **LLM Execution**: The LLM processes the prompt and returns the corrected transcript.

### Step 4: Post-processing & Diff Generation
- **Action**: The system receives the corrected text from the LLM.
- **Logic**:
    1.  **Validation**: Check if the output format is valid and speaker labels are intact. If not, trigger a retry or fallback to another model.
    2.  **Diff Generation**: Compare the original and corrected transcripts to generate a "diff" view, highlighting all changes (additions, deletions). This is crucial for user trust and review.
    3.  **Formatting**: Format the final output into a structured JSON object, ready for storage and display.

### Step 5: Storage and User Review
- **Action**:
    1.  The corrected transcript and the diff data are saved to the database, linked to the original session.
    2.  The user interface displays the corrected transcript, with an option to view the highlighted changes.
    3.  The user can accept, reject, or manually edit the corrections.

## 4. Quality Assurance
- **Metrics**:
    - **Word Error Rate (WER)** reduction: Measure the percentage of errors corrected compared to a human-verified "golden" transcript.
    - **Latency**: Track the end-to-end processing time. Goal is < 10 seconds.
    - **Cost**: Monitor the cost per transcript correction.
- **Process**: Periodically, a sample of corrected transcripts will be reviewed by humans to ensure the AI is not altering the original meaning.

## 5. Fallback Strategy
- If the primary LLM fails (API error, invalid output), the LLM Router will automatically retry with a designated fallback model (e.g., if Haiku fails, retry with GPT-3.5 Turbo).
- If all retries fail, the system will flag the transcript for manual review and use the original raw transcript as a placeholder.

## 6. User Story Alignment

This technical workflow directly supports the following user acceptance criteria:

✅ **Processing Speed**: Completes within 30 seconds (Step 4 targets <10 seconds)
✅ **Diff Comparison**: Generates before/after comparison (Step 4.2)
✅ **Individual Control**: User can accept/reject corrections (Step 5.3)
✅ **Download Ready**: Corrected transcript saved for export (Step 5.1)

**UI Integration Points:**
- Auto-Correct button triggers Step 1
- Progress indicator shows Steps 2-4 processing
- Diff viewer displays Step 4.2 output
- Accept/reject controls interact with Step 5 database

**Success Metrics Mapping:**
- 90% accuracy target → Quality Assurance WER tracking
- <30s processing → Latency monitoring in Step 4
- 85% user acceptance → User interaction tracking in Step 5

## 7. Implementation Notes

**Phase 1 Development Priority**: This workflow is the foundation for all AI Coach features and must be implemented first.

**Cost Optimization**: Use Claude Haiku or GPT-3.5 Turbo for optimal cost/performance ratio.

**Quality Gates**: All corrections must preserve original meaning - validation in Step 4.1 is critical.
