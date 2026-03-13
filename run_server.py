import traceback
import sys

try:
    from api.main import app
    import uvicorn
    print("App imported successfully. Running uvicorn...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
except BaseException as e:
    print("FATAL ERROR DURING STARTUP:")
    traceback.print_exc()
    sys.exit(1)
