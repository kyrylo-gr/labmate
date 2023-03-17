"""Module contains the errors used inside labmate"""


class MultiLineValueError(ValueError):
    """ValueError that excepts the multi-line message by
    removing the 4 spaces"""

    def __init__(self, msg):
        msg = msg.replace("    ", "").replace("\n", "")
        super().__init__(msg)
