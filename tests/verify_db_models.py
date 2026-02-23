import sys
sys.stderr = open('error.log', 'w')
try:
    from modules.core.db_models import *
    print("Import successful")
    init_db()
    print("init_db successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
