from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    recaptcha = StringField('验证码')
    rememberme = BooleanField('一周内自动登录')
    submit = SubmitField('提交')
