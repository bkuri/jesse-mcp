#!/usr/bin/env python3
"""
Setup configuration for jesse-mcp package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="jesse-mcp",
    version="1.0.0",
    author="Jesse Team",
    description="MCP server for quantitative trading analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "*.tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
        "jedi>=0.19.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
        "typing-extensions",
        "scikit-learn>=1.3.0",
        "scipy>=1.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
        "optuna": [
            "optuna>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jesse-mcp=jesse_mcp.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
