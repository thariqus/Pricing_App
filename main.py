from api import app
import atexit
import os

from scheduler import start_scheduler, stop_scheduler

# ... your existing app setup / blueprints ...

start_scheduler()
atexit.register(stop_scheduler)
# from modules.schedule.initiate_cheduler import scheduler

if __name__ == "__main__":
    app.run(debug=True)