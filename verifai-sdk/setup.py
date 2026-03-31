"""Setup configuration for VerifAI SDK"""

from setuptools import setup, find_packages


with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="verifai-sdk",
    version="1.0.0",
    author="VerifAI Team",
    author_email="support@verifai.ai",
    description="Python SDK for VerifAI - AI Quality Review",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/verifai/verifai-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "verifai=verifai_sdk.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
