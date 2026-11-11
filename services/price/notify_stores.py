from flask import current_app, request
import threading
import os
from services.price.store_price_upload import run_replication
from data.response import marshal_response_msg
from data.error_codes import BAD_REQUEST, SUCCESS, INITIATING_FUNCTION
from utils.log_response import _respond

IS_CENTRAL = os.getenv("IS_CENTRAL")
SOURCE = "/api/items/notify_stores"

def response_log(custom_message, code, error, response_message=None):
    return _respond(
        body={},
        custom_message=custom_message,
        ipaddress=request.remote_addr,
        response_message=response_message,
        source="service",
        log_type="Notify store",
        message_code=f"PP{code}",
        log_status=code,
        error=error
    )

def notify_store():
    response_log("Entered in notify store function", INITIATING_FUNCTION, False)
    if IS_CENTRAL == "1":
        return marshal_response_msg({
            "error_message" : "Does not sync from itself",
            "error_details" : "HO does not sync from itself",
            "error_code" : BAD_REQUEST,
            "is_error" : True,
            "custom_field" : {
                "status": "skipped"
            }
        })
    app = current_app._get_current_object()

    thread = threading.Thread(
        target=run_replication,
        args=(app,),
        daemon=True
    )
    thread.start()

    response_log("Notify store function completed", SUCCESS, False)
    return marshal_response_msg({
        "success_message" : "Success",
        "success_code" : SUCCESS,
        "source" : SOURCE,
        "is_error" : False
    })
