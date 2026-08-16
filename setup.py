"""
Code Guardian Skill - Setup

Instalacao: pip install -e .
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="code-guardian-skill",
    version="0.1.0",
    author="Miranda (@paulinett1508-dev)",
    description="🛡️ Skill de analise automatizada de codigo para Claude Code - Anti-desperdicio de tokens",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/paulinett1508-dev/code-guardian-skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Security",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "code-guardian=main:main",
        ],
    },
)
