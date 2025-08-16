"""
Interactive session helpers for O3 Code Generator (brainstorming, idea analysis, etc.)
"""

import json
import sys
from typing import Any

from src.tools.code_generation.o3_code_generator.analysis_utils import (
    save_assistant_brainstorm_results,
    save_text_brainstorm_results,
)
from src.tools.code_generation.o3_code_generator.utils.assistants_api_manager import (
    AssistantsAPIManager,
)


def run_interactive_brainstorm_session() -> dict[str, Any]:
    """Run interactive brainstorming session using OpenAI Assistants API."""
    try:
        print("\n💡 Starting interactive brainstorming session...")
        print("🤖 I'm here to help you explore creative solutions and generate ideas!")
        print("📝 Describe your problem, opportunity, or area you want to explore.")
        print(
            "🔄 Type 'done' when you're ready to generate the final brainstorming results."
        )
        print("🔄 Type 'end' to exit the session and terminate the program.\n")

        # Initialize the assistants API manager with the desired model
        assistants_manager = AssistantsAPIManager(model="gpt-4.1")

        # Create a brainstorming assistant
        assistant_instructions = """
You are an expert brainstorming facilitator focused on helping users discover WHAT to build and WHY it matters. Your role is to guide users through conceptual idea generation and help them clarify their vision - NOT to figure out HOW to implement it.

## Your Focus: WHAT and WHY (Not HOW)
**What You Should Explore:**
- **Problem Identification**: What problems should we solve?
- **Value Proposition**: What value should this provide?
- **Feature Ideas**: What capabilities should it have?
- **User Needs**: What do users really want?
- **Market Opportunities**: What gaps exist?
- **Unique Differentiators**: What makes it special?
- **Big Picture Vision**: What should this become?

**What You Should NOT Do:**
- ❌ Suggest specific technologies or frameworks
- ❌ Discuss technical implementation details
- ❌ Make architecture decisions
- ❌ Provide code or technical solutions
- ❌ Focus on performance optimization
- ❌ Get into platform-specific details

## Your Expertise
- **Creative Thinking Techniques**: SCAMPER, Mind Mapping, Analogical Thinking, Reverse Thinking
- **Innovation Frameworks**: Design Thinking, TRIZ, Blue Ocean Strategy, Jobs-to-be-Done
- **Problem Analysis**: Root cause analysis, opportunity mapping, user need identification
- **Idea Evaluation**: Impact assessment, value proposition analysis, market fit evaluation

## Your Approach
1. **Deep Understanding**: Ask probing questions to uncover root problems and hidden opportunities
2. **Multi-Perspective Exploration**: Consider user, business, market, and societal perspectives
3. **Creative Techniques**: Use SCAMPER, analogies, reverse thinking, and constraint removal
4. **Context Building**: Help users explore user needs, market gaps, and value opportunities
5. **Opportunity Identification**: Uncover adjacent possibilities and unexpected connections
6. **Idea Refinement**: Guide users to combine, expand, and evolve promising concepts

## Conversation Strategy
- **Build on Everything**: Reference specific points from the conversation
- **Challenge Assumptions**: Question constraints and explore "what if" scenarios
- **Encourage Divergent Thinking**: Generate quantity before quality
- **Guide Convergence**: Help organize and prioritize when ready
- **Maintain Context**: Use conversation history to inform suggestions
- **Stay Conceptual**: Focus on ideas and vision, not implementation

## Response Style
- Be encouraging and supportive while pushing creative boundaries
- Provide specific, actionable suggestions rather than vague advice
- Use analogies and examples to illustrate concepts
- Ask follow-up questions that deepen understanding
- Reference specific conversation points to show engagement
- Keep focus on WHAT and WHY, not HOW

## Dynamic Adaptation (IMPORTANT)
After each response, you must generate a dynamic system prompt that will be used for the next interaction. This allows you to become more expert and aligned with the user's specific needs.

**Response Format**: Always respond in this JSON structure (invisible to user):
{
  "user_response": "Your actual response to the user (what they see)",
  "dynamic_system_prompt": "Generated system prompt for next interaction",
  "context_analysis": {
    "user_domain": "Domain/field the user is working in",
    "communication_style": "User's preferred communication style",
    "expertise_level": "User's technical/business expertise level",
    "problem_focus": "Main problem areas the user is exploring",
    "creative_preferences": "User's preferred creative approaches"
  },
  "expertise_focus": {
    "primary_techniques": ["List of brainstorming techniques to emphasize"],
    "domain_knowledge": "Specific domain expertise to build",
    "communication_adaptation": "How to adapt communication style",
    "next_questions": ["Suggested follow-up questions to ask"]
  }
}

**Dynamic Prompt Guidelines**:
- Focus on becoming expert in the user's specific domain
- Adapt to their communication style and expertise level
- Emphasize creative techniques that work well for their context
- Build on insights from the conversation
- Make yourself more effective for their specific needs
- Maintain focus on conceptual/strategic level, not technical implementation

Remember: The user only sees your "user_response" - the rest is for system adaptation. Stay focused on WHAT and WHY, not HOW.
"""

        assistant = assistants_manager.create_assistant(
            name="Brainstorming Assistant",
            instructions=assistant_instructions,
        )

        # Create a thread for the conversation
        thread = assistants_manager.create_thread()

        conversation = []
        dynamic_system_prompt = ""  # Track dynamic prompt across conversation
        user_input = input("👤 You: ").strip()

        try:
            while user_input.lower() not in ["done", "end"]:
                if user_input:
                    # Prepend dynamic prompt to user input if available
                    if dynamic_system_prompt:
                        enhanced_input = (
                            f"{dynamic_system_prompt}\n\nUser: {user_input}"
                        )
                    else:
                        enhanced_input = user_input

                    conversation.append({"role": "user", "content": user_input})

                    # Add enhanced message to thread
                    assistants_manager.add_message(enhanced_input)

                    # Run the assistant
                    run = assistants_manager.run_assistant()
                    assistants_manager.wait_for_run_completion(run)

                    # Get the assistant's response
                    messages = assistants_manager.get_latest_messages(1)
                    if messages:
                        ai_response = messages[0].content[0].text.value

                        # Try to parse as structured response
                        try:
                            structured_response = json.loads(ai_response)

                            # Extract user response and dynamic prompt
                            user_response = structured_response.get(
                                "user_response", ai_response
                            )
                            dynamic_system_prompt = structured_response.get(
                                "dynamic_system_prompt", dynamic_system_prompt
                            )

                            # Show only user response to user
                            print(f"🤖 AI: {user_response}")

                            # Store full structured response in conversation
                            conversation.append(
                                {"role": "assistant", "content": ai_response}
                            )

                            # Log dynamic adaptation (for debugging)
                            context_analysis = structured_response.get(
                                "context_analysis", {}
                            )
                            if context_analysis:
                                print(
                                    f"🔧 [System: Adapting to {context_analysis.get('user_domain', 'unknown')} domain]"
                                )

                        except json.JSONDecodeError:
                            # Fallback to regular response if not structured
                            print(f"🤖 AI: {ai_response}")
                            conversation.append(
                                {"role": "assistant", "content": ai_response}
                            )
                    else:
                        print(
                            "🤖 AI: I'm here to help you brainstorm! What would you like to explore?"
                        )

                user_input = input("👤 You: ").strip()

            # Check if user wants to exit
            if user_input.lower() == "end":
                print("\n👋 Ending session and exiting...")
                sys.exit(0)

            # Don't clean up here - we need the assistant for final idea generation
            # assistants_manager.cleanup()

        except Exception as e:
            print(f"❌ Error with Assistants API: {e}")
            print("💥 Session failed. Please try again.")
            # Clean up on error
            try:
                assistants_manager.cleanup()
            except:
                pass
            sys.exit(1)

        # The assistant already has full conversation context - let it do the work
        print("\n🤖 Generating brainstorming ideas using our conversation context...")

        # Create simple problem statement from user messages
        user_messages = [
            msg["content"] for msg in conversation if msg["role"] == "user"
        ]
        combined_input = "\n".join(user_messages)

        print("\n🤖 Generating brainstorming ideas using our conversation context...")

        # Use the assistant's conversation memory to generate ideas directly
        try:
            # Add final message to the assistant thread asking for idea generation
            final_prompt = f"""
{dynamic_system_prompt}

Based on our entire conversation and your evolved expertise, please generate 15 innovative ideas using advanced brainstorming techniques. Focus on WHAT to build and WHY it matters - NOT HOW to implement it.

## Idea Generation Approach
Use these techniques to generate diverse, high-quality ideas:
1. **SCAMPER Techniques**: Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse
2. **Analogical Thinking**: What works in other domains that could apply here?
3. **Reverse Thinking**: What would make this fail? Then reverse those failure points
4. **Constraint Removal**: What if we removed key constraints?
5. **Multi-Perspective**: Consider user, business, market, and societal viewpoints
6. **Adjacent Possibilities**: Explore related opportunities and unexpected connections

## Idea Requirements
For each idea, provide:
- **Title**: Clear, compelling name
- **Description**: Detailed explanation of the concept and its value proposition
- **Category**: User Experience, Business Model, Feature Innovation, Process Improvement, Market Opportunity, or Concept Innovation
- **Impact Level**: High/Medium/Low (consider user value, market potential, strategic importance)
- **Value Proposition**: What unique value does this provide?
- **Target Users**: Who would benefit most from this?
- **Key Features**: What capabilities would this have?
- **Innovation Type**: Incremental improvement, Radical innovation, or Process optimization
- **Key Assumptions**: What assumptions does this idea challenge or rely on?

## Special Instructions
- **Build on Conversation**: Reference specific problems, preferences, and opportunities we discussed
- **Diverse Thinking**: Include both incremental and breakthrough ideas
- **User-Centered**: Focus on solving real user problems we identified
- **Value-Focused**: Emphasize the value proposition and user benefits
- **Market-Aware**: Consider market opportunities and competitive landscape
- **Leverage Your Expertise**: Use the domain knowledge and techniques you've developed during our conversation
- **Stay Conceptual**: Focus on WHAT and WHY, not technical HOW

## Output Structure
Return in JSON format with this enhanced structure:

{{
  "ideas": [
    {{
      "id": "idea_001",
      "title": "Idea Title",
      "description": "Detailed description explaining the concept and its value proposition",
      "category": "User Experience/Business Model/Feature Innovation/Process Improvement/Market Opportunity/Concept Innovation",
      "impact": "High/Medium/Low",
      "value_proposition": "What unique value does this provide?",
      "target_users": "Who would benefit most from this?",
      "key_features": "What capabilities would this have?",
      "innovation_type": "Incremental/Radical/Process",
      "key_assumptions": "What this idea assumes or challenges",
      "conversation_connection": "How this builds on our discussion"
    }}
  ],
  "categories": ["Category1", "Category2", ...],
  "prioritized_ideas": [sorted list by priority score],
  "summary": "Key insights from our conversation and how they influenced the ideas",
  "conversation_themes": ["Theme1", "Theme2", ...],
  "identified_problems": ["Problem1", "Problem2", ...],
  "user_preferences": ["Preference1", "Preference2", ...],
  "opportunities_explored": ["Opportunity1", "Opportunity2", ...],
  "expertise_applied": "How your evolved expertise influenced these ideas"
}}

Focus on generating ideas that directly address the specific problems and opportunities we've explored in our conversation, using the expertise you've developed throughout our session. Remember: Focus on WHAT and WHY, not HOW.
"""

            # Add the final message to the thread
            assistants_manager.add_message(final_prompt)

            # Run the assistant to generate ideas
            run = assistants_manager.run_assistant()
            assistants_manager.wait_for_run_completion(run)

            # Get the assistant's response
            messages = assistants_manager.get_latest_messages(1)
            if not messages:
                print("❌ No response from assistant")
                return {"problem_statement": combined_input}

            # Parse the assistant's response
            try:
                response_content = messages[0].content[0].text.value
                ideas_data = json.loads(response_content)

                # Save results
                next_step_file = save_assistant_brainstorm_results(
                    ideas_data, combined_input
                )

                # Display enhanced results
                ideas = ideas_data.get("ideas", [])
                categories = ideas_data.get("categories", [])
                prioritized_ideas = ideas_data.get("prioritized_ideas", [])
                conversation_themes = ideas_data.get("conversation_themes", [])
                identified_problems = ideas_data.get("identified_problems", [])
                opportunities_explored = ideas_data.get("opportunities_explored", [])
                expertise_applied = ideas_data.get("expertise_applied", "")

                print(
                    "\n💡 Conceptual brainstorming completed using our conversation context!"
                )
                print(
                    f"📊 Generated {len(ideas)} ideas across {len(categories)} categories"
                )
                print(f"🏆 Categories: {', '.join(categories[:3])}")

                # Show conversation insights
                if conversation_themes:
                    print(f"🎯 Key themes: {', '.join(conversation_themes[:3])}")
                if identified_problems:
                    print(f"🔍 Problems addressed: {', '.join(identified_problems[:2])}")
                if opportunities_explored:
                    print(
                        f"💡 Opportunities explored: {', '.join(opportunities_explored[:2])}"
                    )

                # Show innovation breakdown
                innovation_types = [
                    idea.get("innovation_type", "Unknown") for idea in ideas
                ]
                radical_count = innovation_types.count("Radical")
                incremental_count = innovation_types.count("Incremental")
                process_count = innovation_types.count("Process")
                print(
                    f"🚀 Innovation mix: {radical_count} radical, {incremental_count} incremental, {process_count} process"
                )

                # Show dynamic adaptation summary
                if dynamic_system_prompt:
                    print("🧠 Dynamic expertise applied throughout conversation")

                print(f"📁 Results saved to: {next_step_file}")
                print("🔄 Next step: Use 'idea-analyze' to analyze the best ideas")
                print(f"   Example: python -m main idea-analyze {next_step_file}")

                # Show enhanced top ideas preview
                if prioritized_ideas:
                    print("\n🎯 Top 3 ideas to consider:")
                    for i, idea in enumerate(prioritized_ideas[:3], 1):
                        try:
                            if isinstance(idea, dict):
                                title = idea.get("title", "Untitled")
                                category = idea.get("category", "General")
                                innovation_type = idea.get("innovation_type", "Unknown")
                                impact = idea.get("impact", "Medium")
                                value_prop = idea.get("value_proposition", "")
                                if value_prop:
                                    print(
                                        f"   {i}. {title} ({category}, {innovation_type}, {impact} impact)"
                                    )
                                    print(f"      💎 {value_prop[:60]}...")
                                else:
                                    print(
                                        f"   {i}. {title} ({category}, {innovation_type}, {impact} impact)"
                                    )
                            else:
                                print(f"   {i}. {str(idea)[:80]}...")
                        except Exception as e:
                            print(f"   {i}. [Error displaying idea: {e}]")

                return {"problem_statement": combined_input, "ideas_data": ideas_data}

            except json.JSONDecodeError:
                print("⚠️ Assistant response wasn't in JSON format, saving as text")
                response_content = messages[0].content[0].text.value
                next_step_file = save_text_brainstorm_results(
                    response_content, combined_input
                )
                print(f"📁 Results saved to: {next_step_file}")
                return {
                    "problem_statement": combined_input,
                    "raw_response": response_content,
                }

        except Exception as e:
            print(f"❌ Error with Assistants API: {e}")
            print("💥 Session failed. Please try again.")
            sys.exit(1)
        finally:
            # Clean up assistant after all interactions are complete
            try:
                assistants_manager.cleanup()
            except:
                pass

    except Exception as e:
        print(f"❌ Error during interactive brainstorming session: {e}")
        raise


def run_interactive_idea_session() -> dict:
    """Run interactive idea analysis session using OpenAI Assistants API."""
    # The full implementation would be moved here from o3_main.py, similar to run_interactive_brainstorm_session.
    # For now, return a stub
    return {}
