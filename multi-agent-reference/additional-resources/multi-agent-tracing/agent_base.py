class AgentBase:
    """
    Minimal base class for all agent types. Extend this class to implement agent logic.
    """

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__  # Default to class name

    def act(self, *args, **kwargs):
        """Override this method to define agent behavior."""
        raise NotImplementedError("Subclasses must implement the act() method.")
