#!/usr/bin/env python3
"""
Continuous Resource Utilization Monitor
Tracks CPU, Memory, Disk I/O, and Swap usage for 5 minutes with 35-second intervals
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime


class ResourceMonitor:
    def __init__(self):
        self.data_points = []
        self.start_time = None

    def get_cpu_load(self):
        """Get CPU load averages"""
        try:
            with open("/proc/loadavg", "r") as f:
                load = f.read().strip().split()
                return {
                    "1min": float(load[0]),
                    "5min": float(load[1]),
                    "15min": float(load[2]),
                }
        except:
            return {"1min": 0, "5min": 0, "15min": 0}

    def get_memory_usage(self):
        """Get memory usage statistics"""
        try:
            mem_info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().split()[0]
                        mem_info[key] = int(value) * 1024  # Convert KB to bytes

            total = mem_info.get("MemTotal", 0)
            available = mem_info.get("MemAvailable", 0)
            used = total - available

            return {
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "available_gb": available / (1024**3),
                "usage_percent": (used / total * 100) if total > 0 else 0,
                "buffers_gb": mem_info.get("Buffers", 0) / (1024**3),
                "cached_gb": mem_info.get("Cached", 0) / (1024**3),
            }
        except:
            return {"total_gb": 0, "used_gb": 0, "available_gb": 0, "usage_percent": 0}

    def get_swap_usage(self):
        """Get swap usage statistics"""
        try:
            with open("/proc/meminfo", "r") as f:
                swap_total = 0
                swap_free = 0
                for line in f:
                    if line.startswith("SwapTotal:"):
                        swap_total = int(line.split()[1]) * 1024
                    elif line.startswith("SwapFree:"):
                        swap_free = int(line.split()[1]) * 1024

                swap_used = swap_total - swap_free
                return {
                    "total_gb": swap_total / (1024**3),
                    "used_gb": swap_used / (1024**3),
                    "free_gb": swap_free / (1024**3),
                    "usage_percent": (swap_used / swap_total * 100)
                    if swap_total > 0
                    else 0,
                }
        except:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "usage_percent": 0}

    def get_disk_io(self):
        """Get disk I/O statistics"""
        try:
            io_stats = {}
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    fields = line.split()
                    if len(fields) >= 14:
                        device = fields[2]
                        # Skip loop devices and ram devices
                        if device.startswith(("loop", "ram")):
                            continue

                        reads = int(fields[3])
                        read_sectors = int(fields[5])
                        writes = int(fields[7])
                        write_sectors = int(fields[9])

                        io_stats[device] = {
                            "reads": reads,
                            "read_bytes": read_sectors
                            * 512,  # Assume 512 bytes per sector
                            "writes": writes,
                            "write_bytes": write_sectors * 512,
                        }

            # Calculate totals
            total_reads = sum(stats["reads"] for stats in io_stats.values())
            total_writes = sum(stats["writes"] for stats in io_stats.values())
            total_read_mb = sum(stats["read_bytes"] for stats in io_stats.values()) / (
                1024**2
            )
            total_write_mb = sum(
                stats["write_bytes"] for stats in io_stats.values()
            ) / (1024**2)

            return {
                "total_reads": total_reads,
                "total_writes": total_writes,
                "total_read_mb": total_read_mb,
                "total_write_mb": total_write_mb,
                "devices": io_stats,
            }
        except:
            return {
                "total_reads": 0,
                "total_writes": 0,
                "total_read_mb": 0,
                "total_write_mb": 0,
            }

    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        try:
            # Read /proc/stat twice with small interval for accurate CPU usage
            def read_cpu_times():
                with open("/proc/stat", "r") as f:
                    line = f.readline()
                    times = [int(x) for x in line.split()[1:]]
                    return times

            times1 = read_cpu_times()
            time.sleep(0.1)
            times2 = read_cpu_times()

            # Calculate CPU usage
            deltas = [t2 - t1 for t1, t2 in zip(times1, times2)]
            total_delta = sum(deltas)
            idle_delta = deltas[3]  # idle time is the 4th field

            if total_delta > 0:
                cpu_usage = 100.0 * (1.0 - idle_delta / total_delta)
            else:
                cpu_usage = 0.0

            return cpu_usage
        except:
            return 0.0

    def collect_metrics(self, iteration):
        """Collect all metrics for current iteration"""
        timestamp = datetime.now()
        elapsed = (
            (timestamp - self.start_time).total_seconds() if self.start_time else 0
        )

        metrics = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "iteration": iteration,
            "elapsed_seconds": elapsed,
            "cpu_load": self.get_cpu_load(),
            "cpu_usage": self.get_cpu_usage(),
            "memory": self.get_memory_usage(),
            "swap": self.get_swap_usage(),
            "disk_io": self.get_disk_io(),
        }

        self.data_points.append(metrics)
        return metrics

    def print_metrics(self, metrics):
        """Print current metrics in a formatted way"""
        print(f"\n{'='*60}")
        print(f"ITERATION {metrics['iteration']} - {metrics['timestamp']}")
        print(f"Elapsed: {metrics['elapsed_seconds']:.1f}s")
        print(f"{'='*60}")

        # CPU Information
        cpu_load = metrics["cpu_load"]
        cpu_usage = metrics["cpu_usage"]
        print(
            f"CPU Load Avg: 1min={cpu_load['1min']:.2f}, 5min={cpu_load['5min']:.2f}, 15min={cpu_load['15min']:.2f}"
        )
        print(f"CPU Usage: {cpu_usage:.1f}%")

        # Memory Information
        mem = metrics["memory"]
        print(
            f"Memory: {mem['used_gb']:.2f}GB/{mem['total_gb']:.2f}GB ({mem['usage_percent']:.1f}%)"
        )
        print(
            f"Available: {mem['available_gb']:.2f}GB, Buffers: {mem['buffers_gb']:.2f}GB, Cached: {mem['cached_gb']:.2f}GB"
        )

        # Swap Information
        swap = metrics["swap"]
        if swap["total_gb"] > 0:
            print(
                f"Swap: {swap['used_gb']:.2f}GB/{swap['total_gb']:.2f}GB ({swap['usage_percent']:.1f}%)"
            )
        else:
            print("Swap: Not configured")

        # Disk I/O Information
        io = metrics["disk_io"]
        print(
            f"Disk I/O: {io['total_reads']} reads ({io['total_read_mb']:.1f}MB), {io['total_writes']} writes ({io['total_write_mb']:.1f}MB)"
        )

        print(f"{'='*60}")

    def analyze_trends(self):
        """Analyze trends and patterns in collected data"""
        if len(self.data_points) < 2:
            return

        print(f"\n{'#'*80}")
        print("RESOURCE USAGE ANALYSIS AND TRENDS")
        print(f"{'#'*80}")

        # Extract time series data
        timestamps = [dp["elapsed_seconds"] for dp in self.data_points]
        cpu_loads = [dp["cpu_load"]["1min"] for dp in self.data_points]
        cpu_usage = [dp["cpu_usage"] for dp in self.data_points]
        mem_usage = [dp["memory"]["usage_percent"] for dp in self.data_points]
        swap_usage = [dp["swap"]["usage_percent"] for dp in self.data_points]

        # Calculate trends
        def calculate_trend(values):
            if len(values) < 2:
                return 0
            return (values[-1] - values[0]) / len(values)

        cpu_load_trend = calculate_trend(cpu_loads)
        cpu_usage_trend = calculate_trend(cpu_usage)
        mem_trend = calculate_trend(mem_usage)
        swap_trend = calculate_trend(swap_usage)

        print(f"\n📊 TREND ANALYSIS:")
        print(
            f"CPU Load (1min): {'📈' if cpu_load_trend > 0 else '📉' if cpu_load_trend < 0 else '➡️'} {cpu_load_trend:+.3f}/iteration"
        )
        print(
            f"CPU Usage: {'📈' if cpu_usage_trend > 0 else '📉' if cpu_usage_trend < 0 else '➡️'} {cpu_usage_trend:+.1f}%/iteration"
        )
        print(
            f"Memory Usage: {'📈' if mem_trend > 0 else '📉' if mem_trend < 0 else '➡️'} {mem_trend:+.1f}%/iteration"
        )
        print(
            f"Swap Usage: {'📈' if swap_trend > 0 else '📉' if swap_trend < 0 else '➡️'} {swap_trend:+.1f}%/iteration"
        )

        # Find peaks
        max_cpu_load = max(cpu_loads)
        max_cpu_usage = max(cpu_usage)
        max_mem = max(mem_usage)
        max_swap = max(swap_usage)

        peak_cpu_load_idx = cpu_loads.index(max_cpu_load)
        peak_cpu_usage_idx = cpu_usage.index(max_cpu_usage)
        peak_mem_idx = mem_usage.index(max_mem)

        print(f"\n🎯 PEAK USAGE PERIODS:")
        print(
            f"Highest CPU Load: {max_cpu_load:.2f} at iteration {peak_cpu_load_idx + 1}"
        )
        print(
            f"Highest CPU Usage: {max_cpu_usage:.1f}% at iteration {peak_cpu_usage_idx + 1}"
        )
        print(f"Highest Memory: {max_mem:.1f}% at iteration {peak_mem_idx + 1}")
        if max_swap > 0:
            peak_swap_idx = swap_usage.index(max_swap)
            print(f"Highest Swap: {max_swap:.1f}% at iteration {peak_swap_idx + 1}")

        # Calculate averages
        avg_cpu_load = sum(cpu_loads) / len(cpu_loads)
        avg_cpu_usage = sum(cpu_usage) / len(cpu_usage)
        avg_mem = sum(mem_usage) / len(mem_usage)
        avg_swap = (
            sum(swap_usage) / len(swap_usage) if any(s > 0 for s in swap_usage) else 0
        )

        print(f"\n📈 AVERAGE USAGE:")
        print(f"CPU Load (1min): {avg_cpu_load:.2f}")
        print(f"CPU Usage: {avg_cpu_usage:.1f}%")
        print(f"Memory: {avg_mem:.1f}%")
        if avg_swap > 0:
            print(f"Swap: {avg_swap:.1f}%")

        # Pattern analysis
        print(f"\n🔍 PATTERN ANALYSIS:")

        # Stability check
        cpu_stability = max(cpu_usage) - min(cpu_usage)
        mem_stability = max(mem_usage) - min(mem_usage)

        if cpu_stability < 5:
            print("✅ CPU usage is very stable (low variance)")
        elif cpu_stability < 15:
            print("⚠️ CPU usage shows moderate variation")
        else:
            print("🚨 CPU usage shows high variation - possible workload spikes")

        if mem_stability < 2:
            print("✅ Memory usage is very stable")
        elif mem_stability < 5:
            print("⚠️ Memory usage shows moderate variation")
        else:
            print("🚨 Memory usage shows significant variation")

        # System health assessment
        print(f"\n🏥 SYSTEM HEALTH ASSESSMENT:")

        if avg_cpu_usage < 50:
            print("✅ CPU utilization is healthy")
        elif avg_cpu_usage < 80:
            print("⚠️ CPU utilization is moderate")
        else:
            print("🚨 CPU utilization is high")

        if avg_mem < 70:
            print("✅ Memory utilization is healthy")
        elif avg_mem < 85:
            print("⚠️ Memory utilization is getting high")
        else:
            print("🚨 Memory utilization is critical")

        if avg_swap < 10:
            print("✅ Swap usage is minimal/healthy")
        else:
            print("⚠️ Swap is being used - may indicate memory pressure")

        print(f"\n{'#'*80}")

    def run_monitoring(self, duration_minutes=5, interval_seconds=35):
        """Run the monitoring for specified duration"""
        self.start_time = datetime.now()
        total_seconds = duration_minutes * 60
        iterations = int(total_seconds / interval_seconds) + 1

        print(f"🚀 Starting {duration_minutes}-minute resource monitoring")
        print(f"📅 Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Interval: {interval_seconds} seconds")
        print(f"🔄 Total iterations: {iterations}")
        print(f"⏱️ Total duration: ~{total_seconds} seconds")

        try:
            for i in range(iterations):
                # Collect and display metrics
                metrics = self.collect_metrics(i + 1)
                self.print_metrics(metrics)

                # Provide commentary
                if i == 0:
                    print(
                        "💡 Baseline metrics collected - establishing monitoring rhythm..."
                    )
                elif i == iterations // 3:
                    print(
                        "💡 One-third through monitoring - checking for early trends..."
                    )
                elif i == 2 * iterations // 3:
                    print("💡 Two-thirds complete - patterns should be emerging...")
                elif i == iterations - 1:
                    print("💡 Final iteration - preparing comprehensive analysis...")
                else:
                    # Dynamic commentary based on current vs previous iteration
                    if len(self.data_points) > 1:
                        prev = self.data_points[-2]
                        curr = metrics

                        cpu_change = curr["cpu_usage"] - prev["cpu_usage"]
                        mem_change = (
                            curr["memory"]["usage_percent"]
                            - prev["memory"]["usage_percent"]
                        )

                        comments = []
                        if abs(cpu_change) > 5:
                            direction = "increased" if cpu_change > 0 else "decreased"
                            comments.append(
                                f"CPU {direction} by {abs(cpu_change):.1f}%"
                            )

                        if abs(mem_change) > 1:
                            direction = "increased" if mem_change > 0 else "decreased"
                            comments.append(
                                f"Memory {direction} by {abs(mem_change):.1f}%"
                            )

                        if comments:
                            print(f"💡 Notable change: {', '.join(comments)}")
                        else:
                            print("💡 Stable resource usage since last check...")

                # Sleep until next iteration (except for last iteration)
                if i < iterations - 1:
                    print(
                        f"\n⏳ Sleeping {interval_seconds} seconds until next check..."
                    )
                    time.sleep(interval_seconds)

            # Final analysis
            self.analyze_trends()

        except KeyboardInterrupt:
            print(f"\n\n⚠️ Monitoring interrupted by user")
            if len(self.data_points) > 1:
                print("Analyzing partial data...")
                self.analyze_trends()
        except Exception as e:
            print(f"\n\n❌ Error during monitoring: {e}")
            if len(self.data_points) > 1:
                print("Analyzing collected data before error...")
                self.analyze_trends()


if __name__ == "__main__":
    monitor = ResourceMonitor()
    monitor.run_monitoring(duration_minutes=5, interval_seconds=35)
