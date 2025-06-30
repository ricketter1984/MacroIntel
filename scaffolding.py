import os

# Define the folder and file structure
structure = {
    "event_tracker": ["econ_event_tracker.py"],
    "news_scanner": ["news_insight_feed.py"],
    "alerting": ["alert_manager.py"],
    "insight_engine": ["macro_insight_builder.py"],
    "utils": ["api_clients.py"],
    "config": ["__init__.py"],
    "data": ["event_log.json"],
}

# Base files
base_files = ["main.py", "requirements.txt", "README.md", ".env"]

def create_structure():
    # Create base files
    for file in base_files:
        if not os.path.exists(file):
            with open(file, "w") as f:
                f.write("")
            print(f"Created file: {file}")
    
    # Create subfolders and their files
    for folder, files in structure.items():
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")
        for file in files:
            path = os.path.join(folder, file)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write("")
                print(f"  Created file: {file}")

if __name__ == "__main__":
    create_structure()
