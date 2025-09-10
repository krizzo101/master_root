#!/usr/bin/env python3
"""
WebSocket Stress Test
Tests WebSocket connection stability under high concurrent load and stress conditions
"""
import asyncio
import json
import random
import signal
import sys
import time
from typing import Dict, List

import websockets


class WebSocketStressTester:
    """Comprehensive WebSocket stress testing"""

    def __init__(self):
        self.results = {}
        self.running = True

    async def stress_client(
        self, client_id: int, duration: int, message_rate: float = 1.0
    ):
        """Single stress test client with configurable message rate"""
        uri = "ws://localhost:8765/ws"
        stats = {
            "client_id": client_id,
            "connected_at": None,
            "disconnected_at": None,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "connection_drops": 0,
            "reconnects": 0,
            "latency_samples": [],
        }

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time and self.running:
            try:
                async with websockets.connect(uri) as websocket:
                    if stats["connected_at"] is None:
                        stats["connected_at"] = time.time()
                        print(f"Client {client_id}: Connected")
                    else:
                        stats["reconnects"] += 1
                        print(
                            f"Client {client_id}: Reconnected (attempt {stats['reconnects']})"
                        )

                    last_message_time = 0

                    # Main message loop
                    while time.time() < end_time and self.running:
                        try:
                            # Send messages at specified rate
                            if time.time() - last_message_time >= (1.0 / message_rate):
                                message_type = random.choice(
                                    ["ping", "get_summary", "get_metrics"]
                                )

                                if message_type == "ping":
                                    send_time = time.time()
                                    msg = {
                                        "type": "ping",
                                        "timestamp": send_time,
                                        "client_id": client_id,
                                    }
                                elif message_type == "get_summary":
                                    send_time = time.time()
                                    msg = {
                                        "type": "get_summary",
                                        "timestamp": send_time,
                                    }
                                else:  # get_metrics
                                    send_time = time.time()
                                    msg = {
                                        "type": "get_metrics",
                                        "seconds": random.randint(30, 300),
                                        "timestamp": send_time,
                                    }

                                await websocket.send(json.dumps(msg))
                                stats["messages_sent"] += 1
                                last_message_time = time.time()

                            # Listen for responses
                            try:
                                response = await asyncio.wait_for(
                                    websocket.recv(), timeout=0.1
                                )
                                stats["messages_received"] += 1

                                # Calculate latency for ping responses
                                try:
                                    data = json.loads(response)
                                    if (
                                        data.get("type") == "pong"
                                        and "timestamp" in data
                                    ):
                                        latency = time.time() - data["timestamp"]
                                        stats["latency_samples"].append(
                                            latency * 1000
                                        )  # ms
                                except json.JSONDecodeError:
                                    pass

                            except asyncio.TimeoutError:
                                # No message received, continue
                                pass

                        except websockets.exceptions.ConnectionClosed:
                            stats["connection_drops"] += 1
                            print(
                                f"Client {client_id}: Connection dropped (drop #{stats['connection_drops']})"
                            )
                            break
                        except Exception as e:
                            stats["errors"] += 1
                            if stats["errors"] % 10 == 0:
                                print(
                                    f"Client {client_id}: Error #{stats['errors']}: {e}"
                                )

            except Exception as e:
                stats["connection_drops"] += 1
                print(
                    f"Client {client_id}: Failed to connect (attempt #{stats['connection_drops']}): {e}"
                )
                # Wait before reconnecting
                await asyncio.sleep(random.uniform(0.1, 1.0))

        stats["disconnected_at"] = time.time()
        return stats

    async def run_concurrent_stress_test(
        self, num_clients: int, duration: int, message_rate: float = 2.0
    ):
        """Run stress test with multiple concurrent clients"""
        print(
            f"🚀 WebSocket Stress Test: {num_clients} clients, {duration}s, {message_rate} msg/s per client"
        )
        print(f"Target load: {num_clients * message_rate} messages/s total")

        # Start all clients
        tasks = []
        for i in range(num_clients):
            task = asyncio.create_task(
                self.stress_client(i + 1, duration, message_rate)
            )
            tasks.append(task)
            # Stagger start times slightly
            await asyncio.sleep(0.05)

        # Wait for all clients to complete
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            print("\n🛑 Stress test interrupted")
            self.running = False
            results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if isinstance(r, dict)]

    async def run_connection_drop_test(self, num_clients: int = 10, duration: int = 60):
        """Test resilience to connection drops and reconnections"""
        print(
            f"🔥 Connection Drop Test: {num_clients} clients with forced reconnections"
        )

        async def dropping_client(client_id: int):
            """Client that periodically drops and reconnects"""
            stats = {"drops": 0, "reconnects": 0, "messages": 0, "errors": 0}
            uri = "ws://localhost:8765/ws"

            end_time = time.time() + duration

            while time.time() < end_time and self.running:
                try:
                    async with websockets.connect(uri) as websocket:
                        stats["reconnects"] += 1
                        connection_duration = random.uniform(
                            2, 10
                        )  # Stay connected 2-10 seconds
                        connection_end = time.time() + connection_duration

                        while (
                            time.time() < connection_end
                            and time.time() < end_time
                            and self.running
                        ):
                            try:
                                msg = {"type": "ping", "timestamp": time.time()}
                                await websocket.send(json.dumps(msg))
                                stats["messages"] += 1

                                # Listen for response
                                await asyncio.wait_for(websocket.recv(), timeout=0.5)

                                await asyncio.sleep(0.5)

                            except asyncio.TimeoutError:
                                continue
                            except Exception as e:
                                stats["errors"] += 1
                                break

                        # Deliberately close connection
                        stats["drops"] += 1

                except Exception as e:
                    stats["errors"] += 1

                # Wait before reconnecting
                await asyncio.sleep(random.uniform(0.5, 2.0))

            return stats

        tasks = [
            asyncio.create_task(dropping_client(i + 1)) for i in range(num_clients)
        ]
        results = await asyncio.gather(*tasks)

        return results

    def analyze_results(self, results: List[Dict], test_name: str):
        """Analyze and display test results"""
        if not results:
            print(f"❌ {test_name}: No successful clients")
            return

        print(f"\n📊 {test_name} Results:")
        print("=" * 60)

        # Connection stats
        successful_clients = len([r for r in results if r.get("connected_at")])
        total_messages_sent = sum(r.get("messages_sent", 0) for r in results)
        total_messages_received = sum(r.get("messages_received", 0) for r in results)
        total_errors = sum(r.get("errors", 0) for r in results)
        total_connection_drops = sum(r.get("connection_drops", 0) for r in results)
        total_reconnects = sum(r.get("reconnects", 0) for r in results)

        print(f"Successful clients: {successful_clients}/{len(results)}")
        print(f"Messages sent: {total_messages_sent:,}")
        print(f"Messages received: {total_messages_received:,}")
        print(
            f"Message success rate: {100 * total_messages_received / max(total_messages_sent, 1):.1f}%"
        )
        print(f"Connection drops: {total_connection_drops}")
        print(f"Reconnects: {total_reconnects}")
        print(f"Errors: {total_errors}")

        # Latency analysis
        all_latencies = []
        for r in results:
            all_latencies.extend(r.get("latency_samples", []))

        if all_latencies:
            all_latencies.sort()
            count = len(all_latencies)
            avg_latency = sum(all_latencies) / count
            median_latency = all_latencies[count // 2]
            p95_latency = all_latencies[int(count * 0.95)]
            p99_latency = all_latencies[int(count * 0.99)]

            print(
                f"Latency (ms): avg={avg_latency:.1f}, median={median_latency:.1f}, 95%={p95_latency:.1f}, 99%={p99_latency:.1f}"
            )

        # Rate analysis
        active_duration = max(
            [
                r.get("disconnected_at", time.time())
                - r.get("connected_at", time.time())
                for r in results
                if r.get("connected_at")
            ],
            default=1,
        )
        actual_rate = (
            total_messages_sent / active_duration if active_duration > 0 else 0
        )

        print(f"Actual message rate: {actual_rate:.1f} msg/s")
        print(f"Test duration: {active_duration:.1f}s")


async def main():
    """Main stress test runner"""
    tester = WebSocketStressTester()

    # Set up signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Received interrupt signal")
        tester.running = False

    signal.signal(signal.SIGINT, signal_handler)

    print("🔥 WebSocket Stress Test Suite")
    print("=" * 50)

    try:
        # Test 1: Moderate concurrent load
        print("\n🚀 Test 1: Moderate concurrent load (10 clients)")
        results1 = await tester.run_concurrent_stress_test(
            num_clients=10, duration=30, message_rate=2.0
        )
        tester.analyze_results(results1, "Moderate Load Test")

        # Test 2: High concurrent load
        print("\n🚀 Test 2: High concurrent load (20 clients)")
        results2 = await tester.run_concurrent_stress_test(
            num_clients=20, duration=20, message_rate=3.0
        )
        tester.analyze_results(results2, "High Load Test")

        # Test 3: Connection resilience
        print("\n🚀 Test 3: Connection drop resilience")
        results3 = await tester.run_connection_drop_test(num_clients=8, duration=30)

        print(f"\n📊 Connection Resilience Test Results:")
        print("=" * 60)
        total_drops = sum(r.get("drops", 0) for r in results3)
        total_reconnects = sum(r.get("reconnects", 0) for r in results3)
        total_messages = sum(r.get("messages", 0) for r in results3)
        total_errors = sum(r.get("errors", 0) for r in results3)

        print(f"Connection drops: {total_drops}")
        print(f"Reconnects: {total_reconnects}")
        print(f"Messages sent: {total_messages:,}")
        print(f"Errors: {total_errors}")
        print(f"Resilience rate: {100 * total_reconnects / max(total_drops, 1):.1f}%")

    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
