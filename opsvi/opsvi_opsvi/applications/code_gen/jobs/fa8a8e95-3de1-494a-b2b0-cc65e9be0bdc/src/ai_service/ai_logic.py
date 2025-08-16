import logging
from typing import List, Dict
from datetime import datetime, timedelta
import numpy as np
from .models import Task, TeamMember

logger = logging.getLogger("ai_service.ai_logic")

# --- AI Simulations ---


def prioritize_tasks(tasks: List[Task], members: List[TeamMember]) -> Dict:
    """
    Return prioritized ordering of tasks based on importance, deadlines, and dependencies.
    Real implementation: Use transformer or ranking ML models on task+user data.
    """
    priorities = []
    for t in tasks:
        # Weight: importance + soonest deadline - dependency count - is unassigned penalty
        deadline_score = 0
        if t.deadline:
            try:
                delta = (
                    datetime.fromisoformat(t.deadline) - datetime.now()
                ).total_seconds() / 3600
                deadline_score = max(0, 10 - delta / 24)  # Higher if soon
            except Exception as e:
                logger.warning(f"Invalid deadline: {t.deadline}")
        assigned_factor = 0 if t.assigned_to else -2
        score = t.importance + deadline_score - len(t.dependencies) + assigned_factor
        priorities.append((t.id, score))
    priorities.sort(key=lambda x: -x[1])
    logger.info(f"Priority order: {[x[0] for x in priorities]}")
    return {"ordered_ids": [x[0] for x in priorities]}


def estimate_completion_times(tasks: List[Task]) -> Dict:
    """
    Use pretend ML regression over historical durations, importance, and description features.
    """
    output = {}
    rng = np.random.default_rng(seed=42)
    for t in tasks:
        if t.previous_duration:
            estimate = t.previous_duration * rng.uniform(0.8, 1.2)
        else:
            base = 4 + 2 * (10 - t.importance)  # Higher importance, less time assumed
            estimate = base * rng.uniform(0.8, 1.4)
        output[t.id] = round(max(1.0, estimate), 1)
    logger.info(f"Time estimates: {output}")
    return {"estimates": output}


def detect_dependencies(tasks: List[Task]) -> Dict:
    """
    Detect blocking relationships via NLP keyword overlap as a simulation.
    Real: use embedding similarity/NLP labelling.
    """
    result: Dict[str, List[str]] = {t.id: [] for t in tasks}
    n = len(tasks)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a, b = tasks[i], tasks[j]
            keywords_a = set(a.title.lower().split() + a.description.lower().split())
            keywords_b = set(b.title.lower().split() + b.description.lower().split())
            overlap = keywords_a & keywords_b
            if len(overlap) > 2:  # Magic threshold
                result[a.id].append(b.id)
    logger.info(f"Detected dependencies: {result}")
    return {"dependencies": result}


def suggest_optimal_scheduling(tasks: List[Task], members: List[TeamMember]) -> Dict:
    """
    Assign tasks to members, respecting availability/role, schedule so dependencies are honored.
    Use a simple greedy/deterministic simulation; can be replaced with OR-tools ML scheduling.
    """
    schedule = {}
    member_queue = sorted(members, key=lambda x: -x.skill_level)
    # Build dependency graph
    dep_graph = {t.id: set(t.dependencies) for t in tasks}
    task_map = {t.id: t for t in tasks}
    scheduled_set = set()
    day = 0
    while len(scheduled_set) < len(tasks):
        for t in tasks:
            if t.id in scheduled_set:
                continue
            if dep_graph[t.id] and not dep_graph[t.id].issubset(scheduled_set):
                continue
            # Assign to available member
            chosen = member_queue[day % len(member_queue)]
            start_time = (datetime.now() + timedelta(days=day)).isoformat()
            est_duration = t.estimated_duration or 4.0
            end_time = (
                datetime.fromisoformat(start_time) + timedelta(hours=est_duration)
            ).isoformat()
            schedule[t.id] = {
                "assigned_to": chosen.id,
                "start": start_time,
                "end": end_time,
            }
            scheduled_set.add(t.id)
        day += 1
    logger.info(f"Suggested schedule: {schedule}")
    return {"schedules": schedule}
