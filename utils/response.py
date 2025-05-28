from flask import jsonify


def success(message="Success", data=None, status_code=200, meta=None):
    """
    Creates a standardized success response structure for API responses.

    Args:
        message (str): The success message to be included in the response. Default is "Success".
        data (any): The data to be returned in the response. Default is None.
        status_code (int): The HTTP status code for the response. Default is 200.
        meta (dict): Optional metadata (e.g., pagination info). Default is None.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    response = {"status": "success", "message": message, "data": data}

    if meta is not None:
        response["meta"] = meta

    return jsonify(response), status_code


def failure(message="Something went wrong", errors=None, status_code=400):
    """
    Creates a standardized failure response structure for API responses.

    Args:
        message (str): The error message to be included in the response. Default is "Something went wrong".
        errors (any): The errors to be included in the response. Default is None.
        status_code (int): The HTTP status code for the response. Default is 400.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    response = {"status": "error", "message": message, "errors": errors}
    return jsonify(response), status_code
