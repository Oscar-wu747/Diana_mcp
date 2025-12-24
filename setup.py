from setuptools import find_packages, setup

setup(
    name="diana-mcp-agent",
    version="0.1.0",
    description="Diana 机器人 MCP 代理服务器",
    author="Oscar-wu747",
    author_email="2949583437@qq.com",
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.12.0",
            "isort>=5.13.0",
        ],
    },
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
