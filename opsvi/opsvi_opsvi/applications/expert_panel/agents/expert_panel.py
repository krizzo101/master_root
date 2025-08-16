from typing import Dict

from applications.expert_panel.agents.expert_agent import (
    EthicsExpert,
    ExpertAgent,
    MLExpert,
    StatsExpert,
)
from applications.expert_panel.agents.expert_assigner import ExpertAssignerAgent

from .researcher_agent import ResearcherAgent


class ExpertPanel:
    def __init__(self, question: str):
        self.expert_assigner = ExpertAssignerAgent()
        self.transcript = []
        # Assign experts dynamically for this question
        expert_roster = self.expert_assigner.assign_experts(question)
        self.experts = [
            self._instantiate_expert(e["expert_type"], e["system_message"])
            for e in expert_roster
        ]

    def _instantiate_expert(self, expert_type: str, system_message: str) -> ExpertAgent:
        # Map known types to classes, else use generic ExpertAgent
        mapping = {
            "MLExpert": MLExpert,
            "StatsExpert": StatsExpert,
            "EthicsExpert": EthicsExpert,
            "Researcher": ResearcherAgent,
        }
        cls = mapping.get(expert_type, ExpertAgent)
        if cls is ExpertAgent:
            return cls(
                name=expert_type, specialty=expert_type, system_message=system_message
            )
        return cls(system_message=system_message)

    def run_discussion(self, question, max_rounds=5):
        answers = {e.name: e.propose_answer(question) for e in self.experts}
        self.transcript.append({"round": 1, "answers": answers.copy()})
        round_num = 2
        while not self.check_consensus(answers) and round_num <= max_rounds:
            critiques = {e.name: e.critique_answers(answers) for e in self.experts}
            self.transcript.append({"round": round_num, "critiques": critiques.copy()})
            for e in self.experts:
                answers[e.name] = e.revise_answer(
                    answers[e.name], critiques.get(e.name, {})
                )
            self.transcript.append({"round": round_num, "answers": answers.copy()})
            # If no consensus, invoke Researcher for fact-checking
            if not self.check_consensus(answers):
                researcher = next(
                    (e for e in self.experts if e.name == "Researcher"), None
                )
                if researcher:
                    research_query = f"Fact-check and resolve dispute for: {question} and current answers: {answers}"
                    research_summary = researcher.perform_research(research_query)
                    self.transcript.append(
                        {"round": round_num, "research": research_summary}
                    )
                    # Share research findings with all experts (could update context)
            round_num += 1
        return {
            "consensus": self.get_consensus_answer(answers),
            "answers": answers,
            "transcript": self.transcript,
        }

    def check_consensus(self, answers: Dict) -> bool:
        return len(set(answers.values())) == 1

    def get_consensus_answer(self, answers: Dict) -> str:
        if self.check_consensus(answers):
            return next(iter(answers.values()))
        return "[No consensus reached]"

    @staticmethod
    def pretty_print_transcript(transcript):
        print("\n==== Expert Panel Discussion Transcript ====")
        for entry in transcript:
            round_num = entry.get("round")
            if "answers" in entry:
                print(f"\n-- Round {round_num}: Expert Answers --")
                for expert, answer in entry["answers"].items():
                    print(f"  [{expert}]\n    {answer}\n")
            if "critiques" in entry:
                print(f"\n-- Round {round_num}: Critiques --")
                for expert, critiques in entry["critiques"].items():
                    print(f"  [{expert}] Critiques:")
                    if isinstance(critiques, dict):
                        for target, critique in critiques.items():
                            print(f"    of {target}: {critique}")
                    else:
                        print(f"    {critiques}")

    @staticmethod
    def pretty_print_answers(answers):
        print("\n==== Final Answers by Expert ====")
        for expert, answer in answers.items():
            print(f"  [{expert}]\n    {answer}\n")
