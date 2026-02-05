"""Import Labmate."""

import setuptools


NAME = "labmate"
AUTHOR = "kyrylo.gr | LKB-OMQ"
AUTHOR_EMAIL = "git@kyrylo.gr"
DESCRIPTION = "Data management library to save data and plots to hdf5 files"


with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()


def get_version() -> str:
    """Get version from __config__.py."""
    with open(f"{NAME}/__config__.py", encoding="utf-8") as file:
        for line in file.readlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    raise ValueError("Version not found")


setuptools.setup(
    name=NAME,
    version=get_version(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/kyrylo-gr/{NAME}",
    packages=setuptools.find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "dh5",
    ],
    extras_require={
        "all": ["matplotlib", "pltsave"],
        "dev": [
            "matplotlib",
            "pytest",
            "check-manifest",
            "sphinx",
            "sphinx_rtd_theme",
        ],
    },
)
