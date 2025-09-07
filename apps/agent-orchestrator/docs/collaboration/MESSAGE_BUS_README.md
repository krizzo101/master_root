# Real-Time Message Bus for Agent Collaboration

A production-ready, high-performance Redis-based pub/sub messaging system designed for agent-to-agent communication and collaboration.

## 🚀 Features

- **High Performance**: Handle 50+ concurrent agents with 1000+ messages/second throughput
- **Redis Backend**: Uses Redis Streams and Pub/Sub for scalable, reliable messaging
- **WebSocket Gateway**: Real-time connections for instant message delivery
- **Multiple Message Types**: Point-to-point, broadcast, topic-based, and group messaging
- **Message Persistence**: Optional message replay and persistence
- **Load Balancing**: Intelligent message routing with circuit breakers
- **Admin Interface**: Web-based monitoring and management
- **Simple SDK**: High-level client library for easy integration
- **Performance Monitoring**: Built-in metrics and benchmarking tools

## 📋 Requirements

- Python 3.8+
- Redis server 6.0+
- Required Python packages: `redis`, `websockets`, `aiohttp`, `psutil`

## 🔧 Quick Start

### 1. Install Dependencies

```bash
pip install redis websockets aiohttp psutil
```

### 2. Start Redis Server

```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or install Redis locally
# On Ubuntu: sudo apt install redis-server
# On macOS: brew install redis
```

### 3. Start Message Bus Server

```bash
python message_bus_server.py
```

This starts:
- **WebSocket Gateway** on port 8767 (for agent connections)
- **Admin Interface** on port 8768 (for monitoring)
- **Redis Backend** connection

### 4. Connect Agents

```python
from src.message_bus.simple_client import SimpleMessageClient

async def main():
    # Create agent client
    agent = SimpleMessageClient("my_agent_id", capabilities=["processing", "analysis"])

    # Connect to message bus
    await agent.connect()

    # Send direct message
    response = await agent.send_to_agent("other_agent", {
        "action": "process_data",
        "data": [1, 2, 3, 4, 5]
    })

    # Broadcast to all agents
    await agent.broadcast({"announcement": "Hello everyone!"})

    # Subscribe to topics
    await agent.subscribe_topic("alerts", handle_alert_message)

    # Disconnect
    await agent.disconnect()

def handle_alert_message(data):
    print(f"Alert received: {data}")

# Run the agent
import asyncio
asyncio.run(main())
```

## 🏗️ Architecture

The message bus consists of several key components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent A       │    │   Agent B       │    │   Agent C       │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │WebSocket             │WebSocket             │WebSocket
          │                      │                      │
    ┌─────▼──────────────────────▼──────────────────────▼─────┐
    │           WebSocket Gateway (Port 8767)                │
    │                                                        │
    │  ┌─────────────────┐  ┌─────────────────────────────┐ │
    │  │  Message Router │  │     Connection Manager     │ │
    │  │  - Load Balance │  │   - Heartbeat Monitor      │ │
    │  │  - Topic Route  │  │   - Auto Reconnection      │ │
    │  │  - Priority     │  │   - Session Management     │ │
    │  └─────────────────┘  └─────────────────────────────┘ │
    └────────────────────┬───────────────────────────────────┘
                         │
    ┌────────────────────▼───────────────────────────────────┐
    │              Redis Message Bus                         │
    │                                                        │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
    │  │   Streams   │  │   Pub/Sub   │  │  Persistence │   │
    │  │ (Reliable)  │  │ (Real-time) │  │  (Optional)  │   │
    │  └─────────────┘  └─────────────┘  └─────────────┘   │
    └────────────────────┬───────────────────────────────────┘
                         │
    ┌────────────────────▼───────────────────────────────────┐
    │              Admin Interface (Port 8768)               │
    │                                                        │
    │  📊 Metrics    👥 Agents    📨 Messages    ⚙️ Config  │
    └────────────────────────────────────────────────────────┘
