"""
Dynamic Agent Proxy (DAP) Module

This module implements the Dynamic Agent Proxy that analyzes user prompts,
creates specialized agents optimized for each request, and transparently
proxies the interaction through these agents.
"""

import json
import logging
import time
import uuid
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utils.config import Config
from ..utils.exceptions import AgentCreationError, PromptAnalysisError
from .agent_base import AgentBase
from .specialized_agent import SpecializedAgent


class DynamicAgentProxy(AgentBase):
    """
    Dynamic Agent Proxy (DAP) that analyzes user prompts and creates
    specialized agents optimized for each specific request.

    The DAP serves as an intelligent meta-agent that:
    1. Analyzes each user prompt for intent, domain, complexity, etc.
    2. Creates or evolves agent designs optimized for the specific request
    3. Instantiates specialized agents with tailored configurations
    4. Proxies the interaction transparently
    5. Maintains memory of previous agent designs
    """

    def __init__(self) -> None:
        """Initialize the Dynamic Agent Proxy with an empty agent memory."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = Config()

        # Use OrderedDict to maintain insertion order for memory limit enforcement
        self.agent_memory: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.memory_size = self.config.get("smart_proxy.memory_size", 10)

        self.logger.info(
            "Dynamic Agent Proxy initialized with memory size %d", self.memory_size
        )

    def process(
        self, prompt: str, conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user prompt by analyzing it and creating a specialized agent.

        Args:
            prompt: The user's prompt
            conversation_history: Previous conversation turns

        Returns:
            The response from the specialized agent

        Raises:
            AgentCreationError: If agent creation fails
            PromptAnalysisError: If prompt analysis fails
        """
        start_time = time.time()
        self.logger.info(
            "DAP processing prompt: %s",
            prompt[:50] + "..." if len(prompt) > 50 else prompt,
        )

        try:
            # 1. Analyze the prompt
            prompt_analysis = self._analyze_prompt(prompt, conversation_history)

            # 2. Check if we should modify previous agent or create new one
            previous_agent_id = self._get_previous_agent_id(conversation_history)
            if previous_agent_id and previous_agent_id in self.agent_memory:
                # Evaluate if previous agent should be reused, modified, or replaced
                agent_config = self._evolve_agent_design(
                    previous_agent_id, prompt, prompt_analysis, conversation_history
                )
            else:
                # Create new agent design
                agent_config = self._create_agent_design(
                    prompt, prompt_analysis, conversation_history
                )

            # 3. Instantiate the specialized agent
            specialized_agent = SpecializedAgent(agent_config)

            # 4. Store the agent design for future reference and manage memory size
            agent_id = agent_config["agent_id"]
            self.agent_memory[agent_id] = agent_config
            self._enforce_memory_limit()

            # 5. Process the prompt with the specialized agent
            response = specialized_agent.process(prompt, conversation_history)

            # 6. Update response with agent ID for tracking
            if isinstance(response, dict):
                response["agent_id"] = agent_id

            elapsed_time = time.time() - start_time
            self.logger.info(
                "DAP processed prompt in %.2f seconds with agent %s",
                elapsed_time,
                agent_id,
            )

            return response

        except PromptAnalysisError as e:
            self.logger.error("Prompt analysis failed: %s", str(e))
            raise
        except AgentCreationError as e:
            self.logger.error("Agent creation failed: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error in DAP: %s", str(e), exc_info=True)
            raise AgentCreationError(f"Failed to process prompt: {str(e)}")

    def _enforce_memory_limit(self) -> None:
        """Ensure the agent memory doesn't exceed the configured limit."""
        while len(self.agent_memory) > self.memory_size:
            self.agent_memory.popitem(last=False)  # Remove oldest item

    def _analyze_prompt(
        self, prompt: str, conversation_history: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze the prompt to determine domain, intent, complexity, etc.

        Args:
            prompt: The user's prompt
            conversation_history: Previous conversation turns

        Returns:
            Analysis results containing domain, intent, complexity, etc.

        Raises:
            PromptAnalysisError: If prompt analysis fails
        """
        try:
            # In a full implementation, this would use more sophisticated NLP techniques,
            # potentially making API calls to another model specialized in classification.
            # For now, using simplified detection methods.

            analysis = {
                "primary_domain": self._detect_domain(prompt),
                "intent_classification": self._detect_intent(prompt),
                "complexity_level": self._estimate_complexity(prompt),
                "emotional_tone": self._detect_tone(prompt),
                "specialized_knowledge_areas": self._identify_knowledge_areas(prompt),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            return analysis
        except Exception as e:
            raise PromptAnalysisError(f"Failed to analyze prompt: {str(e)}")

    def _create_agent_design(
        self,
        prompt: str,
        analysis: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Create a new agent design optimized for the specific prompt.

        Args:
            prompt: The user's prompt
            analysis: Results from prompt analysis
            conversation_history: Previous conversation turns

        Returns:
            Complete agent configuration including system message, parameters, etc.

        Raises:
            AgentCreationError: If agent design creation fails
        """
        try:
            # Generate a unique ID for the agent
            agent_id = f"agent_{uuid.uuid4().hex[:8]}_{int(time.time())}"

            # Determine optimal parameters based on analysis
            temperature = self._get_temperature_for_task(analysis)
            max_tokens = self._get_max_tokens_for_task(analysis)

            # Generate appropriate system message
            system_message = self._generate_system_message(analysis, prompt)

            # Create the complete agent configuration
            agent_config = {
                "agent_id": agent_id,
                "creation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "request_prompt": prompt,
                "prompt_analysis": analysis,
                "agent_configuration": {
                    "system_message": system_message,
                    "model": self._select_model_for_task(analysis),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                },
                "contextual_data": self._extract_contextual_data(conversation_history),
                "performance_metrics": {
                    "response_time": None,  # Will be populated after response
                    "token_usage": {"prompt": 0, "completion": 0, "total": 0},
                    "estimated_quality": None,
                },
                "evolution_history": [],
            }

            return agent_config

        except Exception as e:
            raise AgentCreationError(f"Failed to create agent design: {str(e)}")

    def _evolve_agent_design(
        self,
        previous_agent_id: str,
        prompt: str,
        analysis: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Evolve a previous agent design based on the new prompt.

        Args:
            previous_agent_id: ID of the previous agent to evolve from
            prompt: The new user prompt
            analysis: Results from prompt analysis
            conversation_history: Previous conversation turns

        Returns:
            Updated agent configuration

        Raises:
            AgentCreationError: If agent evolution fails
        """
        try:
            previous_config = self.agent_memory[previous_agent_id]

            # Determine what kind of evolution is needed
            prev_analysis = previous_config["prompt_analysis"]
            domain_changed = (
                prev_analysis["primary_domain"] != analysis["primary_domain"]
            )
            intent_changed = (
                prev_analysis["intent_classification"]
                != analysis["intent_classification"]
            )
            complexity_change = abs(
                prev_analysis.get("complexity_level", 3)
                - analysis.get("complexity_level", 3)
            )

            if domain_changed or intent_changed:
                # Major changes - create new agent with reference to previous
                new_config = self._create_agent_design(
                    prompt, analysis, conversation_history
                )
                new_config["evolution_history"].append(
                    {
                        "previous_agent_id": previous_agent_id,
                        "modification_type": "replace",
                        "modification_reason": f"Domain or intent change: domain_changed={domain_changed}, intent_changed={intent_changed}",
                    }
                )
                return new_config
            else:
                # Minor changes - modify existing agent
                new_config = previous_config.copy()
                new_config[
                    "agent_id"
                ] = f"agent_{uuid.uuid4().hex[:8]}_{int(time.time())}"
                new_config["prompt_analysis"] = analysis
                new_config["request_prompt"] = prompt

                # Update system message with refinements
                new_config["agent_configuration"][
                    "system_message"
                ] = self._refine_system_message(
                    previous_config["agent_configuration"]["system_message"],
                    analysis,
                    prompt,
                )

                # Adjust parameters if needed
                if complexity_change > 1:
                    new_config["agent_configuration"][
                        "temperature"
                    ] = self._get_temperature_for_task(analysis)
                    new_config["agent_configuration"][
                        "max_tokens"
                    ] = self._get_max_tokens_for_task(analysis)

                # Update evolution history
                new_config["evolution_history"].append(
                    {
                        "previous_agent_id": previous_agent_id,
                        "modification_type": "update",
                        "modification_reason": "Refinement for similar prompt type",
                    }
                )

                return new_config

        except Exception as e:
            raise AgentCreationError(f"Failed to evolve agent design: {str(e)}")

    # Helper methods for agent design

    def _detect_domain(self, prompt: str) -> str:
        """
        Detect the primary knowledge domain of the prompt.

        Args:
            prompt: The user's prompt

        Returns:
            Detected domain (e.g., "general", "technology", "science", etc.)
        """
        # Simple keyword-based domain detection
        # In a full implementation, use more sophisticated NLP or ML techniques
        domains = {
            "technology": [
                "computer",
                "software",
                "hardware",
                "programming",
                "code",
                "app",
                "tech",
            ],
            "science": [
                "science",
                "scientific",
                "biology",
                "physics",
                "chemistry",
                "research",
            ],
            "business": [
                "business",
                "finance",
                "marketing",
                "economics",
                "management",
                "strategy",
            ],
            "creative": [
                "write",
                "story",
                "poem",
                "creative",
                "design",
                "art",
                "music",
            ],
            "academic": [
                "paper",
                "thesis",
                "research",
                "study",
                "academic",
                "university",
            ],
        }

        prompt_lower = prompt.lower()
        for domain, keywords in domains.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return domain

        return "general"

    def _detect_intent(self, prompt: str) -> str:
        """
        Classify the intent of the prompt.

        Args:
            prompt: The user's prompt

        Returns:
            Detected intent (e.g., "information", "creation", "analysis", etc.)
        """
        # Simple keyword-based intent detection
        # In a full implementation, use more sophisticated NLP or ML techniques
        intents = {
            "information": [
                "what",
                "how",
                "explain",
                "describe",
                "tell me about",
                "information",
            ],
            "creation": ["create", "write", "generate", "develop", "design", "make"],
            "analysis": [
                "analyze",
                "evaluate",
                "compare",
                "assess",
                "review",
                "examine",
            ],
            "problem_solving": [
                "solve",
                "fix",
                "debug",
                "troubleshoot",
                "resolve",
                "solution",
            ],
            "code": [
                "code",
                "function",
                "program",
                "script",
                "implement",
                "coding",
                "algorithm",
            ],
        }

        prompt_lower = prompt.lower()
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return intent

        return "information"

    def _estimate_complexity(self, prompt: str) -> int:
        """
        Estimate the complexity level of the prompt (1-5).

        Args:
            prompt: The user's prompt

        Returns:
            Complexity level from 1 (simple) to 5 (very complex)
        """
        # Simplified complexity estimation based on prompt length, structure, and keywords
        # In a full implementation, use more sophisticated analysis

        complexity = 1  # Start with lowest complexity

        # Length-based adjustment
        if len(prompt) > 500:
            complexity += 2
        elif len(prompt) > 200:
            complexity += 1

        # Keyword-based adjustment
        complexity_indicators = {
            "complex": 1,
            "detailed": 1,
            "comprehensive": 1,
            "in-depth": 1,
            "advanced": 1,
            "elaborate": 1,
            "thoroughly": 1,
            "extensively": 1,
            "simple": -1,
            "basic": -1,
            "briefly": -1,
            "quickly": -1,
        }

        prompt_lower = prompt.lower()
        for indicator, adjustment in complexity_indicators.items():
            if indicator in prompt_lower:
                complexity += adjustment

        # Ensure within range 1-5
        return max(1, min(5, complexity))

    def _detect_tone(self, prompt: str) -> str:
        """
        Detect the emotional tone of the prompt.

        Args:
            prompt: The user's prompt

        Returns:
            Detected tone (e.g., "neutral", "urgent", "formal", etc.)
        """
        # Simple keyword-based tone detection
        # In a full implementation, use sentiment analysis or other NLP techniques
        tones = {
            "urgent": ["urgent", "immediately", "asap", "emergency", "critical"],
            "formal": ["formally", "professional", "officially", "academic", "proper"],
            "casual": ["casual", "friendly", "informal", "relaxed", "conversational"],
            "technical": ["technical", "precise", "exact", "detailed", "specific"],
            "creative": ["creative", "artistic", "imaginative", "innovative", "unique"],
        }

        prompt_lower = prompt.lower()
        for tone, keywords in tones.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return tone

        return "neutral"

    def _identify_knowledge_areas(self, prompt: str) -> List[str]:
        """
        Identify specialized knowledge areas relevant to the prompt.

        Args:
            prompt: The user's prompt

        Returns:
            List of specialized knowledge areas
        """
        # Simple keyword-based knowledge area detection
        # In a full implementation, use more sophisticated techniques
        knowledge_areas = []

        areas = {
            "programming": [
                "code",
                "programming",
                "software",
                "development",
                "algorithm",
            ],
            "data_science": [
                "data",
                "analysis",
                "statistics",
                "machine learning",
                "prediction",
            ],
            "writing": ["write", "content", "article", "blog", "text", "essay"],
            "marketing": ["marketing", "brand", "customer", "sales", "promotion"],
            "finance": ["finance", "investment", "money", "budget", "financial"],
        }

        prompt_lower = prompt.lower()
        for area, keywords in areas.items():
            for keyword in keywords:
                if keyword in prompt_lower and area not in knowledge_areas:
                    knowledge_areas.append(area)

        return knowledge_areas

    def _get_temperature_for_task(self, analysis: Dict[str, Any]) -> float:
        """
        Determine optimal temperature based on analysis.

        Args:
            analysis: Results from prompt analysis

        Returns:
            Appropriate temperature setting (0.0-1.0)
        """
        intent = analysis.get("intent_classification", "information")
        domain = analysis.get("primary_domain", "general")

        # Higher temperature for creative tasks
        if intent in ["creation", "creative"] or domain in ["creative"]:
            return 0.8

        # Lower temperature for factual, analytical, or code tasks
        elif intent in ["information", "analysis", "code"] or domain in [
            "science",
            "academic",
        ]:
            return 0.2

        # Middle temperature for general tasks
        return 0.5

    def _get_max_tokens_for_task(self, analysis: Dict[str, Any]) -> int:
        """
        Determine optimal max tokens based on analysis.

        Args:
            analysis: Results from prompt analysis

        Returns:
            Appropriate max_tokens setting
        """
        complexity = analysis.get("complexity_level", 3)
        intent = analysis.get("intent_classification", "information")

        # Higher token limit for complex tasks or content creation
        if complexity >= 4 or intent == "creation":
            return 4000

        # Medium token limit for moderately complex tasks
        elif complexity >= 2:
            return 2000

        # Lower token limit for simple tasks
        return 1000

    def _select_model_for_task(self, analysis: Dict[str, Any]) -> str:
        """
        Select the appropriate model based on the task requirements.

        Args:
            analysis: Results from prompt analysis

        Returns:
            Model identifier
        """
        complexity = analysis.get("complexity_level", 3)

        # For more complex tasks, use more capable models
        if complexity >= 4:
            return "gpt-4-1106-preview"

        # For medium complexity
        elif complexity >= 2:
            return "gpt-4-1106-preview"

        # For simpler tasks
        return "gpt-3.5-turbo"

    def _generate_system_message(self, analysis: Dict[str, Any], prompt: str) -> str:
        """
        Generate an optimized system message based on analysis.

        Args:
            analysis: Results from prompt analysis
            prompt: The user's prompt

        Returns:
            Tailored system message
        """
        domain = analysis.get("primary_domain", "general")
        intent = analysis.get("intent_classification", "information")
        knowledge_areas = analysis.get("specialized_knowledge_areas", [])

        # Base system message with role definition
        system_message = (
            f"You are a specialized AI assistant focused on {domain} topics."
        )

        # Add knowledge area specialization if available
        if knowledge_areas:
            system_message += f" Your expertise includes {', '.join(knowledge_areas)}."

        # Add intent-specific guidance
        if intent == "code":
            system_message += "\n\nYour primary task is to generate clean, efficient, and secure code."
            system_message += "\nPrioritize readability, maintainability, proper error handling, and security best practices."
            system_message += "\nInclude comments to explain complex logic and provide usage examples when appropriate."

        elif intent == "creation":
            system_message += (
                "\n\nYour primary task is to provide creative and original content."
            )
            system_message += "\nFocus on quality, originality, and meeting the specific requirements in the request."
            system_message += (
                "\nConsider the target audience and purpose of the content."
            )

        elif intent == "analysis":
            system_message += "\n\nYour primary task is to analyze information critically and objectively."
            system_message += "\nConsider multiple perspectives, identify patterns and insights, and provide evidence-based conclusions."
            system_message += (
                "\nAcknowledge limitations and uncertainties in your analysis."
            )

        elif intent == "information":
            system_message += "\n\nYour primary task is to provide accurate, concise, and helpful information."
            system_message += (
                "\nFocus on factual correctness, clarity, and relevance to the query."
            )
            system_message += (
                "\nDistinguish between established facts and opinions or speculations."
            )

        # Add general capabilities and boundaries
        system_message += (
            "\n\nYou should provide helpful, harmless, and honest responses."
        )
        system_message += "\n\nWhen responding:"
        system_message += "\n- Be concise and direct"
        system_message += "\n- Focus specifically on the user's request"
        system_message += "\n- Provide substantive, valuable information"
        system_message += "\n- Avoid unnecessary disclaimers or hedging language"

        # Add temporal awareness
        system_message += f"\n\nCurrent date: {time.strftime('%Y-%m-%d')}"
        system_message += "\nKnowledge cutoff: 2023-04"

        return system_message

    def _refine_system_message(
        self, previous_system_message: str, analysis: Dict[str, Any], prompt: str
    ) -> str:
        """
        Refine a previous system message based on new information.

        Args:
            previous_system_message: The system message to refine
            analysis: New analysis results
            prompt: The new user prompt

        Returns:
            Refined system message
        """
        # In a full implementation, this would make intelligent refinements
        # based on the new prompt and analysis

        # For now, we'll make some basic adjustments
        knowledge_areas = analysis.get("specialized_knowledge_areas", [])

        # Check if we need to add new expertise areas
        if knowledge_areas:
            expertise_line = f"Your expertise includes {', '.join(knowledge_areas)}."
            if "Your expertise includes" not in previous_system_message:
                # Add expertise line after the first sentence
                first_line_end = previous_system_message.find(".")
                if first_line_end != -1:
                    return (
                        previous_system_message[: first_line_end + 1]
                        + f" {expertise_line}"
                        + previous_system_message[first_line_end + 1 :]
                    )

        # Update the date
        message = previous_system_message.replace(
            "Current date: "
            + previous_system_message.split("Current date: ")[1].split("\n")[0],
            f"Current date: {time.strftime('%Y-%m-%d')}",
        )

        return message

    def _extract_contextual_data(
        self, conversation_history: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Extract relevant contextual data from conversation history.

        Args:
            conversation_history: Previous conversation turns

        Returns:
            Extracted contextual data
        """
        if not conversation_history:
            return {"conversation_summary": "No prior conversation"}

        # In a full implementation, this would extract key entities, facts, preferences, etc.
        # using more sophisticated NLP techniques

        # For now, a simplified implementation
        contextual_data = {
            "conversation_summary": f"Prior conversation with {len(conversation_history)} turns",
            "key_entities": [],
            "important_facts": [],
            "user_preferences": {},
        }

        # Extract mentions of key entities (very simplified)
        all_text = " ".join([turn.get("prompt", "") for turn in conversation_history])

        # Example simple entity extraction (names, organizations)
        import re

        # Look for capitalized words as potential entities
        potential_entities = re.findall(r"\b[A-Z][a-zA-Z]*\b", all_text)
        if potential_entities:
            # Take up to 5 most frequent entities
            from collections import Counter

            entities = [
                entity for entity, _ in Counter(potential_entities).most_common(5)
            ]
            contextual_data["key_entities"] = entities

        return contextual_data

    def _get_previous_agent_id(
        self, conversation_history: Optional[List[Dict[str, Any]]]
    ) -> Optional[str]:
        """
        Extract the previous agent ID from conversation history.

        Args:
            conversation_history: Previous conversation turns

        Returns:
            Previous agent ID if available, None otherwise
        """
        if not conversation_history or len(conversation_history) < 2:
            return None

        # Look for agent_id in the last response
        last_response = conversation_history[-1].get("response", {})
        if isinstance(last_response, dict):
            return last_response.get("agent_id")

        return None
