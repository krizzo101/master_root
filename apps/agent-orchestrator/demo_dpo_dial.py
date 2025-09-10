#!/usr/bin/env python3
"""
Demo: DPO Dial Control - Simple Level Adjustment

Shows how DPO is ON by default and easily adjustable.
"""

from src.dpo.enhancement_config import DEFAULT_CONFIG, DPOEnhancementConfig
from src.dpo.request_analyzer import RequestAnalyzer
from src.generic_orchestrator import AgentTask


def show_dial_effects(request: str = "Build a todo list app"):
    """Show what happens at each dial level."""

    print("=" * 70)
    print("🎛️  DPO ENHANCEMENT DIAL DEMO")
    print("=" * 70)
    print(f"\n📝 Request: '{request}'")
    print("=" * 70)

    # Start with default
    config = DPOEnhancementConfig(enabled=True, level=DEFAULT_CONFIG.level)

    print(f"\n📍 DEFAULT STATE: Level {config.level.to_number()} ({config.level.value})")
    print("   This is where DPO starts - smart but not excessive\n")

    # Show each level
    for level in range(6):
        config.dial(level)
        print(f"\n{'─' * 60}")
        print(f"DIAL SETTING: {level}")
        print(f"{'─' * 60}")

        if level == 0:
            print("⚫ OFF - No DPO enhancement")
            print("   • Just basic orchestrator behavior")
            print("   • Single task, no analysis")
            print("   • Example: 1 task (implement_todo_app)")

        elif level == 1:
            print("🟤 MINIMAL - Light touch")
            print(f"   • Max {config.max_agents} agents")
            print(f"   • Max {config.max_tasks_per_phase} tasks per phase")
            print("   • Basic validation only")
            print("   • Example: 2 tasks (analyze → implement)")

        elif level == 2:
            print("🟡 ESSENTIAL - Smart defaults (DEFAULT)")
            print(f"   • Max {config.max_agents} agents")
            print(f"   • Max {config.max_tasks_per_phase} tasks per phase")
            print("   • Quality gates: ✓")
            print("   • Testing: ✓")
            print("   • Documentation: ✗")
            print("   • Example: 4 tasks (analyze → design → implement → test)")

        elif level == 3:
            print("🟢 BALANCED - Well-rounded")
            print(f"   • Max {config.max_agents} agents")
            print(f"   • Max {config.max_tasks_per_phase} tasks per phase")
            print("   • Quality gates: ✓")
            print("   • Testing: ✓")
            print("   • Documentation: ✓")
            print("   • Example: 6 tasks (+ database design, + documentation)")

        elif level == 4:
            print("🔵 COMPREHENSIVE - Thorough")
            print(f"   • Max {config.max_agents} agents")
            print(f"   • Max {config.max_tasks_per_phase} tasks per phase")
            print("   • All enhancements enabled")
            print("   • Security & deployment included")
            print("   • Example: 10 tasks (+ security, + deployment, + monitoring)")

        elif level == 5:
            print("🟣 MAXIMUM - Everything (The Crazy Cool Stuff!)")
            print(f"   • Max {config.max_agents} agents!")
            print(f"   • Max {config.max_tasks_per_phase} tasks per phase")
            print("   • Infers missing requirements: ✓")
            print("   • Adds everything it can think of")
            print("   • Example: 15+ tasks (+ performance optimization, + A/B testing,")
            print("            + analytics, + multi-platform, + AI features...)")


def show_usage_examples():
    """Show how to use the dial in code."""
    print("\n" + "=" * 70)
    print("💻 USAGE EXAMPLES")
    print("=" * 70)

    print("\n1️⃣ Using default (Level 2 - Essential):")
    print(
        """
    # DPO is ON by default at Level 2
    orchestrator = EnhancedOrchestrator()  # DPO enabled automatically
    """
    )

    print("\n2️⃣ Dialing down for simple task:")
    print(
        """
    # Just need something basic
    config = DPOEnhancementConfig()
    config.dial(1)  # Minimal enhancement
    orchestrator = EnhancedOrchestrator(dpo_config=config)
    """
    )

    print("\n3️⃣ Dialing up for complex project:")
    print(
        """
    # Need comprehensive analysis
    config = DPOEnhancementConfig()
    config.dial(4)  # Comprehensive enhancement
    orchestrator = EnhancedOrchestrator(dpo_config=config)
    """
    )

    print("\n4️⃣ Going full power:")
    print(
        """
    # Want all the crazy cool stuff!
    config = DPOEnhancementConfig()
    config.dial(5)  # MAXIMUM POWER! 🚀
    orchestrator = EnhancedOrchestrator(dpo_config=config)
    """
    )

    print("\n5️⃣ Turning DPO off:")
    print(
        """
    # Don't want any enhancement
    config = DPOEnhancementConfig()
    config.dial(0)  # OFF
    orchestrator = EnhancedOrchestrator(dpo_config=config)
    """
    )


def show_quick_reference():
    """Show quick reference card."""
    print("\n" + "=" * 70)
    print("📋 QUICK REFERENCE")
    print("=" * 70)
    print(
        """
    Level | Name          | Agents | Tasks | Best For
    ------|---------------|--------|-------|---------------------------
      0   | OFF           |   1    |   1   | When you know exactly what you want
      1   | MINIMAL       |   3    |   2   | Simple, well-defined tasks
    ★ 2   | ESSENTIAL     |   6    |   4   | Most development tasks (DEFAULT)
      3   | BALANCED      |   8    |   4   | Professional projects
      4   | COMPREHENSIVE |  12    |   6   | Enterprise requirements
      5   | MAXIMUM       |  15    |   8   | When you want everything

    ★ = Default level
    """
    )


def main():
    """Run the dial demo."""
    show_dial_effects()
    show_usage_examples()
    show_quick_reference()

    print("\n" + "=" * 70)
    print("🎯 KEY POINTS")
    print("=" * 70)
    print(
        """
    ✅ DPO is ON by default at Level 2 (Essential)
    ✅ Simple dial from 0-5 to adjust enhancement
    ✅ Level 2-3 perfect for most tasks
    ✅ Level 5 when you want the crazy cool stuff
    ✅ Level 0 to turn it off completely
    ✅ config.dial(n) - that's all you need!
    """
    )


if __name__ == "__main__":
    main()
