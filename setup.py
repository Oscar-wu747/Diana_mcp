from setuptools import setup, find_packages

setup(
    name="diana-mcp-agent",
    version="0.1.0",
    description="Diana 机器人 MCP 代理服务器",
    author="Your Name",
    author_email="your.email@example.com",
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=2.0.0",
    ],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)