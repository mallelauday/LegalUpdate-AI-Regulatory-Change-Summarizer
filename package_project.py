import os
import zipfile
from pathlib import Path

def create_project_zip():
    root_dir = Path(__file__).resolve().parent
    zip_path = root_dir / "LegalUpdate_AI_Regulatory_Change_Summarizer.zip"
    
    ignore_dirs = {
        "venv", ".venv", "node_modules", "__pycache__", ".git", ".gemini", "dist"
    }
    ignore_extensions = {".pyc", ".pyo"}
    
    print(f"Creating clean production ZIP archive at: {zip_path}")
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            
            for file in files:
                if file.endswith(".zip") or any(file.endswith(ext) for ext in ignore_extensions):
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(root_dir)
                zipf.write(file_path, arcname)
                file_count += 1
                
    zip_size_kb = zip_path.stat().st_size / 1024
    print(f"Successfully packaged {file_count} files into ZIP ({zip_size_kb:.2f} KB).")

if __name__ == "__main__":
    create_project_zip()

