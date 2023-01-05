import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='quanalys',
    version="1",
    author="LKB-OMQ",
    author_email="cryo.paris.su@gmail.com",
    description="Data management library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SamuelDeleglise/acquisition_utils",
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