```

### Core Components

1. **Message Bus Core** (`src/message_bus/core/`)
   - Redis integration with connection pooling
   - Message serialization and compression
   - Delivery confirmation and retry logic

2. **WebSocket Gateway** (`src/message_bus/gateway/`)
   - Real-time agent connections
   - Connection management and heartbeats
   - Message routing to connected clients

3. **Message Router** (`src/message_bus/routing/`)
   - Load balancing across agent instances
   - Topic-based routing and subscriptions
   - Circuit breaker patterns for fault tolerance

4. **Client SDK** (`src/message_bus/client/` and `src/message_bus/simple_client.py`)
   - High-level API for agents
   - Automatic reconnection and error handling
   - Support for all message types

5. **Admin Interface** (`src/message_bus/admin/`)
   - Web-based monitoring dashboard
   - Agent management and control
   - Performance metrics and analytics

## 📨 Message Types

The message bus supports four primary message patterns:

### 1. Point-to-Point Messaging
Direct communication between specific agents.

```python
response = await client.send_to_agent("target_agent", {
    "action": "process_request",
    "data": {"key": "value"}
})
```

### 2. Broadcast Messaging
Send messages to all connected agents.

```python
await client.broadcast({
    "type": "system_announcement",
    "message": "System maintenance in 5 minutes"
})
```

### 3. Topic-Based Messaging
Publish/subscribe pattern with topic filtering.

```python
# Subscribe to topics
await client.subscribe_topic("alerts", handle_alert)
await client.subscribe_topic("notifications", handle_notification)

# Publish to topics
await client.send_to_topic("alerts", {
    "level": "critical",
    "message": "Database connection lost"
})
```

### 4. Group Messaging
Messages targeted at specific groups of agents.

```python
# Join groups
await client.join_group("processing_team", handle_team_message)

# Send to group
await client.send_to_group("processing_team", {
    "task": "monthly_report",
    "deadline": "2024-01-31"
})
```

## 🎯 Usage Examples

### Basic Agent Communication

```python
from src.message_bus.simple_client import SimpleMessageClient

class MyAgent:
    def __init__(self, agent_id):
        self.client = SimpleMessageClient(
            agent_id=agent_id,
            capabilities=["processing", "analysis"]
        )

        # Register message handlers
        self.client.register_direct_handler(self.handle_direct_message)
        self.client.register_broadcast_handler(self.handle_broadcast)

    async def start(self):
        await self.client.connect()

        # Subscribe to relevant topics
        await self.client.subscribe_topic("work_assignments", self.handle_work)
        await self.client.subscribe_topic("system_alerts", self.handle_alerts)

    def handle_direct_message(self, sender_id, data):
        print(f"Direct message from {sender_id}: {data}")

    def handle_broadcast(self, sender_id, data):
        print(f"Broadcast from {sender_id}: {data}")

    def handle_work(self, data):
        print(f"Work assignment: {data}")

    def handle_alerts(self, data):
        print(f"System alert: {data}")
```

### Task Delegation Example

```python
class ManagerAgent:
    async def delegate_task(self, task_data, required_capability):
        # Broadcast task to agents with specific capability
        await self.client.broadcast({
            "type": "task_available",
            "task": task_data,
            "required_capabilities": [required_capability]
        })

    async def handle_task_interest(self, sender_id, data):
        # Agent expressed interest in a task
        if self.can_assign_task(sender_id, data["task_id"]):
            await self.client.send_to_agent(sender_id, {
                "type": "task_assigned",
                "task_id": data["task_id"]
            })
```

## 📊 Performance & Benchmarking

### Running Benchmarks

```bash
python benchmarks.py --agents 50 --duration 30
```

This tests:
- **Throughput**: Messages per second capacity
- **Latency**: Average, P95, and P99 response times
- **Scalability**: Performance under different agent counts
- **Resource Usage**: Memory and CPU consumption

### Expected Performance

The message bus is designed to meet these performance requirements:

- **Throughput**: 1000+ messages/second
- **Concurrent Agents**: 50+ agents simultaneously
- **Average Latency**: <100ms for message delivery
- **Success Rate**: >99% message delivery

### Performance Tips

1. **Connection Pooling**: Use Redis connection pools for high throughput
2. **Message Batching**: Batch small messages when possible
3. **Compression**: Enable compression for large messages (>1KB)
4. **Topic Design**: Use specific topics rather than broad broadcasts
5. **Connection Management**: Implement proper heartbeat and reconnection logic

## 🔧 Configuration

### Server Configuration

```bash
python message_bus_server.py \
  --redis-url redis://localhost:6379/0 \
  --websocket-port 8767 \
  --admin-port 8768 \
  --max-connections 1000
```

### Client Configuration

```python
client = SimpleMessageClient(
    agent_id="my_agent",
    websocket_url="ws://localhost:8767",
    capabilities=["processing", "analysis"],
    auto_reconnect=True,
)
```

### Redis Configuration

For production use, configure Redis with:

```
# /etc/redis/redis.conf
maxmemory-policy allkeys-lru
maxmemory 2gb
timeout 300
tcp-keepalive 300
save 900 1
save 300 10
save 60 10000
```

## 🛡️ Error Handling & Reliability

The message bus includes several reliability features:

### Automatic Reconnection
Clients automatically reconnect on connection loss with exponential backoff.

### Message Persistence
Optional message persistence ensures delivery even if agents are temporarily offline.

### Circuit Breakers
The router includes circuit breakers to handle agent failures gracefully.

### Health Monitoring
Built-in health checks and monitoring for all components.

### Graceful Degradation
Falls back to file-based queuing if Redis becomes unavailable.

## 📈 Monitoring & Admin Interface

Access the admin interface at `http://localhost:8768` to monitor:

