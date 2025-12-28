# Architecture Overview

## System Design

The Movie Agent Service follows a **service-oriented architecture** with clear separation between the service layer and the UI layer.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flask (Thin UI)                      │
│  - HTTP endpoints                                       │
│  - Request/response handling                            │
│  - Input validation                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              MovieAgentApp (Facade)                      │
│  - Public API                                           │
│  - Composition root                                     │
│  - Dependency wiring                                    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ MovieTools   │ │  RAG    │ │   Vision     │
│   Agent      │ │  Store  │ │   Analyst    │
└──────────────┘ └──────────┘ └──────────────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
            ┌─────────────────┐
            │  Movie Data     │
            │  (IMDb Dataset) │
            └─────────────────┘
```

### Component Responsibilities

#### 1. Flask (UI Layer)
- **Role**: Thin HTTP interface
- **Responsibility**: 
  - Accept HTTP requests
  - Validate inputs
  - Call service methods
  - Format responses
  - Handle HTTP errors

#### 2. MovieAgentApp (Service Facade)
- **Role**: Public API and composition root
- **Responsibility**:
  - Expose service methods to Flask
  - Wire dependencies (data loader, vector store, agent, tools)
  - Manage service lifecycle (initialization, state)
  - Provide unified interface

#### 3. MovieToolsAgent (Agent Layer)
- **Role**: ReAct agent orchestrator
- **Responsibility**:
  - Process user queries
  - Select and execute tools
  - Maintain conversation context
  - Generate responses

#### 4. RAG Store (Knowledge Base)
- **Role**: Vector store for movie data
- **Responsibility**:
  - Store movie embeddings
  - Perform semantic search
  - Retrieve relevant context

#### 5. Vision Analyst
- **Role**: Image analysis for movie posters
- **Responsibility**:
  - Analyze uploaded images
  - Extract movie information from posters
  - Provide descriptions for agent

### Data Flow

1. **User Request** → Flask receives HTTP request
2. **Validation** → Flask validates input
3. **Service Call** → Flask calls `MovieAgentApp.chat()`
4. **Agent Processing** → Agent analyzes query, selects tools
5. **Tool Execution** → Tools query RAG store, analyze images, etc.
6. **Response Generation** → Agent generates response from tool results
7. **Return** → Response flows back through service → Flask → HTTP response

### Design Patterns

- **Facade Pattern**: `MovieAgentApp` provides simple interface to complex subsystem
- **Service Layer**: Business logic separated from UI
- **Composition Root**: Dependencies wired in `MovieAgentApp.__init__()`
- **Dependency Injection**: Manual DI (no framework)
- **Thin Controller**: Flask only handles HTTP concerns

### Technology Stack

- **LLM**: Groq (Llama 3.1 8B) or OpenAI GPT
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Store**: FAISS
- **Agent Framework**: LangChain
- **UI**: Flask (REST API)
- **Vision**: BLIP (local) or OpenAI Vision

