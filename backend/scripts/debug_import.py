import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from app.main import app
    print("Import OK")
except Exception as e:
    traceback.print_exc()
