"""Import Labmate."""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="labmate",
    version="0.7.8",
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
