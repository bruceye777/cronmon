from datetime import timedelta
from io import BytesIO
from flask import render_template, redirect, request, url_for, flash, current_app, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from cronmon import get_logger, get_config
from cronmon.models import User, session_token_generate
from cronmon.utils import create_validate_code
from . import auth
from .forms import LoginForm


LOGGER = get_logger(__name__)
CFG = get_config()


def request_log():
    """日志记录"""
    client_ip = str(request.remote_addr)
    url = request.url
    method = request.method
    user = current_user.username
    msg = ' - '.join((client_ip, method, url, user))
    LOGGER.info(msg)


@auth.after_request
def after_request(response):
    """请求之后，如果用户已认证，且是登录请求，则记录日志"""
    if current_user.is_authenticated and request.endpoint[5:] == 'login':
        request_log()
    return response


@auth.before_request
def before_request():
    """请求之前，如果用户已认证，且是登出请求，则记录日志"""
    if current_user.is_authenticated and request.endpoint[5:] == 'logout':
        request_log()

    url_prefix = CFG.URL_ROOT.split('/')[2]
    url_check = request.headers.get("Referer")

    if not url_check:
        url_check = url_prefix
    if not url_check.startswith('http://'+url_prefix) and not url_check.startswith('https://'+url_prefix)\
            and not url_check.startswith(url_prefix):
        abort(403)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """登录路由函数"""
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.get(User.username == form.username.data)
            # 如果用户不为空，且密码正确，不被禁用以及验证码正确（如有），则允许登录系统
            if user is not None and user.verify_password(form.password.data) and user.is_active() \
                    and (session.get('img') == form.recaptcha.data.upper() or not CFG.VALIDATE_CODE_USE):
                duration = timedelta(days=7)
                login_user(user, form.rememberme.data, duration=duration)
                return redirect(request.args.get('next') or url_for('main.index'))
            elif not user.is_active() and not user.is_anonymous():
                flash('账户被禁用')
            elif CFG.VALIDATE_CODE_USE and not session.get('img') == form.recaptcha.data.upper():
                flash('验证码错误')
            else:
                flash('密码错误')
        except User.DoesNotExist:
            flash('用户名错误')
        except:
            flash('登录异常')
    return render_template('auth/login.html', form=form, code=CFG.VALIDATE_CODE_USE)


@auth.route('/logout')
@login_required
def logout():
    """登出路由函数，登出时重写session token，确保session失效"""
    user = User.get(User.id == current_user.id)
    logout_user()
    user.session_token = session_token_generate()
    user.save()
    flash('您已退出登录')
    return redirect(url_for('auth.login'))


@auth.route('/code')
def get_code():
    """验证码验证路由函数"""
    code_img, strs = create_validate_code()
    buf = BytesIO()
    code_img.save(buf, 'jpeg')
    buf_str = buf.getvalue()
    response = current_app.make_response(buf_str)
    response.headers['Content-Type'] = 'image/gif'
    session['img'] = strs.upper()
    return response
