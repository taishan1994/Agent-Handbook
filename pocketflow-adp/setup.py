from setuptools import setup, find_packages

try:
    with open("README.MD", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A utility package for the Agent Handbook project, providing tools for LLM interaction and web search."

setup(
    name="agent-handbook-utils",
    version="0.1.0",
    description="Utility functions for the Agent Handbook project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Agent Handbook Team",
    author_email="",
    url="",
    packages=['agent_handbook_utils'],
    package_dir={'agent_handbook_utils': 'agent_handbook_utils'},
    include_package_data=True,
    install_requires=[
        "openai>=1.0.0",
        "numpy>=1.20.0",
        "aiohttp>=3.8.0",
        "requests>=2.27.0",
        "beautifulsoup4>=4.11.0",
        "jieba>=0.42.1",
        "tqdm>=4.64.0",
        "lxml>=4.9.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)