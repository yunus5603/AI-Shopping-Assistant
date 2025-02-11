from setuptools import find_packages, setup
from typing import List
import os

def get_requirements() -> List[str]:
    """Read requirements.txt file and return list of requirements."""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []

    if os.path.exists(requirements_path):
        with open(requirements_path) as f:
            requirements = [req.strip() for req in f.readlines()]
            requirements = [req for req in requirements if req and not req.startswith('#') and req != "-e ."]

    return requirements

setup(
    name="flipkart",
    version="0.0.1",
    author="Yunus Shaikh",
    author_email="syunus838@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements()
)
