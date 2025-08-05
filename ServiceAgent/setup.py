#!/usr/bin/env python3
"""
Setup script for ServiceAgent.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [line.strip() for line in requirements_path.read_text().splitlines() if line.strip() and not line.startswith("#")]

setup(
    name="serviceagent",
    version="1.0.0",
    author="ServiceAgent Team",
    author_email="team@serviceagent.com",
    description="A modular, extensible AI agent built with LangGraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/serviceagent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "serviceagent=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="ai agent langgraph llm tools mcp",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/serviceagent/issues",
        "Source": "https://github.com/yourusername/serviceagent",
        "Documentation": "https://serviceagent.readthedocs.io/",
    },
) 