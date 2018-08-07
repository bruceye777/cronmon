from flask import g
from flask_httpauth import HTTPBasicAuth
from cronmon.api.errors import unauthorized, forbidden
from cronmon.models import User, AnonymousUser
from . import api_1_0

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(api_username, api_password):
    """验证api用户名和api密码"""
    if api_username and api_password:
        try:
            user = User.get(User.api_username == api_username, User.status == True)
        except:
            g.current_user = AnonymousUser()
            return True
    else:
        return False
    g.current_user = user
    return user.verify_api_password(api_password)


@api_1_0.before_request
@auth.login_required
def before_request():
    """禁止匿名用户访问"""
    if g.current_user.is_anonymous():
        return forbidden('Active user only')


@auth.error_handler
def auth_error():
    """错误处理"""
    return unauthorized('Invalid credentials')
