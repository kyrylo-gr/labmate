"""Import Labmate."""

import setuptools

NAME = "labmate"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(f"{NAME}/__version.py", "r", encoding="utf-8") as fh:
    version = fh.read().split("=")[-1].strip()

setuptools.setup(
    name=NAME,
    version=version,
    author="LKB-OMQ",
    author_email="cryo.paris.su@gmail.com",
    description="Data management library to save data and plots to hdf5 files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kyrylo-gr/labmate",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
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
