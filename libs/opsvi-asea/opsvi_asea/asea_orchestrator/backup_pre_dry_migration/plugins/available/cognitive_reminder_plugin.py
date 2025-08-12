from typing import List, Any, Optional, Dict
import random
from datetime import datetime
from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class CognitiveReminderPlugin(BasePlugin):
    """
    Provides cognitive reminders and thinking prompts to enhance agent reasoning.
    Simple, immediate value approach to improve thinking patterns.
    """

    def __init__(self):
        super().__init__()
        self.reminder_categories = {
            "research": [
                "Perform research and use advanced cognitive reasoning",
                "Gather evidence before drawing conclusions",
                "Research multiple perspectives on this topic",
                "What information do you need to answer this properly?",
                "Look for authoritative sources and recent developments",
            ],
            "critical_thinking": [
                "Challenge your initial assumptions",
                "Consider multiple perspectives before concluding",
                "What evidence supports or contradicts this view?",
                "What are the potential counterarguments?",
                "Question the obvious - what might you be missing?",
            ],
            "systematic_approach": [
                "Break down complex problems into manageable parts",
                "Apply systematic analysis to this challenge",
                "What is the logical sequence of steps here?",
                "Consider both immediate and long-term implications",
                "Structure your reasoning from first principles",
            ],
            "validation": [
                "Verify your conclusions with concrete evidence",
                "Test your reasoning against real-world examples",
                "What would prove this approach wrong?",
                "How can you validate these claims?",
                "Cross-check your findings with multiple sources",
            ],
            "creativity": [
                "Think outside conventional approaches",
                "What unconventional solutions might work?",
                "Consider analogies from other domains",
                "What would an expert in X field suggest?",
                "Combine ideas in novel ways",
            ],
            "completeness": [
                "Have you addressed all aspects of the question?",
                "What important details might be missing?",
                "Consider the user's underlying needs",
                "What follow-up questions should you anticipate?",
                "Ensure your response is actionable and complete",
            ],
        }

    @staticmethod
    def get_name() -> str:
        return "cognitive_reminder"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize cognitive reminder system."""
        self.event_bus = event_bus

        # Load custom reminders if provided
        custom_reminders = config.config.get("custom_reminders", {})
        if custom_reminders:
            self.reminder_categories.update(custom_reminders)

        print(
            f"Cognitive Reminder initialized with {len(self.reminder_categories)} reminder categories"
        )

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute cognitive reminder operations."""
        try:
            params = context.state
            action = params.get("action", "get_reminders")

            if action == "get_reminders":
                return await self._get_reminders(params)
            elif action == "get_specific_reminder":
                return await self._get_specific_reminder(params)
            elif action == "evaluate_thinking":
                return await self._evaluate_thinking(params)
            else:
                return PluginResult(
                    success=False, error_message=f"Unknown action: {action}"
                )

        except Exception as e:
            return PluginResult(
                success=False, error_message=f"Cognitive reminder error: {str(e)}"
            )

    async def _get_reminders(self, params: Dict[str, Any]) -> PluginResult:
        """Get cognitive reminders based on task type."""
        task_type = params.get("task_type", "general")
        num_reminders = params.get("num_reminders", 3)
        user_prompt = params.get("user_prompt", "")

        # Determine relevant reminder categories based on task analysis
        relevant_categories = self._analyze_task_needs(user_prompt, task_type)

        # Select reminders from relevant categories
        selected_reminders = []
        for category in relevant_categories:
            if category in self.reminder_categories:
                category_reminders = self.reminder_categories[category]
                selected_reminders.extend(
                    random.sample(category_reminders, min(2, len(category_reminders)))
                )

        # If not enough reminders, add from general categories
        if len(selected_reminders) < num_reminders:
            all_reminders = []
            for reminders in self.reminder_categories.values():
                all_reminders.extend(reminders)

            additional_needed = num_reminders - len(selected_reminders)
            additional_reminders = random.sample(
                all_reminders, min(additional_needed, len(all_reminders))
            )
            selected_reminders.extend(additional_reminders)

        # Limit to requested number
        final_reminders = selected_reminders[:num_reminders]

        return PluginResult(
            success=True,
            data={
                "reminders": final_reminders,
                "relevant_categories": relevant_categories,
                "task_type": task_type,
                "reminder_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_available": sum(
                        len(r) for r in self.reminder_categories.values()
                    ),
                    "categories_used": len(relevant_categories),
                },
            },
        )

    async def _get_specific_reminder(self, params: Dict[str, Any]) -> PluginResult:
        """Get reminders from specific category."""
        category = params.get("category")
        num_reminders = params.get("num_reminders", 1)

        if category not in self.reminder_categories:
            return PluginResult(
                success=False,
                error_message=f"Category '{category}' not found. Available: {list(self.reminder_categories.keys())}",
            )

        category_reminders = self.reminder_categories[category]
        selected = random.sample(
            category_reminders, min(num_reminders, len(category_reminders))
        )

        return PluginResult(
            success=True,
            data={
                "reminders": selected,
                "category": category,
                "total_in_category": len(category_reminders),
            },
        )

    async def _evaluate_thinking(self, params: Dict[str, Any]) -> PluginResult:
        """Evaluate if thinking approach needs specific reminders."""
        reasoning_text = params.get("reasoning_text", "")

        # Simple analysis of reasoning patterns
        evaluation = {
            "needs_research": self._needs_research_reminder(reasoning_text),
            "needs_critical_thinking": self._needs_critical_thinking_reminder(
                reasoning_text
            ),
            "needs_systematic_approach": self._needs_systematic_reminder(
                reasoning_text
            ),
            "needs_validation": self._needs_validation_reminder(reasoning_text),
            "needs_completeness_check": self._needs_completeness_reminder(
                reasoning_text
            ),
        }

        # Generate targeted reminders based on evaluation
        targeted_reminders = []
        for need, is_needed in evaluation.items():
            if is_needed:
                category = (
                    need.replace("needs_", "")
                    .replace("_reminder", "")
                    .replace("_check", "")
                )
                if category in self.reminder_categories:
                    reminder = random.choice(self.reminder_categories[category])
                    targeted_reminders.append(
                        {
                            "reminder": reminder,
                            "category": category,
                            "reason": f"Analysis suggests {category} improvement needed",
                        }
                    )

        return PluginResult(
            success=True,
            data={
                "evaluation": evaluation,
                "targeted_reminders": targeted_reminders,
                "needs_improvement": any(evaluation.values()),
                "analysis_timestamp": datetime.now().isoformat(),
            },
        )

    def _analyze_task_needs(self, user_prompt: str, task_type: str) -> List[str]:
        """Analyze what types of cognitive reminders are needed."""
        relevant_categories = []

        prompt_lower = user_prompt.lower()

        # Research indicators
        if any(
            word in prompt_lower
            for word in ["research", "find", "information", "data", "study", "analysis"]
        ):
            relevant_categories.append("research")

        # Critical thinking indicators
        if any(
            word in prompt_lower
            for word in ["evaluate", "compare", "assess", "judge", "decide", "choose"]
        ):
            relevant_categories.append("critical_thinking")

        # Systematic approach indicators
        if any(
            word in prompt_lower
            for word in ["plan", "strategy", "framework", "systematic", "methodology"]
        ):
            relevant_categories.append("systematic_approach")

        # Creativity indicators
        if any(
            word in prompt_lower
            for word in ["creative", "innovative", "novel", "unique", "brainstorm"]
        ):
            relevant_categories.append("creativity")

        # Validation indicators
        if any(
            word in prompt_lower
            for word in ["validate", "verify", "confirm", "check", "test"]
        ):
            relevant_categories.append("validation")

        # Always include completeness for comprehensive responses
        relevant_categories.append("completeness")

        # Default categories if none detected
        if not relevant_categories:
            relevant_categories = [
                "research",
                "critical_thinking",
                "systematic_approach",
            ]

        return list(set(relevant_categories))  # Remove duplicates

    def _needs_research_reminder(self, text: str) -> bool:
        """Check if reasoning text suggests need for more research."""
        research_indicators = [
            "i think",
            "i believe",
            "probably",
            "maybe",
            "seems like",
        ]
        return any(indicator in text.lower() for indicator in research_indicators)

    def _needs_critical_thinking_reminder(self, text: str) -> bool:
        """Check if reasoning needs more critical analysis."""
        # Look for lack of questioning or alternative perspectives
        question_words = ["why", "how", "what if", "however", "but", "although"]
        return len([w for w in question_words if w in text.lower()]) < 2

    def _needs_systematic_reminder(self, text: str) -> bool:
        """Check if reasoning needs more systematic approach."""
        systematic_indicators = ["first", "second", "then", "next", "step", "phase"]
        return len([w for w in systematic_indicators if w in text.lower()]) < 2

    def _needs_validation_reminder(self, text: str) -> bool:
        """Check if reasoning needs validation."""
        validation_indicators = ["evidence", "proof", "confirmed", "tested", "verified"]
        return not any(indicator in text.lower() for indicator in validation_indicators)

    def _needs_completeness_reminder(self, text: str) -> bool:
        """Check if reasoning might be incomplete."""
        # Simple heuristic: very short responses might be incomplete
        return len(text.split()) < 50

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="get_reminders",
                description="Get cognitive reminders based on task type",
            ),
            Capability(
                name="get_specific_reminder",
                description="Get reminders from specific category",
            ),
            Capability(
                name="evaluate_thinking",
                description="Evaluate thinking approach and suggest targeted reminders",
            ),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data."""
        return ValidationResult(is_valid=True, errors=[])

    @staticmethod
    def get_dependencies() -> List[str]:
        """External dependencies."""
        return []

    @staticmethod
    def get_configuration_schema() -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "custom_reminders": {
                    "type": "object",
                    "description": "Custom reminder categories and messages",
                }
            },
        }
