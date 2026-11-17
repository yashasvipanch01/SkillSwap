from pathlib import Path

folders = [
    "app/core", "app/db", "app/models", "app/schemas", "app/services", "app/routers",
    "tests", "docs", "migrations/versions",
]
packages = [
    "app", "app/core", "app/db", "app/schemas", "app/services", "app/routers", "tests",
]

for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)
for package in packages:
    (Path(package) / "__init__.py").touch()

print("Folders ready.")
