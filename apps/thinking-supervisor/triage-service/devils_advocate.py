"""
Devil's Advocate Agent - Asks specific, contextual questions to force deeper thinking
"""

import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add paths for knowledge access
sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps")

try:
    from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False


class DevilsAdvocate:
    """Agent that asks specific, contextual questions based on what you're actually saying"""
    
    def __init__(self):
        # Load operational instructions once
        self.operational_rules = self._load_operational_rules()
        
    def _load_operational_rules(self) -> List[str]:
        """Load key operational rules from knowledge base"""
        rules = [
            "NO ASSUMPTIONS - Verify everything, don't guess",
            "NO FALLBACKS - Fix root causes, not symptoms",
            "BE AN EXPERT ADVISOR - Question and evaluate, don't just execute",
            "CHECK SHARED RESOURCES - Don't modify what works for everything else",
            "UNDERSTAND BEFORE CHANGING - Know why code exists before modifying"
        ]
        
        if KNOWLEDGE_AVAILABLE:
            try:
                query_tool = get_enhanced_query()
                result = query_tool.query(
                    query_type="search",
                    query_text="GLOBAL OPERATIONAL INSTRUCTIONS",
                    limit=1
                )
                # Add any specific rules from KB
                for item in result.get("results", []):
                    content = item.get("content", "")
                    if "NO ASSUMPTIONS" in content:
                        # Extract key rules
                        rules.append("From KB: Question every assumption before acting")
            except:
                pass  # Use defaults if KB unavailable
                
        return rules
    
    def _extract_specifics(self, thought: str) -> Dict[str, Any]:
        """Extract specific details from the thought to ask about"""
        specifics = {
            "errors": [],
            "values": [],
            "files": [],
            "functions": [],
            "comparisons": [],
            "problems": [],
            "solutions": []
        }
        
        # Extract error messages or error descriptions
        error_patterns = [
            r"error[:\s]+([^\.]+)",
            r"fails? with ([^\.]+)",
            r"doesn't work with ([^\.]+)",
            r"rejected?(?:ing)? ([^\.]+)",
            r"not valid (?:for|under) ([^\.]+)"
        ]
        for pattern in error_patterns:
            matches = re.findall(pattern, thought.lower())
            specifics["errors"].extend(matches)
        
        # Extract specific values mentioned
        value_patterns = [
            r"(?:value|parameter|argument) (?:of |is )?(['\"]?\w+['\"]?)",
            r"(?:tried?|using|with) (['\"]?\d+['\"]?)",
            r"(?:set to|equals?) (['\"]?\w+['\"]?)"
        ]
        for pattern in value_patterns:
            matches = re.findall(pattern, thought.lower())
            specifics["values"].extend(matches)
        
        # Extract file names
        file_patterns = [
            r"(?:file|module|script) ([a-zA-Z0-9_\-\.]+\.py)",
            r"in ([a-zA-Z0-9_\-/]+\.py)",
            r"(?:edit|modify|change) ([a-zA-Z0-9_\-/]+)"
        ]
        for pattern in file_patterns:
            matches = re.findall(pattern, thought)
            specifics["files"].extend(matches)
        
        # Extract function/parameter names
        func_patterns = [
            r"(?:function|method|parameter) ([a-zA-Z_]\w+)",
            r"([a-zA-Z_]\w+)\s*(?:works?|fails?|doesn't work)",
            r"([a-zA-Z_]\w+):\s*(?:Optional|int|str|bool|List)"
        ]
        for pattern in func_patterns:
            matches = re.findall(pattern, thought)
            specifics["functions"].extend(matches)
        
        # Extract comparisons
        if "but" in thought.lower() or "while" in thought.lower() or "however" in thought.lower():
            comp_patterns = [
                r"(\w+) works? but (\w+) doesn't",
                r"(\w+) is (.+) while (\w+) is (.+)",
                r"difference (?:is|between) (.+)"
            ]
            for pattern in comp_patterns:
                matches = re.findall(pattern, thought.lower())
                specifics["comparisons"].extend(matches)
        
        # Extract problem descriptions
        problem_keywords = ["issue", "problem", "error", "fails", "doesn't work", "rejected", "can't"]
        for keyword in problem_keywords:
            if keyword in thought.lower():
                # Get the sentence containing the keyword
                sentences = thought.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        specifics["problems"].append(sentence.strip())
                        break
        
        # Extract proposed solutions
        solution_keywords = ["will", "going to", "plan to", "should", "need to", "have to", "try"]
        for keyword in solution_keywords:
            if keyword in thought.lower():
                sentences = thought.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        specifics["solutions"].append(sentence.strip())
                        break
        
        return specifics
    
    def _generate_specific_questions(self, thought: str, specifics: Dict[str, Any]) -> List[str]:
        """Generate specific questions based on extracted details"""
        questions = []
        
        # Questions about specific errors
        if specifics["errors"]:
            for error in specifics["errors"][:2]:  # First 2 errors
                questions.append(f"What's the EXACT error message for '{error}'? Copy-paste it.")
                questions.append(f"At what line of code does '{error}' occur? Show me the stack trace.")
        
        # Questions about specific values
        if specifics["values"]:
            value = specifics["values"][0]
            questions.append(f"You mentioned {value} - have you tested adjacent values? What about {value}±1?")
            questions.append(f"Does {value} work when passed as a different type (string vs int)?")
            questions.append(f"Is {value} within the expected range? What ARE the bounds?")
        
        # Questions about files being modified
        if specifics["files"]:
            file = specifics["files"][0]
            questions.append(f"When was {file} last modified? By whom? For what purpose?")
            questions.append(f"What other code depends on {file}? Have you checked?")
            questions.append(f"Can you show me the current version of {file} around the problem area?")
        
        # Questions about function/parameter differences
        if specifics["functions"]:
            if len(specifics["functions"]) >= 2:
                func1, func2 = specifics["functions"][:2]
                questions.append(f"What's the EXACT type signature difference between {func1} and {func2}?")
                questions.append(f"Can you show me both {func1} and {func2} side by side?")
            else:
                func = specifics["functions"][0]
                questions.append(f"What's the full signature of {func}? Include all parameters and types.")
                questions.append(f"Where is {func} defined? Show me the implementation.")
        
        # Questions about comparisons
        if specifics["comparisons"]:
            questions.append("You're comparing things - can you create a minimal test case showing the difference?")
            questions.append("Have you verified your comparison is accurate? Show me the evidence.")
        
        # Questions about the problem
        if specifics["problems"]:
            questions.append("When did this problem START? What changed right before it broke?")
            questions.append("Can you reproduce this problem in isolation? Show me a minimal example.")
            questions.append("Does this problem occur in other environments or just yours?")
        
        # Questions about proposed solutions
        if specifics["solutions"]:
            questions.append("How will you TEST that your solution actually works?")
            questions.append("What could go WRONG with your approach? Be specific.")
            questions.append("Is there prior art? Has anyone solved this exact problem before?")
        
        return questions
    
    def _generate_contextual_alternatives(self, thought: str, specifics: Dict[str, Any]) -> List[str]:
        """Generate specific alternative approaches based on the context"""
        alternatives = []
        
        if "parameter" in thought.lower() and "doesn't work" in thought.lower():
            alternatives.append("Create a test harness that tries ALL parameter types and values systematically")
            alternatives.append("Check the MCP/FastMCP source code directly to see how it validates parameters")
            alternatives.append("Use a debugger to step through the validation and see where it fails")
        
        if "error" in thought.lower() and any(word in thought.lower() for word in ["50", "integer", "int"]):
            alternatives.append("Try the same value as different types: 50, '50', 50.0, float(50)")
            alternatives.append("Check if there's a version mismatch between your Pydantic and FastMCP's expectations")
        
        if "field" in thought.lower() and "none" in thought.lower():
            alternatives.append("Compare with working examples in the FastMCP documentation or tests")
            alternatives.append("Try using the older Field syntax that other working parameters use")
        
        if "restart" in thought.lower():
            alternatives.append("Instead of restarting, can you hot-reload or dynamically update the definition?")
            alternatives.append("Create a minimal standalone test that doesn't require the full MCP server")
        
        return alternatives
    
    def analyze(self, thought: str, intended_action: Optional[str], thought_data: Any) -> Dict:
        """
        Analyze the current thought and ask SPECIFIC, CONTEXTUAL questions
        """
        
        questions = []
        alternatives = []
        warnings = []
        critical_violations = []
        
        # Extract specific details from the thought
        specifics = self._extract_specifics(thought)
        
        # Get step awareness
        thought_number = getattr(thought_data, "thoughtNumber", 1) if thought_data else 1
        total_thoughts = getattr(thought_data, "totalThoughts", 1) if thought_data else 1
        next_thought_needed = getattr(thought_data, "nextThoughtNeeded", False) if thought_data else False
        is_final_thought = not next_thought_needed or thought_number >= total_thoughts
        
        # Generate specific questions based on what was said
        specific_questions = self._generate_specific_questions(thought, specifics)
        questions.extend(specific_questions[:5])  # Top 5 most relevant
        
        # Generate contextual alternatives
        contextual_alternatives = self._generate_contextual_alternatives(thought, specifics)
        alternatives.extend(contextual_alternatives[:3])
        
        # On final thought, ask verification questions
        if is_final_thought:
            questions.append("Show me EXACTLY how you'll verify this works - what commands will you run?")
            questions.append("What's your rollback plan if this breaks something?")
            
            # Check confidence with specific questions
            confidence = getattr(thought_data, "confidenceLevel", None) if thought_data else None
            if confidence and confidence < 70:
                questions.append(f"You're only {confidence}% confident - what specific info would get you to 90%?")
                alternatives.append(f"Get to 90% confidence first: what specific test would increase certainty?")
        
        # Check for rule violations with specific context
        thought_lower = thought.lower()
        
        # NO ASSUMPTIONS - but be specific about WHAT assumption
        assumption_words = ["probably", "should", "might", "assume", "think", "believe", "guess"]
        for word in assumption_words:
            if word in thought_lower:
                # Find what follows the assumption word
                idx = thought_lower.index(word)
                context = thought[idx:min(idx+50, len(thought))]
                critical_violations.append(f"🚨 NO ASSUMPTIONS: You said '{context}' - verify this!")
                questions.append(f"You said '{word}' - what SPECIFIC test would verify this?")
                break
        
        # Check attempts and ask about specific failures
        attempts = getattr(thought_data, "attemptNumber", 1) if thought_data else 1
        if attempts > 2:
            previous_failures = getattr(thought_data, "previousFailures", []) if thought_data else []
            if previous_failures:
                questions.append(f"You've tried {attempts} times - what was DIFFERENT about attempt #{attempts-1}?")
                questions.append(f"Your previous approach '{previous_failures[-1] if previous_failures else 'unknown'}' failed - why?")
            alternatives.append(f"After {attempts} attempts, try the OPPOSITE approach")
        
        # Determine skepticism level based on specific issues found
        if critical_violations:
            skepticism_level = "critical"
            should_pause = True
        elif len(specific_questions) > 3:
            skepticism_level = "high"
            should_pause = True
        elif specific_questions:
            skepticism_level = "medium"
            should_pause = False
        else:
            skepticism_level = "low"
            should_pause = False
        
        # Generate summary that references specific issues
        if critical_violations:
            summary = critical_violations[0]
        elif specific_questions:
            summary = f"ANSWER THIS FIRST: {specific_questions[0]}"
        elif alternatives:
            summary = f"Consider instead: {alternatives[0]}"
        else:
            summary = "Proceed, but document your assumptions"
        
        return {
            "critical_violations": critical_violations,
            "warnings": warnings,
            "questions": questions[:5],  # Top 5 most specific
            "alternatives": alternatives[:3],
            "skepticism_level": skepticism_level,
            "should_pause": should_pause,
            "summary": summary,
            "specifics_found": {k: len(v) for k, v in specifics.items() if v}  # What we extracted
        }