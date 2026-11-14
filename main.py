from api import app
import atexit
import os
from modules.schedule.scheduler_job_price_activation import run_scheduler  
import os
import threading
from modules.schedule.scheduler_job_price_activation import run_scheduler
from modules.schedule.scheduler_job_store_price_replication import run_replication_scheduler
from flask_cors import CORS

PORT_NUMBER = os.getenv("PORT_NUMBER")

from scheduler import start_scheduler, stop_scheduler

# ... your existing app setup / blueprints ...

# start_scheduler()
# atexit.register(stop_scheduler)
# from modules.schedule.initiate_cheduler import scheduler

CORS(app, resources={
    r"/*": {
        "origins": ['*']
    }
})

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=run_scheduler, kwargs={"interval": 10}, daemon=True).start()
        threading.Thread(target=run_replication_scheduler, args=(app,), daemon=True).start()

    app.run(debug=True, port=PORT_NUMBER, host="0.0.0.0")
