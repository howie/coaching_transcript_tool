# Tier 3 Workflow: Coaching Insight Generation

## 1. Overview

This document describes the technical workflow for **Epic 3: Advanced Coaching Insights**. This workflow supports two key user stories:
- *"As an experienced coach, I want AI insights into conversation patterns so that I can identify breakthrough moments and improve my coaching style."*
- *"As a coach managing multiple clients, I want cross-session insights so that I can track client progress and optimize my coaching approach."*

This is the most advanced tier, aiming to move beyond descriptive analysis (what happened) to prescriptive and predictive insights (what could be improved and why). It analyzes conversation patterns, coach-client dynamics, and historical data to generate deep, actionable recommendations.

**Related User Stories**: 
- [Epic 3.1: Conversation Pattern Discovery](../../user-stories.md#user-story-31-conversation-pattern-discovery)
- [Epic 3.2: Client Progress Analytics](../../user-stories.md#user-story-32-client-progress-analytics)

## 2. Workflow Diagram

```mermaid
graph TD
    A[Tier 1 & 2 Data] --> B{Insight Generation Request};
    B -- Session ID & Historical Context --> C[Data Aggregation Engine];
    C --> D[LLM Router Service];
    D -- Route to Top-Tier Model --> E[Selected LLM (e.g., Gemini 1.5 Pro, Claude Opus)];
    E -- Multi-turn/RAG Prompt --> F[LLM Generates Insights];
    F --> G{Parse & Categorize Insights};
    G --> H[Save to Coaching Insights DB];
    H --> I[Generate Insight Report];
    I --> J[Coach Dashboard UI];
```

## 3. Step-by-Step Process

### Step 1: Trigger and Data Aggregation
- **Trigger**: User requests "Deep Insights" for a session, typically available only on premium plans.
- **Input**: The target session's corrected transcript and its Tier 2 ICF analysis.
- **Data Aggregation Engine**:
    1.  Fetches the primary input data.
    2.  Retrieves historical data for the coach and client, such as:
        -   Past ICF competency scores.
        -   Key themes from previous sessions.
        -   Client's stated goals and progress.
    3.  (Future) May incorporate Retrieval-Augmented Generation (RAG) by fetching relevant articles or best practices from a coaching knowledge base.

### Step 2: LLM Routing
- **Action**: The LLM Router receives the aggregated data package.
- **Logic**:
    1.  Identify the task as `insight_generation`.
    2.  This task requires a model with a large context window and superior reasoning. The default recommendation is **Gemini 1.5 Pro** for its ability to process vast amounts of historical data in a single context. **Claude 3 Opus** or **GPT-4o** are excellent alternatives.
    3.  This service is computationally expensive and should be reserved for premium subscription tiers.

### Step 3: Advanced Prompt Engineering
- **Action**: Construct a multi-faceted prompt that encourages deep reasoning. This may involve a multi-turn conversation with the LLM to refine insights.
- **Prompt Template (Example - Simplified)**:
    ```
    You are a world-class coaching supervisor. Your task is to provide deep, non-obvious insights about the attached coaching session.

    **Context:**
    - **Current Session Transcript:** [Insert current transcript]
    - **Current ICF Analysis:** [Insert Tier 2 JSON summary]
    - **Historical Performance:** [Insert summary of coach's past competency scores]
    - **Client History:** [Insert summary of client's goals and past session themes]

    **Analysis Dimensions (Address each point):**
    1.  **Questioning Patterns**: Analyze the coach's questioning technique. Are they mostly open or closed questions? Do they lead the client? Identify a pivotal question and explain its impact.
    2.  **Client Breakthrough Moments**: Pinpoint 1-2 moments where the client had a significant realization. What did the coach do right before that moment?
    3.  **Coach's Blind Spots**: Based on the dialogue and historical data, what is a potential recurring blind spot for this coach (e.g., avoiding challenging the client, consistently focusing on one topic)?
    4.  **Session Arc**: Describe the overall flow of the conversation. Was there a clear beginning, middle, and end? Where did the energy shift?
    5.  **Actionable Recommendations**: Provide 3 concrete, actionable recommendations for the coach to try in their next session with this client.

    **Output Format:**
    Provide your analysis in a clear, structured markdown format.
    ```

### Step 4: Processing, Parsing, and Categorization
- **Action**: The system receives the markdown-formatted analysis from the LLM.
- **Logic**:
    1.  **Parsing**: Parse the markdown to identify the different insight categories (e.g., "Questioning Patterns", "Client Breakthroughs").
    2.  **Categorization**: For each insight, assign a category and priority level.
    3.  **Validation**: Check for coherence and relevance. A simple heuristic can be to ensure the insight contains references or quotes from the text.

### Step 5: Storage and Presentation
- **Action**: The parsed insights are stored and prepared for the user.
- **Logic**:
    1.  Each insight is saved as a record in the `coaching_insights` table, linked to the analysis.
    2.  The UI presents these insights in an engaging way, perhaps as interactive cards.
    3.  "Breakthrough Moments" could be linked directly to the timestamp in the transcript, allowing the coach to replay that part of the conversation.

## 4. Key Challenges and Mitigations
- **Subjectivity**: High-level insights can be subjective.
    - **Mitigation**: Frame insights as "potential observations" or "areas for reflection" rather than absolute truths. Always back them up with evidence from the text.
- **Cost**: This analysis is expensive in terms of token usage.
    - **Mitigation**: Clearly tie this feature to premium subscription tiers. Use cheaper models to pre-process or summarize historical data before sending it to the expensive model.
- **Latency**: The analysis can take several minutes.
    - **Mitigation**: Implement this as an asynchronous background job. The user requests the analysis and is notified via email or a dashboard notification when it's ready.

## 5. Future Enhancements
- **Cross-Session Analysis**: Automatically identify patterns and trends across dozens of a coach's sessions.
- **Predictive Analytics**: Based on the current trajectory, predict the likelihood of a client achieving their goals and suggest coaching strategies to improve the odds.

## 6. User Story Alignment

This technical workflow supports multiple Epic 3 acceptance criteria:

**Epic 3.1 - Conversation Pattern Discovery:**
✅ **Flow Analysis**: Step 1 aggregates session flow data
✅ **Breakthrough Identification**: Step 3 prompting targets pivotal moments
✅ **Blind Spot Detection**: Step 4 categorizes coach pattern insights
✅ **Style Analysis**: Step 3 multi-faceted prompting covers coaching patterns

**Epic 3.2 - Client Progress Analytics:**
✅ **Multi-Session Data**: Step 1 aggregates historical client data
✅ **Engagement Trends**: Step 2 processes conversation dynamics over time
✅ **Technique Effectiveness**: Step 4 categorizes successful interventions
✅ **Goal Prediction**: Step 3 advanced prompting includes predictive elements

**UI Integration Points:**
- "Deep Insights" button triggers Step 1 data aggregation
- Processing indicator shows 10-minute analysis timeframe
- Interactive timeline displays Step 5 breakthrough moments
- Pattern cards present Step 4 categorized insights
- Progress dashboard visualizes Step 1 historical trends

**Success Metrics Mapping:**
- 85% coaches discover new insights → Step 4 insight uniqueness validation
- 70% breakthrough accuracy → Step 3 moment identification precision
- 75% goal prediction accuracy → Step 3 predictive prompting validation

## 7. Implementation Notes

**Phase 3 Development Priority**: Requires Phase 1 & 2 data as foundation.

**Enterprise Feature**: Reserved for Enterprise tier due to computational cost.

**Model Selection**: Gemini 1.5 Pro preferred for large context window handling historical data.

**Async Processing**: Long processing time requires background job implementation with notification system.

**Privacy Considerations**: Multi-session analysis requires explicit client consent for data aggregation.
