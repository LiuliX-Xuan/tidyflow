from setuptools import setup, find_packages

setup(
    name="tidyflow",
    version="0.1.0",
    description="CSV/Excel/JSON 数据清洗 CLI 工具",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="LiuliX",
    url="https://github.com/LiuliX/tidyflow",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "gif": ["Pillow>=9.0.0"],
    },
    entry_points={
        "console_scripts": [
            "tidyflow=tidyflow.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)
