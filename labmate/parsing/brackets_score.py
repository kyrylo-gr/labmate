"""BracketsScore class."""


class BracketsScore:
    """Score number of brackets.

    Example:
        >>> brackets = BracketsScore()
        >>> brackets.update_from_str(" ( {a+b} ")
        >>> brackets.is_zero()
        False
        >>> brackets.update_from_str(" ) ")
        >>> brackets.is_zero()
        True

    """

    def __init__(self) -> None:
        """Initialize brackets score."""
        self.round = 0
        self.curly = 0
        self.square = 0

    def is_zero(self):
        """Check if the score is zero, i.e. all brackets are closed."""
        return self.round == 0 and self.curly == 0 and self.square == 0

    def update_from_str(self, text: str):
        """Update bracket scores from string.

        Args:
            text (str): Any string with (), {} or [] brackets.
        """
        self.round += text.count("(") - text.count(")")
        self.curly += text.count("{") - text.count("}")
        self.square += text.count("[") - text.count("]")
