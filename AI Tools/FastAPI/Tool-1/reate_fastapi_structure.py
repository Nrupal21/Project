import os

# Define the folder structure
folders = [
    "app",
    "app/api",
    "app/api/v1",
    "app/api/v1/endpoints",
    "app/models",
    "app/schemas",
    "app/services",
    "tests"
]

# Create the folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create __init__.py files
init_files = [
    "app/__init__.py",
    "app/api/__init__.py",
    "app/api/v1/__init__.py",
    "app/api/v1/endpoints/__init__.py",
    "app/models/__init__.py",
    "app/schemas/__init__.py",
    "app/services/__init__.py",
    "tests/__init__.py"
]

for init_file in init_files:
    with open(init_file, 'w') as f:
        pass  # Create an empty __init__.py file

# Create main.py and example files
with open("app/main.py", 'w') as f:
    f.write("# Main entry point for the FastAPI application\n")

with open("app/api/v1/endpoints/example.py", 'w') as f:
    f.write("# Example endpoint file\n")

with open("app/models/example_model.py", 'w') as f:
    f.write("# Example model file\n")

with open("app/schemas/example_schema.py", 'w') as f:
    f.write("# Example schema file\n")

with open("app/services/example_service.py", 'w') as f:
    f.write("# Example service file\n")

with open("tests/test_example.py", 'w') as f:
    f.write("# Test cases for the application\n")

with open("requirements.txt", 'w') as f:
    f.write("# List your project dependencies here\n")

with open("README.md", 'w') as f:
    f.write("# Project Title\n\n## Description\n\nProject description goes here.\n")

print("Basic FastAPI folder structure created successfully.")
