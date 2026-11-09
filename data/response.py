def marshal_response_msg(body):
    return {
        "response" : {
            "data" : body.get('data') or [],
            "error" : {
                "error_details" : body.get('error_details') or "",
                "error_code" : body.get('error_code') or "",
                "error_message" : body.get('error_message') or ""
            },
            "info" : {
                "success_message" : body.get('success_message') or "",
                "success_code" : body.get('success_code') or "",
                "source" : body.get('source') or ""
            },
            "custom_fields" : body.get('custom_field') or {},
            "is_error" : body.get('is_error')
        }
    }