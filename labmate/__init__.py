"""
This is something
"""

try:
    __import__("pkg_resources").declare_namespace(__name__)
except ModuleNotFoundError:
    pass
