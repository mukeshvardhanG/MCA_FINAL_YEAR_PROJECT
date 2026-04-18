import subprocess
import os

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

res = subprocess.run([r"C:\Users\G Mukesh Vardhan\OneDrive\Desktop\My Project\.venv\Scripts\python.exe", r"backend\scripts\_fix_seed.py"], capture_output=True, text=True, cwd=r"C:\Users\G Mukesh Vardhan\OneDrive\Desktop\My Project", encoding='utf-8', env=env)
with open("error.txt", "w", encoding="utf-8") as f:
    f.write(res.stderr)
