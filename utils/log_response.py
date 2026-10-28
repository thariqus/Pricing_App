from flask import jsonify
from repository.price.create_log import write_log


def _respond(body, source, log_type, log_status, custom_message, message_code, error, response_message=None, ipaddress=None):
    """Write the log row, then return the JSON response."""
    write_log(
        custom_message=custom_message,
        response_message=response_message or body.get("message"),
        source=source,
        log_type=log_type,
        message_code=message_code,
        log_status=log_status,
        info=not error,
        error=error,
        ipaddress = ipaddress
    )
    return jsonify(body), log_status