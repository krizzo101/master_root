#!/usr/bin/env python3
"""
Message Bus Performance Benchmarks

Comprehensive performance testing suite to validate message bus meets requirements:
- Handle 50+ concurrent agents efficiently
- Achieve 1000+ messages/second throughput
- Maintain sub-100ms average latency
- Test point-to-point, broadcast, and topic-based messaging
- Monitor memory and CPU usage under load

Usage:
    python benchmarks.py [--redis-url REDIS_URL] [--duration SECONDS] [--agents COUNT]
"""

import argparse
import asyncio
import json
import logging
import statistics
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from src.message_bus.core.message_bus import MessageBus
from src.message_bus.gateway.websocket_gateway import WebSocketGateway
from src.message_bus.simple_client import SimpleMessageClient

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce log noise during benchmarks
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test"""

    test_name: str
    duration_seconds: float
    agent_count: int
    total_messages_sent: int
    total_messages_received: int
    messages_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    success_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MessageBusBenchmark:
    """Comprehensive benchmark suite for message bus performance"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        websocket_port: int = 8767,
    ):
        self.redis_url = redis_url
        self.websocket_port = websocket_port

        # Test infrastructure
        self.message_bus: Optional[MessageBus] = None
        self.websocket_gateway: Optional[WebSocketGateway] = None
        self.test_clients: List[SimpleMessageClient] = []

        # Performance tracking
        self.sent_timestamps: Dict[str, float] = {}
        self.received_timestamps: Dict[str, float] = {}
        self.latencies: List[float] = []
        self.errors: List[str] = []

        # System monitoring
        self.process = psutil.Process()
        self.initial_memory = 0
        self.initial_cpu = 0

    async def setup_infrastructure(self) -> None:
        """Setup message bus infrastructure for testing"""
        try:
            print("🔧 Setting up test infrastructure...")

            # Start Redis-based message bus
            self.message_bus = MessageBus(
                redis_url=self.redis_url,
                max_connections=200,  # Higher for benchmarks
                enable_compression=True,
                compression_threshold=512,
            )
            await self.message_bus.start()

            # Start WebSocket gateway
            self.websocket_gateway = WebSocketGateway(
                message_bus=self.message_bus,
                port=self.websocket_port,
                max_connections=500,  # Higher for benchmarks
            )
            await self.websocket_gateway.start()

            # Initialize monitoring
            self.initial_memory = self.process.memory_info().rss / 1024 / 1024
            self.initial_cpu = self.process.cpu_percent()

            print("✅ Infrastructure ready")

        except Exception as e:
            logger.error(f"Failed to setup infrastructure: {e}")
            raise

    async def teardown_infrastructure(self) -> None:
        """Clean up test infrastructure"""
        try:
            print("🧹 Cleaning up...")

            # Disconnect all test clients
            for client in self.test_clients:
                try:
                    if client.is_connected:
                        await client.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting client: {e}")

            self.test_clients.clear()

            # Stop infrastructure
            if self.websocket_gateway:
                await self.websocket_gateway.stop()

            if self.message_bus:
                await self.message_bus.stop()

            print("✅ Cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def create_test_clients(self, count: int) -> List[SimpleMessageClient]:
        """Create and connect test clients"""
        clients = []

        print(f"👥 Creating {count} test clients...")

        # Create clients in batches to avoid overwhelming the server
        batch_size = 10
        for i in range(0, count, batch_size):
            batch_clients = []

            for j in range(i, min(i + batch_size, count)):
                client = SimpleMessageClient(
                    agent_id=f"test_agent_{j}",
                    websocket_url=f"ws://localhost:{self.websocket_port}",
                    capabilities=["benchmark", "test"],
                    auto_reconnect=False,
                )

                # Register message handler to track latencies
                def create_handler(client_id):
                    def handle_message(sender_id: str, data: Dict[str, Any]):
                        msg_id = data.get("message_id")
                        if msg_id in self.sent_timestamps:
                            received_time = time.time()
                            latency_ms = (
                                received_time - self.sent_timestamps[msg_id]
                            ) * 1000
                            self.latencies.append(latency_ms)
                            self.received_timestamps[msg_id] = received_time

                    return handle_message

                client.register_direct_handler(create_handler(j))
                client.register_broadcast_handler(create_handler(j))

                batch_clients.append(client)

            # Connect batch
            connect_tasks = [client.connect() for client in batch_clients]
            results = await asyncio.gather(*connect_tasks, return_exceptions=True)

            for client, result in zip(batch_clients, results):
                if isinstance(result, Exception):
                    self.errors.append(f"Failed to connect {client.agent_id}: {result}")
                elif result:
                    clients.append(client)
                else:
                    self.errors.append(f"Failed to connect {client.agent_id}")

            # Small delay between batches
            await asyncio.sleep(0.1)

        print(f"✅ Connected {len(clients)}/{count} clients")
        return clients

    async def benchmark_point_to_point_messaging(
        self,
        agent_count: int,
        duration_seconds: int,
        message_size_bytes: int = 100,
    ) -> BenchmarkResult:
        """Benchmark point-to-point message delivery"""
        print("\n📡 Point-to-Point Messaging Benchmark")
        print(
            f"   Agents: {agent_count}, Duration: {duration_seconds}s, "
            f"Message Size: {message_size_bytes}B"
        )

        # Reset tracking
        self.sent_timestamps.clear()
        self.received_timestamps.clear()
        self.latencies.clear()
        self.errors.clear()

        # Create test clients
        clients = await self.create_test_clients(agent_count)
        if len(clients) < 2:
            raise Exception("Need at least 2 clients for point-to-point testing")

        # Create test message payload
        test_payload = {
            "data": "x" * (message_size_bytes - 50),  # Account for metadata
            "timestamp": 0,
            "message_id": "",
        }

        start_time = time.time()
        end_time = start_time + duration_seconds
        messages_sent = 0

        print("🚀 Starting point-to-point message flood...")

        # Message sending loop
        while time.time() < end_time:
            # Select random sender and receiver
            sender = clients[messages_sent % len(clients)]
            receiver = clients[(messages_sent + 1) % len(clients)]

            # Create unique message
            msg_id = str(uuid.uuid4())
            test_payload["message_id"] = msg_id
            test_payload["timestamp"] = time.time()

            # Record send time
            send_time = time.time()
            self.sent_timestamps[msg_id] = send_time

            # Send message
            try:
                response = await sender.send_to_agent(
                    receiver.agent_id, test_payload.copy()
                )
                if not response.success:
                    self.errors.append(f"Send failed: {response.error}")
                else:
                    messages_sent += 1
            except Exception as e:
                self.errors.append(f"Send exception: {e}")

            # Small delay to prevent overwhelming
            await asyncio.sleep(0.001)

        # Wait for message delivery
        await asyncio.sleep(2)

        return self._calculate_results(
            "Point-to-Point Messaging",
            time.time() - start_time,
            len(clients),
            messages_sent,
        )

    async def benchmark_broadcast_messaging(
        self,
        agent_count: int,
        duration_seconds: int,
        message_size_bytes: int = 100,
    ) -> BenchmarkResult:
        """Benchmark broadcast message delivery"""
        print("\n📢 Broadcast Messaging Benchmark")
        print(
            f"   Agents: {agent_count}, Duration: {duration_seconds}s, "
            f"Message Size: {message_size_bytes}B"
        )

        # Reset tracking
        self.sent_timestamps.clear()
        self.received_timestamps.clear()
        self.latencies.clear()
        self.errors.clear()

        # Create test clients
        clients = await self.create_test_clients(agent_count)

        # Create test message payload
        test_payload = {
            "data": "x" * (message_size_bytes - 50),
            "timestamp": 0,
            "message_id": "",
        }

        start_time = time.time()
        end_time = start_time + duration_seconds
        messages_sent = 0

        print("🚀 Starting broadcast message flood...")

        # Message sending loop
        while time.time() < end_time:
            sender = clients[messages_sent % len(clients)]

            # Create unique message
            msg_id = str(uuid.uuid4())
            test_payload["message_id"] = msg_id
            test_payload["timestamp"] = time.time()

            # Record send time
            send_time = time.time()
            self.sent_timestamps[msg_id] = send_time

            # Broadcast message
            try:
                response = await sender.broadcast(test_payload.copy())
                if not response.success:
                    self.errors.append(f"Broadcast failed: {response.error}")
                else:
                    messages_sent += 1
            except Exception as e:
                self.errors.append(f"Broadcast exception: {e}")

            # Longer delay for broadcasts (more expensive)
            await asyncio.sleep(0.01)

        # Wait for message delivery
        await asyncio.sleep(3)

        return self._calculate_results(
            "Broadcast Messaging", time.time() - start_time, len(clients), messages_sent
        )

    async def benchmark_topic_messaging(
        self,
        agent_count: int,
        duration_seconds: int,
        topic_count: int = 5,
    ) -> BenchmarkResult:
        """Benchmark topic-based messaging"""
        print("\n🏷️  Topic-Based Messaging Benchmark")
        print(
            f"   Agents: {agent_count}, Duration: {duration_seconds}s, Topics: {topic_count}"
        )

        # Reset tracking
        self.sent_timestamps.clear()
        self.received_timestamps.clear()
        self.latencies.clear()
        self.errors.clear()

        # Create test clients
        clients = await self.create_test_clients(agent_count)

        # Subscribe clients to random topics
        topics = [f"topic_{i}" for i in range(topic_count)]

        for client in clients:
            # Each client subscribes to 2-3 random topics
            import random

            client_topics = random.sample(topics, min(3, len(topics)))
            for topic in client_topics:

                def create_topic_handler(topic_name):
                    def handle_topic_message(data: Dict[str, Any]):
                        msg_id = data.get("message_id")
                        if msg_id in self.sent_timestamps:
                            received_time = time.time()
                            latency_ms = (
                                received_time - self.sent_timestamps[msg_id]
                            ) * 1000
                            self.latencies.append(latency_ms)
                            self.received_timestamps[msg_id] = received_time

                    return handle_topic_message

                await client.subscribe_topic(topic, create_topic_handler(topic))

        # Wait for subscriptions to settle
        await asyncio.sleep(1)

        start_time = time.time()
        end_time = start_time + duration_seconds
        messages_sent = 0

        print("🚀 Starting topic message flood...")

        # Message sending loop
        while time.time() < end_time:
            sender = clients[messages_sent % len(clients)]
            topic = topics[messages_sent % len(topics)]

            # Create message
            msg_id = str(uuid.uuid4())
            test_payload = {
                "message_id": msg_id,
                "timestamp": time.time(),
                "data": f"Topic message {messages_sent}",
            }

            # Record send time
            send_time = time.time()
            self.sent_timestamps[msg_id] = send_time

            # Send to topic
            try:
                response = await sender.send_to_topic(topic, test_payload)
                if not response.success:
                    self.errors.append(f"Topic send failed: {response.error}")
                else:
                    messages_sent += 1
            except Exception as e:
                self.errors.append(f"Topic send exception: {e}")

            await asyncio.sleep(0.005)

        # Wait for message delivery
        await asyncio.sleep(2)

        return self._calculate_results(
            "Topic-Based Messaging",
            time.time() - start_time,
            len(clients),
            messages_sent,
        )

    def _calculate_results(
        self, test_name: str, duration: float, agent_count: int, messages_sent: int
    ) -> BenchmarkResult:
        """Calculate benchmark results"""

        # Calculate latency statistics
        if self.latencies:
            avg_latency = statistics.mean(self.latencies)
            p95_latency = statistics.quantiles(self.latencies, n=20)[
                18
            ]  # 95th percentile
            p99_latency = statistics.quantiles(self.latencies, n=100)[
                98
            ]  # 99th percentile
            max_latency = max(self.latencies)
        else:
            avg_latency = p95_latency = p99_latency = max_latency = 0

        # Calculate throughput
        messages_per_second = messages_sent / duration if duration > 0 else 0

        # Calculate success rate
        messages_received = len(self.received_timestamps)
        success_rate = (
            (messages_received / messages_sent * 100) if messages_sent > 0 else 0
        )

        # Get system resource usage
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_usage = current_memory - self.initial_memory
        cpu_usage = self.process.cpu_percent()

        return BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            agent_count=agent_count,
            total_messages_sent=messages_sent,
            total_messages_received=messages_received,
            messages_per_second=messages_per_second,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            max_latency_ms=max_latency,
            success_rate=success_rate,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            errors=self.errors.copy(),
        )

    async def run_all_benchmarks(
        self, agent_count: int = 50, duration: int = 30
    ) -> List[BenchmarkResult]:
        """Run complete benchmark suite"""

        print("\n" + "=" * 60)
        print("🏁 STARTING MESSAGE BUS BENCHMARKS")
        print("=" * 60)
        print(f"Target: {agent_count} agents, {duration}s duration")
        print("Requirements: >1000 msg/s, <100ms avg latency")

        results = []

        try:
            await self.setup_infrastructure()

            # Run point-to-point benchmark
            result = await self.benchmark_point_to_point_messaging(
                agent_count, duration
            )
            results.append(result)
            self._print_result(result)

            # Clear clients between tests
            for client in self.test_clients:
                await client.disconnect()
            self.test_clients.clear()
            await asyncio.sleep(2)

            # Run broadcast benchmark
            result = await self.benchmark_broadcast_messaging(
                agent_count, duration // 2
            )
            results.append(result)
            self._print_result(result)

            # Clear clients between tests
            for client in self.test_clients:
                await client.disconnect()
            self.test_clients.clear()
            await asyncio.sleep(2)

            # Run topic benchmark
            result = await self.benchmark_topic_messaging(agent_count, duration)
            results.append(result)
            self._print_result(result)

        finally:
            await self.teardown_infrastructure()

        return results

    def _print_result(self, result: BenchmarkResult) -> None:
        """Print formatted benchmark result"""
        print(f"\n📊 {result.test_name} Results:")
        print(f"   Throughput:     {result.messages_per_second:.1f} msg/s")
        print(f"   Avg Latency:    {result.avg_latency_ms:.1f} ms")
        print(f"   P95 Latency:    {result.p95_latency_ms:.1f} ms")
        print(f"   P99 Latency:    {result.p99_latency_ms:.1f} ms")
        print(f"   Success Rate:   {result.success_rate:.1f}%")
        print(f"   Memory Usage:   {result.memory_usage_mb:.1f} MB")
        print(f"   CPU Usage:      {result.cpu_usage_percent:.1f}%")

        if result.errors:
            print(f"   Errors:         {len(result.errors)}")

        # Check if requirements are met
        throughput_ok = result.messages_per_second >= 1000
        latency_ok = result.avg_latency_ms <= 100
        success_ok = result.success_rate >= 95

        status = "✅ PASS" if all([throughput_ok, latency_ok, success_ok]) else "❌ FAIL"
        print(f"   Status:         {status}")

    def save_results(
        self, results: List[BenchmarkResult], filename: str = None
    ) -> None:
        """Save benchmark results to JSON file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"benchmark_results_{timestamp}.json"

        data = {
            "timestamp": time.time(),
            "results": [result.to_dict() for result in results],
            "summary": {
                "total_tests": len(results),
                "avg_throughput": statistics.mean(
                    [r.messages_per_second for r in results]
                ),
                "avg_latency": statistics.mean([r.avg_latency_ms for r in results]),
                "overall_success_rate": statistics.mean(
                    [r.success_rate for r in results]
                ),
            },
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n💾 Results saved to: {filename}")


async def main():
    """Main benchmark runner"""
    parser = argparse.ArgumentParser(description="Message Bus Performance Benchmarks")
    parser.add_argument(
        "--redis-url", default="redis://localhost:6379/0", help="Redis connection URL"
    )
    parser.add_argument(
        "--agents", type=int, default=50, help="Number of test agents to simulate"
    )
    parser.add_argument(
        "--duration", type=int, default=30, help="Test duration in seconds"
    )
    parser.add_argument(
        "--websocket-port", type=int, default=8767, help="WebSocket server port"
    )
    parser.add_argument(
        "--save-results", action="store_true", help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Create and run benchmarks
    benchmark = MessageBusBenchmark(
        redis_url=args.redis_url,
        websocket_port=args.websocket_port,
    )

    try:
        results = await benchmark.run_all_benchmarks(
            agent_count=args.agents,
            duration=args.duration,
        )

        # Print final summary
        print("\n" + "=" * 60)
        print("📈 BENCHMARK SUMMARY")
        print("=" * 60)

        for result in results:
            throughput_status = "✅" if result.messages_per_second >= 1000 else "❌"
            latency_status = "✅" if result.avg_latency_ms <= 100 else "❌"
            print(f"{result.test_name}:")
            print(f"  {throughput_status} {result.messages_per_second:.0f} msg/s")
            print(f"  {latency_status} {result.avg_latency_ms:.1f}ms avg latency")

        if args.save_results:
            benchmark.save_results(results)

        print("\n🎉 Benchmarking complete!")

    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
