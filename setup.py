# setup.py
from setuptools import setup, find_packages

setup(
    name="gitwit",
    version="0.1.1",
    description="A CLI for showing activity, experts, etc.. based on git data.",
    author="Jack Francis Dalton",
    author_email="jackfrancisdalton@gmail.com",
    python_requires=">=3.7",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "typer[all]>=0.9.0",
        "GitPython>=3.1.31",
        "rich>=13.5.2",
        "watchdog>=4.0.0",
    ],
    # extras_require={ Don't think these are needed, will review later
    #     "dev": [
    #         "pytest>=7.3.1",
    #         "pytest-mock>=3.10.0",
    #     ],
    # },
    entry_points={
        "console_scripts": [
            "gitwit = cli.cli:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Typer",
    ],
)
