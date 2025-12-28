# Design Decisions

This document explains **WHY** architectural and implementation decisions were made.

## Core Principles

### 1. Separation of Concerns

**Decision**: Strict separation between service layer and UI layer.

**Rationale**:
- Service can be tested independently of Flask
- Service can be reused (CLI, different UI frameworks, etc.)
- UI changes don't affect business logic
- Follows Single Responsibility Principle

**Trade-offs**:
- Slightly more code (service + UI layers)
- More abstraction layers

### 2. Flask as Thin UI Layer

**Decision**: Flask only handles HTTP concerns, delegates all logic to service.

**Rationale**:
- Flask is not a business logic framework
- Keeps HTTP concerns (routing, status codes, headers) separate
- Makes service testable without HTTP layer
- Follows "Thin Controller" pattern

**Trade-offs**:
- More explicit wiring between Flask and service
- Cannot use Flask-specific features in service (good thing!)

### 3. Facade Pattern for MovieAgentApp

**Decision**: `MovieAgentApp` acts as facade, hiding complexity of agent, tools, RAG store.

**Rationale**:
- Flask doesn't need to know about agent internals
- Single entry point simplifies testing
- Changes to internal structure don't affect Flask
- Clear public API boundary

**Trade-offs**:
- One more layer of indirection
- Facade can become "god object" if not careful (mitigated by service layer pattern)

### 4. Manual Dependency Injection

**Decision**: No DI framework, wire dependencies manually in composition root.

**Rationale**:
- Explicit dependencies (easier to understand)
- No framework lock-in
- Simpler for small-to-medium projects
- Full control over lifecycle

**Trade-offs**:
- More boilerplate for large projects
- Manual wiring can be error-prone (mitigated by clear structure)

### 5. Service as Standalone Module

**Decision**: Service can run independently, doesn't require Flask.

**Rationale**:
- Testable without HTTP server
- Can be used in CLI tools, scripts, other frameworks
- Clear boundaries
- Interview-driven: demonstrates understanding of service architecture

**Trade-offs**:
- Cannot use Flask-specific features (session, request context, etc.)
- Must handle state management explicitly

### 6. Interview-Driven Terminology

**Decision**: Use industry-standard terms (service, facade, composition root, etc.).

**Rationale**:
- Demonstrates understanding of software architecture
- Aligns with how senior engineers discuss systems
- Makes codebase self-documenting
- Shows staff-level thinking

**Trade-offs**:
- May be unfamiliar to junior developers
- Requires documentation (this file!)

### 7. RAG + ReAct Boundaries

**Decision**: Clear separation between RAG (retrieval) and ReAct (agent reasoning).

**Rationale**:
- RAG provides context, ReAct uses it
- Tools can use RAG, but RAG doesn't know about agents
- Follows dependency rule (high-level depends on low-level)
- Easier to test and reason about

**Trade-offs**:
- More explicit data passing
- Cannot use LangChain's built-in RAG chains (we build our own)

### 8. Explicit Error Handling

**Decision**: Service methods return errors, Flask converts to HTTP status codes.

**Rationale**:
- Service doesn't know about HTTP (separation of concerns)
- Errors are typed and explicit
- Easier to test error cases
- Clear error boundaries

**Trade-offs**:
- Must map service errors to HTTP status codes
- More error handling code

## Future Considerations

- **Caching**: Add caching layer for frequent queries
- **Rate Limiting**: Implement at Flask layer
- **Logging**: Structured logging with correlation IDs
- **Monitoring**: Health checks, metrics endpoints
- **Configuration**: Environment-based config management

