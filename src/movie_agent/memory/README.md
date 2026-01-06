# Memory Layer

Senior-level memory system following architectural best practices.

## Architecture Principles

Memory follows the same patterns as tools and retrieval:

1. **Protocol-Based Interfaces** (`AgentMemory` ABC)
2. **Separation of Concerns** (conversation, semantic, episodic)
3. **Dependency Inversion** (depend on interfaces, not implementations)
4. **Composition** (`MemoryManager` composes multiple memories)
5. **Feature Flag** (memory is OFF by default)

## Memory Types

### 1. ConversationMemory (Implemented)

**Purpose**: Short-term conversational continuity

**Key traits**:
- FIFO buffer (first in, first out)
- No embeddings
- No persistence
- Bounded (max_turns)
- Cheap and predictable

**Use case**: Resolve pronouns ("that movie", "compare them")

### 2. SemanticMemory (Not Yet Implemented)

**Purpose**: Medium-term user preferences and queries

**Implementation**: Would reuse existing vector store pattern

**Use case**: Remember what the user likes, prior queries

### 3. EpisodicMemory (Not Yet Implemented)

**Purpose**: Important moments, not everything

**Implementation**: Importance-scored events

**Use case**: "User likes Nolan movies", "User prefers sci-fi thrillers"

## Usage

### Enable Memory

```python
from movie_agent.config import MovieAgentConfig

config = MovieAgentConfig(
    enable_memory=True,  # Feature flag
    memory_max_turns=10,  # Maximum conversation turns
)
```

### Clear Memory

```python
service.clear_memory()  # Clear all memory (for session reset)
```

## Memory Responsibilities

**Memory DOES**:
- Store structured interaction facts
- Provide retrieval interfaces
- Apply retention and eviction policies

**Memory DOES NOT**:
- Decide tool usage
- Format prompts
- Store raw LLM transcripts blindly

## Design Decisions

1. **Memory is OFF by default** - Feature flag prevents accidental use
2. **Conversation memory only** - Minimal implementation (can extend later)
3. **No persistence** - Memory cleared on service restart
4. **Explicit integration** - Memory context injected into prompt explicitly
5. **Fail soft** - Memory failures don't break the agent

## Future Extensions

- Semantic memory using FAISS vector store
- Episodic memory with importance scoring
- Persistence (database/KV store)
- User-specific memory profiles
- Memory compression/summarization

