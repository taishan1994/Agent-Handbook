# Design Doc: PocketFlow FastAPI Background Job with SSE Progress

> Please DON'T remove notes for AI

## Requirements

> Notes for AI: Keep it simple and clear.
> If the requirements are abstract, write concrete user stories

**User Story**: As a user, I want to submit an article topic via a web API and receive real-time progress updates while the article is being generated in the background, so I can see the workflow progress without blocking the UI.

**Core Requirements**:
1. Submit article topic via REST API endpoint
2. Start background job for article generation workflow
3. Receive real-time progress updates via Server-Sent Events (SSE)
4. Get final article result when workflow completes
5. Handle multiple concurrent requests

**Technical Requirements**:
- FastAPI web server with REST endpoints
- Background task processing using asyncio
- Server-Sent Events for progress streaming
- Simple web interface to test the functionality

## Flow Design

> Notes for AI:
> 1. Consider the design patterns of agent, map-reduce, rag, and workflow. Apply them if they fit.
> 2. Present a concise, high-level description of the workflow.

### Applicable Design Pattern:

**Workflow Pattern**: Sequential processing of article generation steps with progress reporting at each stage.

### Flow High-level Design:

1. **Generate Outline Node**: Creates a structured outline for the article topic
2. **Write Content Node**: Writes content for each section in the outline  
3. **Apply Style Node**: Applies conversational styling to the final article

Each node puts progress updates into an asyncio.Queue for SSE streaming.

```mermaid
flowchart LR
    outline[Generate Outline] --> content[Write Content]
    content --> styling[Apply Style]
```

## Utility Functions

> Notes for AI:
> 1. Understand the utility function definition thoroughly by reviewing the doc.
> 2. Include only the necessary utility functions, based on nodes in the flow.

1. **Call LLM** (`utils/call_llm.py`)
   - *Input*: prompt (str)
   - *Output*: response (str)
   - Used by all workflow nodes for LLM tasks

## Node Design

### Shared Store

> Notes for AI: Try to minimize data redundancy

The shared store structure is organized as follows:

```python
shared = {
    "topic": "user-provided-topic",
    "sse_queue": asyncio.Queue(),  # For sending SSE updates
    "sections": ["section1", "section2", "section3"],
    "draft": "combined-section-content",
    "final_article": "styled-final-article"
}
```

### Node Steps

> Notes for AI: Carefully decide whether to use Batch/Async Node/Flow.

1. **Generate Outline Node**
   - *Purpose*: Create a structured outline with 3 main sections using YAML output
   - *Type*: Regular Node (synchronous LLM call)
   - *Steps*:
     - *prep*: Read "topic" from shared store
     - *exec*: Call LLM to generate YAML outline, parse and validate structure
     - *post*: Write "sections" to shared store, put progress update in sse_queue

2. **Write Content Node**
   - *Purpose*: Generate concise content for each outline section
   - *Type*: BatchNode (processes each section independently)
   - *Steps*:
     - *prep*: Read "sections" from shared store (returns list of sections)
     - *exec*: For one section, call LLM to write 100-word content
     - *post*: Combine all section content into "draft", put progress update in sse_queue

3. **Apply Style Node**
   - *Purpose*: Apply conversational, engaging style to the combined content
   - *Type*: Regular Node (single LLM call for styling)
   - *Steps*:
     - *prep*: Read "draft" from shared store
     - *exec*: Call LLM to rewrite in conversational style
     - *post*: Write "final_article" to shared store, put completion update in sse_queue
