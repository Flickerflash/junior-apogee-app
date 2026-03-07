"""
setup.py for Junior Apogee
"""
from setuptools import setup, find_packages

setup(
    name="junior-apogee",
    version="0.1.0b0",
    description="AI Agent Evaluation & QA Platform",
    author="Ndr (Flickerflash)",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0.0",
        "python-dotenv>=0.21.0",
        "requests>=2.31.0",
        "anthropic>=0.7.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "pyyaml>=6.0",
        "pandas>=2.0.0",
        "click>=8.1.0",
        "colorama>=0.4.6",
        "tqdm>=4.66.0",
        "loguru>=0.7.0",
    ],
)
