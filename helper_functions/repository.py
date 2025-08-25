import os 
os.environ.setdefault("CHROMA_DB_IMPL", "duckdb+parquet")
os.environ.setdefault("CREWAI_STORAGE_DIR", ".crewai_storage")

import sys 
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

# <---Libraries--->
import gdown, os, re, shutil, time, zipfile

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env")
DOCUMENT_EXTENSION_ALLOWED = {".doc",".docx", ".md", ".pdf", ".txt"}

# <---Database--->
repository_source = "1FpsgCX_-wVXbINFWkI3mLjyklEzMYjGw" # Link to Google Drive
repository_zip = Path("repository.zip") # Path of downloaded zip_folder
repository_directory = Path("repository") # Unzipped base repository folder
DATA_ROOT = Path("data") # Storage for per-user data

if not repository_zip.exists():
    gdown.download(id = repository_source, output = str(repository_zip), quiet = False) # Download process
repository_directory.mkdir(parents = True, exist_ok = True)
with zipfile.ZipFile(repository_zip, "r") as file: # Extraction of zipped folder
    file.extractall(repository_directory)

def check_extension(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in DOCUMENT_EXTENSION_ALLOWED # Check compatibility of documents

def check_documents(directory: Path):
    for path in directory.rglob("*"):
        if check_extension(path):
            yield path # Filter compatible documents

documents = list(check_documents(repository_directory)) # Compilation of all PDFs
print(f"Found {len(documents)} documents:")
for document in documents:
    print(" -", document)

# <---Per-user Data--->
def sanitise(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)[:200] # Replaces unsafe characters with "_" and truncates to 200 characters

def get_user_root(user_key: str) -> Path:
    key = sanitise(user_key)
    root = DATA_ROOT / key
    root.mkdir(parents = True, exist_ok = True) # Creates a new folder for the user, if not existent
    return root

def get_user_uploads(user_key: str) -> Path:
    directory = get_user_root(user_key) / "user_uploads"
    directory.mkdir(parents = True, exist_ok = True) # Creates a new folder for user uploads, if not existent
    return directory

def get_user_repository(user_key: str) -> Path:
    directory = get_user_root(user_key) / "repository_working"
    directory.mkdir(parents = True, exist_ok = True) # Creates a new folder for the working repository, if not existent
    return directory

def list_user_uploads(user_key: str) -> list[Path]:
    uploads = get_user_uploads(user_key)
    return sorted([file for file in uploads.iterdir() if file.is_file()]) # Returns a list of existing user uploads in his/her folder

def save_user_uploads(user_files: list | None, user_key: str) -> list[Path]:
    saved = []
    if not user_files:
        return saved
    directory_uploads = get_user_uploads(user_key)
    for user_file in user_files:
        name = sanitise(user_file.name)
        target = directory_uploads / name
        if target.exists():
            timestamp = int(time.time())
            target = directory_uploads / f"{target.stem}_{timestamp}{target.suffix}" # Append a timestamp if a file with the same exists, so it does not overwrite it
        with open(target, "wb") as file:
            file.write(user_file.getbuffer())
        saved.append(target)
    return saved # Return the list of saved paths.

# <--Repository--->
def prepare_repository(user_files: list | None, user_key: str, selected_file_names: list[str] | None) -> Path:
    _ = save_user_uploads(user_files, user_key) # Save new files uploaded by user into their own folder
    
    repository_working = get_user_repository(user_key)
    for path in repository_working.iterdir():
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path) # Clears working repository, so the next request is refreshed
    
    for document in check_documents(repository_directory):
        shutil.copy2(document, repository_working / document.name) # Copy base repository into the user's working folder
    
    if selected_file_names:
        directory_uploads = get_user_uploads(user_key)
        for name in selected_file_names:
            source = directory_uploads / name
            if check_extension(source) and source.exists():
                shutil.copy2(source, repository_working / source.name) # Copy selected file if it exists and is of compatible extension

    list_documents = [path for path in repository_working.iterdir() if path.is_file()]
    print(f"[{user_key}] Working repository contains {len(list_documents)} files.")
    return repository_working