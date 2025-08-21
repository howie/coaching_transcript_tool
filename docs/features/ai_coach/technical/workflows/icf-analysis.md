# Tier 2 Workflow: ICF Competency Analysis

## 1. Overview

This document outlines the technical workflow for **Epic 2.1: ICF Skills Assessment Dashboard**. This workflow supports the user story: *"As a coach seeking ICF certification, I want AI analysis of my competencies so that I can track my progress and identify areas for improvement."*

The goal is to analyze a coaching conversation against the International Coaching Federation (ICF) Core Competencies framework, providing structured feedback, scores, and evidence-based examples to help coaches track and improve their skills.

**Related User Stories**: 
- [Epic 2.1: ICF Skills Assessment](../../user-stories.md#user-story-21-icf-skills-assessment-dashboard)
- [Epic 2.2: Professional Assessment Report](../../user-stories.md#user-story-22-professional-icf-assessment-report)

## 2. Workflow Diagram

```mermaid
graph TD
    A[Corrected Transcript] --> B{Analysis Request};
    B -- Session ID & Config --> C[LLM Router Service];
    C -- Route to High-Reasoning Model --> D[Selected LLM (e.g., Claude 3.5 Sonnet)];
    D -- Structured Analysis Prompt --> E[LLM Analyzes Competencies];
    E --> F{Parse & Validate JSON Output};
    F -- Valid JSON --> G[Extract Scores & Evidence];
    G --> H[Save to Competency Scores DB];
    H --> I[Generate Report];
    I --> J[Coach Dashboard UI];
    F -- Invalid JSON --> K[Retry/Fallback Logic];
```

## 3. Step-by-Step Process

### Step 1: Trigger and Input
- **Trigger**: User requests an ICF analysis for a specific session, or it's triggered automatically post-correction for Pro/Enterprise users.
- **Input**: A clean, corrected transcript from the Tier 1 process.

### Step 2: LLM Routing
- **Action**: The LLM Router Service receives the analysis request.
- **Logic**:
    1.  Identify the task as `icf_competency_analysis`.
    2.  Select a powerful model with strong reasoning and instruction-following capabilities. The default recommendation is **Claude 3.5 Sonnet** due to its excellent performance-to-cost ratio for this type of analysis. **GPT-4o** is a strong alternative.
    3.  The selection can be influenced by the user's subscription plan (e.g., Enterprise users might default to the most powerful model like Claude 3 Opus).

### Step 3: Prompt Engineering for Structured Output
- **Action**: Construct a sophisticated prompt that guides the LLM to produce a structured JSON output.
- **Prompt Template**:
    ```
    You are an ICF Master Certified Coach (MCC) responsible for evaluating a coaching session. Analyze the provided transcript based on the 8 ICF Core Competencies.

    **Instructions:**
    1.  For each of the 8 competencies, provide a score from 1 to 5 (1=Not Demonstrated, 5=Expertly Demonstrated).
    2.  For each score, provide a brief justification (2-3 sentences).
    3.  For each competency, extract 1-2 direct quotes from the transcript as evidence.
    4.  Provide one actionable recommendation for improvement for each competency.
    5.  Return the entire analysis as a single, valid JSON object. Do not include any text outside of the JSON.

    **JSON Structure:**
    {
      "overall_summary": "Brief summary of the coach's performance...",
      "competencies": [
        {
          "name": "1. Demonstrates Ethical Practice",
          "score": <integer>,
          "justification": "...",
          "evidence": [
            { "speaker": "Coach", "quote": "..." }
          ],
          "recommendation": "..."
        },
        // ... (repeat for all 8 competencies)
      ]
    }

    **Transcript to Analyze:**
    [Insert corrected transcript here]

    **JSON Output:**
    ```

### Step 4: Processing and Validation
- **Action**: The system receives the JSON output from the LLM.
- **Logic**:
    1.  **Parsing**: Attempt to parse the string output into a JSON object.
    2.  **Validation**:
        - If parsing fails, the text is likely malformed. Trigger a retry (potentially with a refined prompt asking the model to fix its own output).
        - If parsing succeeds, validate the JSON schema (e.g., using Pydantic). Ensure all required fields are present, scores are within range, and data types are correct.
        - If validation fails, trigger a fallback or flag for manual review.

### Step 5: Data Storage and Aggregation
- **Action**: The validated JSON data is processed and stored.
- **Logic**:
    1.  Iterate through the `competencies` array in the JSON.
    2.  For each competency, create a new record in the `competency_scores` table, linking it to the `ai_analyses` record.
    3.  Store the score, justification, evidence, and recommendation.
    4.  This structured data allows for powerful long-term analytics, such as tracking a coach's "Listens Actively" score over months.

### Step 6: Report Generation and Display
- **Action**: The system generates a user-friendly report from the stored data.
- **Output**:
    - A visual dashboard showing scores for all 8 competencies (e.g., using a radar chart).
    - A detailed breakdown for each competency, displaying the score, justification, and clickable evidence quotes that link back to the transcript.
    - A summary of strengths and areas for improvement.

## 4. Quality Assurance
- **Metrics**:
    - **Inter-rater reliability**: Compare the AI's scores with scores from human expert evaluators on a benchmark set of transcripts.
    - **Consistency**: Ensure the model provides similar scores for similar coaching behaviors across different sessions.
    - **User Feedback**: Collect feedback from coaches on the perceived accuracy and usefulness of the analysis.

## 5. Continuous Improvement
- The system will create a "feedback loop" where anonymized, user-corrected analyses can be used to fine-tune prompts or custom models in the future, continuously improving the accuracy and relevance of the AI-generated feedback.

## 6. User Story Alignment

This technical workflow directly supports the following user acceptance criteria:

✅ **Pro+ Feature Gating**: Analysis triggered only for Pro+ plans (Step 2)
✅ **8 Competency Scores**: Generates 1-5 scale scores (Step 3 prompt structure)
✅ **Evidence Quotes**: Extracts supporting transcript quotes (Step 4 validation)
✅ **Actionable Recommendations**: Provides improvement suggestions (Step 3 JSON structure)
✅ **Progress Tracking**: Historical trend analysis (Step 5 database storage)

**UI Integration Points:**
- "Analyze ICF Competencies" button triggers Step 1
- Processing indicator shows 2-5 minute analysis time
- Radar chart displays Step 4 competency scores
- Evidence viewer links to Step 4 extracted quotes
- Progress charts visualize Step 5 historical data

**Success Metrics Mapping:**
- ±0.5 point accuracy → Step 4 Quality Assurance validation
- 80% actionable recommendations → Step 3 prompt engineering
- 90% evidence relevance → Step 4 JSON validation

## 7. Implementation Notes

**Phase 2 Development Priority**: Builds on Phase 1 transcript correction foundation.

**Model Selection**: Claude 3.5 Sonnet recommended for optimal reasoning/cost balance.

**Subscription Integration**: Pro+ plan validation required before analysis initiation.

**Report Generation**: This workflow feeds both dashboard (2.1) and PDF report (2.2) user stories.
