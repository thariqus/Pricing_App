from api import app
import atexit
import os
from modules.schedule.scheduler_job_price_activation import run_scheduler  
import os
import threading
from modules.schedule.scheduler_job_price_activation import run_scheduler

PORT_NUMBER = os.getenv("PORT_NUMBER")

from scheduler import start_scheduler, stop_scheduler

# ... your existing app setup / blueprints ...

# start_scheduler()
# atexit.register(stop_scheduler)
# from modules.schedule.initiate_cheduler import scheduler

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=run_scheduler, kwargs={"interval": 10}, daemon=True).start()
    app.run(debug=True, port=PORT_NUMBER, host="0.0.0.0")