- **Agent Status**: Connected agents and their capabilities
- **Message Metrics**: Throughput, latency, and error rates
- **System Health**: Resource usage and component status
- **Message Queues**: Pending and failed messages
- **Performance Charts**: Real-time performance graphs

### Available Endpoints

- `GET /health` - System health check
- `GET /metrics` - Performance metrics
- `GET /agents` - List connected agents
- `GET /topics` - Active topics and subscriptions
- `POST /agents/{id}/kick` - Disconnect an agent
- `POST /topics/{topic}/broadcast` - Send admin broadcast

## 🧪 Testing & Validation

### Run the Demo

```bash
# Terminal 1: Start the server
python message_bus_server.py

# Terminal 2: Run the basic demo
python examples/message_bus_demo.py

# Terminal 3: Run the collaboration example
python examples/agent_collaboration_example.py
```

### Run Performance Tests

```bash
# Basic performance test
python benchmarks.py

# Extended test with more agents
python benchmarks.py --agents 100 --duration 60

# Save results for analysis
python benchmarks.py --save-results
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure Redis server is running
   - Check Redis connection URL
   - Verify firewall settings

2. **High Latency**
   - Check Redis performance
   - Monitor network conditions
   - Reduce message size
   - Use message compression

3. **Message Loss**
   - Enable message persistence
   - Check Redis memory limits
   - Implement proper error handling

4. **Agent Disconnections**
   - Increase heartbeat interval
   - Check network stability
   - Review connection timeout settings

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor Redis performance:

```bash
redis-cli monitor
redis-cli info stats
```

## 🛠️ Development & Extension

### Adding Custom Message Types

1. Extend the `MessageType` enum in `message_types.py`
2. Update the message router logic
3. Add handling in the client SDK

### Custom Message Handlers

```python
class CustomAgent(CollaborativeAgent):
    def __init__(self):
        super().__init__("custom_agent", "custom", ["special_processing"])

    def handle_direct_message(self, sender_id, data):
        if data.get("type") == "custom_request":
            self.handle_custom_request(sender_id, data)
        else:
            super().handle_direct_message(sender_id, data)

    def handle_custom_request(self, sender_id, data):
        # Custom processing logic
        pass
```

### Performance Optimization

1. **Message Serialization**: Use faster serialization (e.g., msgpack)
2. **Connection Pooling**: Implement custom connection pooling
3. **Caching**: Add message caching for frequently accessed data
4. **Batching**: Implement message batching for high-throughput scenarios

## 📚 API Reference

### SimpleMessageClient

The main client interface for agents:

#### Methods

- `connect() -> bool` - Connect to message bus
- `disconnect()` - Disconnect from message bus
- `send_to_agent(recipient_id, data, priority=NORMAL) -> MessageResponse` - Send direct message
- `broadcast(data, required_capabilities=None) -> MessageResponse` - Broadcast message
- `send_to_topic(topic, data) -> MessageResponse` - Publish to topic
- `send_to_group(group_id, data) -> MessageResponse` - Send to group
- `subscribe_topic(topic, handler) -> bool` - Subscribe to topic
- `join_group(group_id, handler) -> bool` - Join message group
- `register_direct_handler(handler)` - Register direct message handler
- `register_broadcast_handler(handler)` - Register broadcast message handler

#### Properties

- `is_connected -> bool` - Connection status
- `agent_id -> str` - Agent identifier

### Message Structure

```python
{
    "message_id": "unique-id",
    "message_type": "point_to_point|broadcast|topic|group",
    "sender_id": "sending-agent-id",
    "recipient_id": "target-agent-id",  # For direct messages
    "topic": "topic-name",              # For topic messages
    "group_id": "group-name",           # For group messages
    "payload": {...},                   # Message data
    "priority": "low|normal|high|critical",
    "timestamp": 1640995200.0,
    "requires_ack": false,
    "persistent": false
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
git clone <repository>
cd message-bus
pip install -r requirements.txt
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

For questions, issues, or contributions:

1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Join our community discussions

---

**Built for production agent collaboration** 🤖💬
