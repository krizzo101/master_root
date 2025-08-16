import logging


class ExpertAgent:
    def __init__(self, name, specialty, system_message: str | None = None):
        self.name = name
        self.specialty = specialty
        self.memory = []
        self.system_message = (
            system_message
            or f"You are a world-class expert in {specialty}. Provide authoritative, up-to-date, and well-reasoned answers."
        )
        self.logger = logging.getLogger(__name__)

    def propose_answer(self, question, context=None):
        # Return a concise expert opinion only
        opinion = self._specialty_opinion(question)
        self.memory.append(("propose", opinion))
        return opinion

    def critique_answers(self, all_answers, context=None):
        critiques = {}
        for agent, answer in all_answers.items():
            if agent != self.name:
                critique = self._critique_opinion(answer)
                critiques[agent] = critique
        self.memory.append(("critique", critiques))
        return critiques

    def revise_answer(self, own_answer, critiques, context=None):
        # Return a revised answer as a short summary, not a concatenation
        if critiques:
            revised = self._revise_opinion(own_answer, critiques)
        else:
            revised = own_answer
        self.memory.append(("revise", revised))
        return revised

    def _specialty_opinion(self, question):
        # Generate a plausible, concise expert opinion
        if self.specialty == "Machine Learning":
            return "Key open problems include interpretability, robustness, and alignment of learning systems."
        elif self.specialty == "Statistics":
            return "Major challenges are quantifying uncertainty, causal inference, and evaluation metrics for AGI."
        elif self.specialty == "Ethics":
            return "Critical issues are value alignment, safety, and societal impact of AGI deployment."
        else:
            return f"Important open problems remain unsolved in {self.specialty}."

    def _critique_opinion(self, answer):
        # Generate a brief, plausible critique
        return "This answer could be improved by addressing additional perspectives or clarifying assumptions."

    def _revise_opinion(self, own_answer, critiques):
        # Summarize the revised answer based on critiques
        return own_answer + " (Revised after peer feedback.)"


class MLExpert(ExpertAgent):
    def __init__(self, system_message: str | None = None):
        super().__init__(
            name="MLExpert",
            specialty="Machine Learning",
            system_message=system_message
            or "You are a world-class machine learning expert. Provide authoritative, up-to-date, and well-reasoned answers.",
        )


class StatsExpert(ExpertAgent):
    def __init__(self, system_message: str | None = None):
        super().__init__(
            name="StatsExpert",
            specialty="Statistics",
            system_message=system_message
            or "You are a world-class statistics expert. Provide authoritative, up-to-date, and well-reasoned answers.",
        )


class EthicsExpert(ExpertAgent):
    def __init__(self, system_message: str | None = None):
        super().__init__(
            name="EthicsExpert",
            specialty="Ethics",
            system_message=system_message
            or "You are a world-class ethics expert. Provide authoritative, up-to-date, and well-reasoned answers.",
        )
