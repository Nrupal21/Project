import os

# Define the folder and file structure
structure = {
    "frontend": {
        "public": {},
        "src": {
            "assets": {},
            "components": {
                "Editor": {},
                "Canvas": {},
                "Chat": {},
                "Dashboard": {}
            },
            "pages": {},
            "utils": {},
            "main.js": ""
        },
        "index.html": ""
    },
    "backend": {
        "app": {
            "routes": {},
            "services": {},
            "models": {},
            "utils": {},
            "auth.py": "",
            "main.py": ""
        },
        "requirements.txt": "",
        "config.py": ""
    },
    "ai_models": {
        "code_ai.py": "",
        "design_ai.py": "",
        "productivity_ai.py": "",
        "audio_ai.py": ""
    },
    "database": {
        "schemas": {},
        "seeders": {},
        "init_db.py": ""
    },
    "storage": {
        "aws_s3.py": ""
    },
    "tests": {
        "frontend": {},
        "backend": {},
        "ai_models": {}
    },
    ".env": "",
    "README.md": "",
    "deploy": {
        "vercel.json": "",
        "render.yaml": "",
        "Dockerfile": ""
    }
}

# Function to create folders and files recursively
def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w") as f:
                if name.endswith(".py"):
                    f.write(f"# {name} - Auto-generated\n")

# Create the project
project_root = "Tool_1"
os.makedirs(project_root, exist_ok=True)
create_structure(project_root, structure)

print(f"✅ Project structure created in ./{project_root}/")
