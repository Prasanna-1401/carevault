import os
from pathlib import Path
from dulwich import porcelain
from dulwich.repo import Repo

REPO_PATH = Path(__file__).resolve().parent

def init_and_commit():
    print(f"Working in repository path: {REPO_PATH}")
    
    # 1. Initialize repository if .git doesn't exist
    git_dir = REPO_PATH / ".git"
    if not git_dir.exists():
        repo = porcelain.init(str(REPO_PATH))
        print("Initialized empty Git repository.")
    else:
        repo = Repo(str(REPO_PATH))
        print("Found existing Git repository.")

    # 2. Configure user name & email
    config = repo.get_config()
    config.set((b"user",), b"name", b"Prasanna-1401")
    config.set((b"user",), b"email", b"Prasanna-1401@users.noreply.github.com")
    config.write_to_path()
    print("Configured Git author: Prasanna-1401 <Prasanna-1401@users.noreply.github.com>")

    # 3. Add remote origin
    remote_url = b"https://github.com/Prasanna-1401/carevault.git"
    try:
        config.set((b"remote", b"origin"), b"url", remote_url)
        config.set((b"remote", b"origin"), b"fetch", b"+refs/heads/*:refs/remotes/origin/*")
        config.write_to_path()
        print(f"Configured remote 'origin': {remote_url.decode()}")
    except Exception as e:
        print("Remote config note:", e)

    # 4. Stage tracked files
    tracked_files = [
        "README.md",
        ".gitignore",
        "run.bat",
        "run.ps1",
        "test_suite.py",
        "git_manager.py",
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/database.py",
        "app/security.py",
        "app/storage.py",
        "app/seed_data.py",
        "app/services/__init__.py",
        "app/services/ai_assistant.py",
        "app/services/prescription_reader.py",
        "app/services/duplicate_detector.py",
        "app/services/translator.py",
        "app/services/question_generator.py",
        "app/services/hospital_matcher.py",
        "app/services/consent_service.py",
        "app/routers/__init__.py",
        "app/routers/auth.py",
        "app/routers/patients.py",
        "app/routers/records.py",
        "app/routers/consents.py",
        "app/routers/ai.py",
        "app/routers/hospitals.py",
        "app/routers/audit.py",
        "app/routers/lab.py",
        "app/routers/doctor.py",
        "app/routers/admin.py",
        "app/static/css/custom.css",
        "app/static/js/app.js",
        "app/templates/index.html"
    ]

    # Create empty __init__.py if missing
    for p in ["app/__init__.py", "app/services/__init__.py", "app/routers/__init__.py"]:
        init_file = REPO_PATH / p
        if not init_file.exists():
            init_file.parent.mkdir(parents=True, exist_ok=True)
            init_file.write_text("# CareVault AI package\n", encoding="utf-8")

    existing_files = [f for f in tracked_files if (REPO_PATH / f).exists()]
    
    porcelain.add(str(REPO_PATH), paths=existing_files)
    print(f"Staged {len(existing_files)} files into Git index.")

    # 5. Commit
    commit_msg = b"Initial release: CareVault AI - Patient-Controlled Digital Health Wallet & Clinical Decision Support"
    commit_sha = porcelain.commit(
        str(REPO_PATH),
        message=commit_msg,
        committer=b"Prasanna-1401 <Prasanna-1401@users.noreply.github.com>",
        author=b"Prasanna-1401 <Prasanna-1401@users.noreply.github.com>"
    )
    print(f"Commit created successfully! Hash: {commit_sha.decode()[:8]}")

    # Set branch to main
    try:
        repo.refs[b"refs/heads/main"] = commit_sha
        repo.refs.set_symbolic_ref(b"HEAD", b"refs/heads/main")
        print("Branch set to 'main'.")
    except Exception as e:
        print("Branch note:", e)

    print("\nGit repository successfully configured and committed for Prasanna-1401!")

if __name__ == "__main__":
    init_and_commit()
