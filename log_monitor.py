#!/usr/bin/env python3
"""
Continuous System Log Monitor
Monitors system logs for 5 minutes with 40-second intervals
"""

import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime


class LogMonitor:
    def __init__(self):
        self.iteration = 0
        self.start_time = datetime.now()
        self.patterns = defaultdict(list)
        self.error_counts = Counter()
        self.log_stats = []
        self.auth_accessible = False

    def check_log_accessibility(self):
        """Check which log files are accessible"""
        log_files = [
            "/var/log/syslog",
            "/var/log/auth.log",
            "/var/log/kern.log",
            "/var/log/messages",
        ]

        accessible = []
        for log_file in log_files:
            if os.path.exists(log_file) and os.access(log_file, os.R_OK):
                accessible.append(log_file)

        self.auth_accessible = "/var/log/auth.log" in accessible
        return accessible

    def get_recent_syslog(self, lines=50):
        """Get recent syslog entries"""
        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), "/var/log/syslog"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split("\n") if result.returncode == 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return []

    def get_dmesg_output(self, lines=50):
        """Get recent dmesg output"""
        try:
            result = subprocess.run(
                ["dmesg", "--time-format=ctime", "-T"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[-lines:]
            return []
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return []

    def get_auth_log(self, lines=30):
        """Get recent auth log entries if accessible"""
        if not self.auth_accessible:
            return []
        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), "/var/log/auth.log"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split("\n") if result.returncode == 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return []

    def analyze_log_entry(self, entry):
        """Analyze a single log entry for patterns and errors"""
        if not entry.strip():
            return None

        # Extract timestamp, service, and message
        parts = entry.split(" ", 4)
        if len(parts) < 4:
            return None

        timestamp = " ".join(parts[:3])
        service = parts[3] if len(parts) > 3 else "unknown"
        message = parts[4] if len(parts) > 4 else ""

        # Identify log level/type
        log_type = "info"
        if any(word in entry.lower() for word in ["error", "err", "failed", "failure"]):
            log_type = "error"
        elif any(word in entry.lower() for word in ["warn", "warning"]):
            log_type = "warning"
        elif any(word in entry.lower() for word in ["crit", "critical", "fatal"]):
            log_type = "critical"

        return {
            "timestamp": timestamp,
            "service": service,
            "message": message,
            "type": log_type,
            "raw": entry,
        }

    def detect_patterns(self, entries):
        """Detect patterns in log entries"""
        patterns = {
            "repeated_errors": defaultdict(int),
            "service_activity": defaultdict(int),
            "time_patterns": defaultdict(int),
        }

        for entry in entries:
            analyzed = self.analyze_log_entry(entry)
            if not analyzed:
                continue

            # Count service activity
            patterns["service_activity"][analyzed["service"]] += 1

            # Count repeated error messages
            if analyzed["type"] in ["error", "warning", "critical"]:
                # Normalize error message for pattern detection
                normalized_msg = re.sub(r"\d+", "X", analyzed["message"][:100])
                patterns["repeated_errors"][normalized_msg] += 1

            # Time pattern (hour)
            try:
                hour = datetime.strptime(
                    analyzed["timestamp"].split()[2], "%H:%M:%S"
                ).hour
                patterns["time_patterns"][hour] += 1
            except:
                pass

        return patterns

    def run_analysis_iteration(self):
        """Run a single analysis iteration"""
        self.iteration += 1
        current_time = datetime.now()
        elapsed = (current_time - self.start_time).total_seconds()

        print(f"\n{'='*60}")
        print(f"LOG ANALYSIS ITERATION {self.iteration}/8")
        print(f"Time: {current_time.strftime('%H:%M:%S')} | Elapsed: {elapsed:.1f}s")
        print(f"{'='*60}")

        # Get log data
        syslog_entries = self.get_recent_syslog(50)
        dmesg_entries = self.get_dmesg_output(50)
        auth_entries = self.get_auth_log(30) if self.auth_accessible else []

        # Analyze syslog
        if syslog_entries:
            print(f"\n📋 SYSLOG ANALYSIS ({len(syslog_entries)} entries):")
            syslog_patterns = self.detect_patterns(syslog_entries)

            # Show recent errors
            recent_errors = [
                e
                for e in syslog_entries[-10:]
                if any(word in e.lower() for word in ["error", "warn", "fail", "crit"])
            ]
            if recent_errors:
                print("  🚨 Recent Errors/Warnings:")
                for error in recent_errors[-3:]:
                    print(f"    • {error}")
            else:
                print("  ✅ No recent errors in syslog")

            # Service activity
            top_services = sorted(
                syslog_patterns["service_activity"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]
            print("  📊 Top Active Services:")
            for service, count in top_services:
                print(f"    • {service}: {count} entries")
        else:
            print("\n📋 SYSLOG: Not accessible or empty")

        # Analyze dmesg
        if dmesg_entries:
            print(f"\n🔧 DMESG ANALYSIS ({len(dmesg_entries)} entries):")
            dmesg_errors = [
                e
                for e in dmesg_entries
                if any(
                    word in e.lower()
                    for word in ["error", "warn", "fail", "oops", "bug"]
                )
            ]
            if dmesg_errors:
                print("  🚨 Kernel Issues:")
                for error in dmesg_errors[-2:]:
                    print(f"    • {error}")
            else:
                print("  ✅ No kernel errors detected")

            # Show recent dmesg activity
            print("  📝 Recent Kernel Messages:")
            for msg in dmesg_entries[-3:]:
                print(f"    • {msg}")
        else:
            print("\n🔧 DMESG: Not accessible")

        # Analyze auth log
        if auth_entries:
            print(f"\n🔐 AUTH LOG ANALYSIS ({len(auth_entries)} entries):")
            auth_errors = [
                e
                for e in auth_entries
                if any(word in e.lower() for word in ["failed", "invalid", "error"])
            ]
            if auth_errors:
                print("  🚨 Authentication Issues:")
                for error in auth_errors[-2:]:
                    print(f"    • {error}")
            else:
                print("  ✅ No authentication errors")
        else:
            print("\n🔐 AUTH LOG: Not accessible")

        # Store statistics for final summary
        iteration_stats = {
            "iteration": self.iteration,
            "time": current_time,
            "syslog_count": len(syslog_entries),
            "dmesg_count": len(dmesg_entries),
            "auth_count": len(auth_entries),
            "syslog_errors": len(
                [
                    e
                    for e in syslog_entries
                    if any(word in e.lower() for word in ["error", "warn", "fail"])
                ]
            ),
            "dmesg_errors": len(
                [
                    e
                    for e in dmesg_entries
                    if any(word in e.lower() for word in ["error", "warn", "fail"])
                ]
            ),
        }
        self.log_stats.append(iteration_stats)

        print(f"\n📈 ITERATION SUMMARY:")
        print(
            f"  • Syslog entries: {iteration_stats['syslog_count']} ({iteration_stats['syslog_errors']} errors)"
        )
        print(
            f"  • Dmesg entries: {iteration_stats['dmesg_count']} ({iteration_stats['dmesg_errors']} errors)"
        )
        print(f"  • Auth entries: {iteration_stats['auth_count']}")

        return iteration_stats

    def generate_final_summary(self):
        """Generate comprehensive analysis summary"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE 5-MINUTE LOG ANALYSIS SUMMARY")
        print(f"{'='*80}")

        total_time = (datetime.now() - self.start_time).total_seconds()
        print(f"📊 MONITORING OVERVIEW:")
        print(f"  • Duration: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"  • Iterations: {len(self.log_stats)}")
        print(f"  • Interval: ~40 seconds")

        if self.log_stats:
            # Aggregate statistics
            total_syslog = sum(s["syslog_count"] for s in self.log_stats)
            total_dmesg = sum(s["dmesg_count"] for s in self.log_stats)
            total_auth = sum(s["auth_count"] for s in self.log_stats)
            total_syslog_errors = sum(s["syslog_errors"] for s in self.log_stats)
            total_dmesg_errors = sum(s["dmesg_errors"] for s in self.log_stats)

            print(f"\n📈 AGGREGATE STATISTICS:")
            print(f"  • Total syslog entries analyzed: {total_syslog}")
            print(f"  • Total dmesg entries analyzed: {total_dmesg}")
            print(f"  • Total auth entries analyzed: {total_auth}")
            print(f"  • Syslog errors/warnings: {total_syslog_errors}")
            print(f"  • Kernel errors/warnings: {total_dmesg_errors}")

            print(f"\n🔍 TREND ANALYSIS:")
            if len(self.log_stats) > 1:
                syslog_trend = (
                    self.log_stats[-1]["syslog_count"]
                    - self.log_stats[0]["syslog_count"]
                )
                error_trend = (
                    self.log_stats[-1]["syslog_errors"]
                    - self.log_stats[0]["syslog_errors"]
                )
                print(
                    f"  • Syslog activity trend: {'+' if syslog_trend > 0 else ''}{syslog_trend} entries"
                )
                print(
                    f"  • Error trend: {'+' if error_trend > 0 else ''}{error_trend} errors"
                )
            else:
                print("  • Insufficient data for trend analysis")

            # System health assessment
            avg_errors_per_iteration = (
                total_syslog_errors / len(self.log_stats) if self.log_stats else 0
            )
            print(f"\n🏥 SYSTEM HEALTH ASSESSMENT:")
            if avg_errors_per_iteration == 0:
                print("  • Status: EXCELLENT - No errors detected")
            elif avg_errors_per_iteration < 2:
                print("  • Status: GOOD - Minimal error activity")
            elif avg_errors_per_iteration < 5:
                print("  • Status: FAIR - Moderate error activity")
            else:
                print("  • Status: POOR - High error activity detected")

            print(f"  • Average errors per iteration: {avg_errors_per_iteration:.1f}")

        print(f"\n✅ MONITORING COMPLETE")
        print(f"{'='*80}")


def main():
    monitor = LogMonitor()

    print("🚀 Starting 5-minute continuous log monitoring...")
    print("⏱️  Running 8 iterations with 40-second intervals")

    # Check log accessibility
    accessible_logs = monitor.check_log_accessibility()
    print(f"📁 Accessible log files: {accessible_logs}")

    try:
        for i in range(8):  # 8 iterations * 40 seconds ≈ 5.3 minutes
            monitor.run_analysis_iteration()

            if i < 7:  # Don't sleep after the last iteration
                print(f"\n⏳ Sleeping 40 seconds until next iteration...")
                time.sleep(40)

    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")

    finally:
        monitor.generate_final_summary()


if __name__ == "__main__":
    main()
