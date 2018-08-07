from flask import jsonify


def error_response(code, error, msg):
    """错误响应"""
    response = jsonify({'error': error, 'message': msg})
    response.status_code = code
    return response


def bad_request(message):
    """400错误处理"""
    return error_response(400, 'Bad Request', message)


def unauthorized(message):
    """401错误处理"""
    return error_response(401, 'Unauthorized', message)


def forbidden(message):
    """403错误处理"""
    return error_response(403, 'Forbidden', message)
