import os 
from pathlib import Path
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

project_name = "flipkart"

# Define project structure
list_of_files = [
    f"{project_name}/__init__.py",
    f"{project_name}/callbacks.py",
    f"{project_name}/data_converter.py",
    f"{project_name}/data_ingestion.py",
    f"{project_name}/retrieval_generation.py",
    "static/style.css",
    "templates/index.html",
    "setup.py",
    "app.py",
    "requirements.txt",
    ".env",
    "README.md",
    "logs/.gitkeep"
]

# Create project structure
for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Created directory: {filedir}")
    
    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass
        logging.info(f"Created file: {filename}")