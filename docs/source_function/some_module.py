import numpy as np
import some_module2
from some_module2 import test4

external_variable = 1


def test():
    return 2


def test2(x):
    b = 2
    t = SomeClass()
    return x + test() + external_variable + b + some_module2.test3() + test4() + t.test6()


class SomeClass:
    def __init__(self):
        self.a = 1

    def test6(self):
        return 2
