# Agent Communication Platform

## Overview
A distributed communication and collaboration platform enabling autonomous agents to coordinate, share knowledge, and work together effectively.

## Architecture

### Core Components

1. **Message Bus** (`message_bus.py`)
   - Central message routing system
   - Topic-based pub/sub messaging
   - Message persistence and history
   - Priority queuing

2. **Knowledge Base** (`knowledge_base.py`)
   - Shared knowledge repository
   - Expert identification system
   - Searchable by topics and content
   - Usefulness scoring

3. **Collaboration Protocols** (`collaboration_protocols.py`)
   - Peer review workflow
   - Task handoff mechanism
   - Proposal voting system
   - Structured interaction patterns

4. **Platform Integration** (`communication_platform.py`)
   - Unified interface for all components
   - Agent registration and management
   - Metrics and monitoring
   - Client SDK for agents

## Quick Start

```python
from communication_platform import CommunicationPlatform

# Initialize platform
platform = CommunicationPlatform()

# Register an agent
client = await platform.register_agent(
    agent_id="my_agent",
    name="My Agent",
    capabilities=["coding", "testing"]
)

# Send a message
await client.send_message(
    recipient="other_agent",
    topic="code_review",
    content={"code": "def hello(): pass"}
)

# Receive messages
messages = await client.receive_messages()

# Share knowledge
await client.share_knowledge(
    topic="python_tips",
    knowledge={"tip": "Use asyncio for concurrency"}
)
```

## Communication Patterns

### Direct Messaging
Agent-to-agent private communication.

### Broadcasting
Send messages to all agents.

### Topic Subscription
Subscribe to specific topics for relevant messages.

### Help Requests
Request assistance from agents with specific capabilities.

## Collaboration Workflows

### Peer Review
1. Author submits artifact for review
2. Platform assigns reviewers
3. Reviewers provide feedback
4. Author receives consolidated feedback

### Task Handoff
1. Agent A identifies need to transfer task
2. Initiates handoff to Agent B
3. Agent B accepts or rejects
4. Task ownership transfers

### Consensus Voting
1. Agent proposes decision
2. Platform notifies voters
3. Agents vote on proposal
4. Result determined by majority

## API Reference

### AgentClient Methods

- `send_message(recipient, topic, content, priority)` - Send a message
- `receive_messages()` - Get pending messages
- `share_knowledge(topic, knowledge)` - Add to knowledge base
- `query_knowledge(query)` - Search knowledge base
- `find_expert(topic)` - Find expert agent
- `request_help(capability, task_details)` - Request assistance
- `request_review(artifact, reviewers)` - Initiate peer review
- `update_status(status, workload)` - Update agent status

## Testing

Run the test suite:
```bash
python test_platform.py
```

## Performance Considerations

- Message queues are in-memory (upgrade to Redis for production)
- Knowledge base uses file persistence (consider database for scale)
- Async operations throughout for non-blocking communication

## Future Enhancements

1. WebSocket support for real-time messaging
2. Redis backend for distributed deployment
3. Message encryption for sensitive data
4. GraphQL API for complex queries
5. Machine learning for intelligent routing
6. Metrics dashboard for monitoring

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                  Agent Clients                  │
└─────────────┬──────────────────┬────────────────┘
              │                  │
        ╔═════▼══════════════════▼═════╗
        ║   Communication Platform     ║
        ╠═══════════════════════════════╣
        ║  ┌───────────────────────┐   ║
        ║  │    Message Bus        │   ║
        ║  │  - Routing            │   ║
        ║  │  - Persistence        │   ║
        ║  └───────────────────────┘   ║
        ║  ┌───────────────────────┐   ║
        ║  │   Knowledge Base      │   ║
        ║  │  - Storage            │   ║
        ║  │  - Search             │   ║
        ║  └───────────────────────┘   ║
        ║  ┌───────────────────────┐   ║
        ║  │  Collaboration        │   ║
        ║  │  - Protocols          │   ║
        ║  │  - Workflows          │   ║
        ║  └───────────────────────┘   ║
        ╚═══════════════════════════════╝
```

## Contributing

When extending the platform:
1. Follow the interface definitions in `interfaces.py`
2. Add tests for new functionality
3. Update documentation
4. Maintain backwards compatibility

## License
MIT

---
Built by Multi-Agent Collaboration System
Version 1.0.0
