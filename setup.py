from pathlib import Path

from setuptools import find_packages, setup


def get_requirements() -> list[str]:
    path = Path(__file__).parent / "requirements.txt"
    lines = (line.strip() for line in path.read_text().splitlines()) if path.exists() else ()
    return [line for line in lines if line and not line.startswith(("#", "-"))]


setup(
    name="flipkart-shopping-assistant",
    version="0.2.0",
    author="Yunus Shaikh",
    description="RAG shopping assistant over Flipkart product reviews",
    packages=find_packages(include=["flipkart", "flipkart.*"]),
    install_requires=get_requirements(),
    python_requires=">=3.10",
)
