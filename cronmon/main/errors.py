from flask import render_template, request, jsonify
from . import main


def error_response(code, msg):
    """错误响应"""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify(msg)
        response.status_code = code
        return response
    return render_template('errors/'+str(code)+'.html'), code


@main.app_errorhandler(401)
def unauthorized(e):
    """401错误处理"""
    return error_response(401, {'error': 'unauthorized'})


@main.app_errorhandler(403)
def forbidden(e):
    """403错误处理"""
    return error_response(403, {'error': 'forbidden'})


@main.app_errorhandler(404)
def page_not_found(e):
    """404错误处理"""
    return error_response(404, {'error': 'not found'})


@main.app_errorhandler(500)
def internal_server_error(e):
    """500错误处理"""
    return error_response(500, {'error': 'internal server error'})
