from html import escape
from flask_wtf import FlaskForm
from wtforms.widgets import HTMLString, html_params
from wtforms.validators import DataRequired, Length, NumberRange, Email, EqualTo, Regexp, InputRequired
from wtforms import StringField, SubmitField, BooleanField, SelectField, SelectMultipleField, IntegerField, \
    PasswordField, ValidationError
from crontab import CronTab
from flask_login import current_user
from cronmon.models import Business, TaskMonitor, Notifier, Permission, User


def perm_check(query_all):
    """根据业务权限调整查询语句"""
    perm_list = Permission.select().where(Permission.perm_user_id == current_user.id).get().perm_list.split()
    if not perm_list == ['0']:
        query = query_all.where(Business.id.in_(perm_list))
    else:
        query = query_all

    return query


def validate_crontab(form, field):
    """crontab字段格式校验"""
    try:
        CronTab(field.data).next(default_utc=False)
    except:
        raise ValidationError('非法的crontab格式')


class SearchForm(FlaskForm):
    """搜索表单基类"""
    search_content = StringField('搜索内容', validators=[DataRequired(message='不能为空'),
                                                     Length(1, 64, message='长度不正确')])
    submit = SubmitField('提交')


class BusinessForm(FlaskForm):
    """业务表单"""
    business_name = StringField('业务名', validators=[DataRequired(message='不能为空'),
                                                   Length(2, 64, message='长度不正确')])
    status = BooleanField('生效标识')
    submit = SubmitField('提交')


class BusinessSearchForm(SearchForm):
    """业务搜索表单"""
    search_by = SelectField('搜索项', choices=[('business_name', '业务名')])


class NotifierForm(FlaskForm):
    """通知人表单"""
    notify_name = StringField('通知人姓名',
                              validators=[DataRequired(message='不能为空'), Length(2, 64, message='长度不正确')])
    notify_email = StringField('邮件地址', validators=[Email(message='无效邮件地址.')])
    notify_tel = StringField('电话号码',
                             validators=[DataRequired(message='不能为空'), Length(11, 11, message='长度不正确')])
    status = BooleanField('生效标识')
    submit = SubmitField('提交')


class NotifierSearchForm(SearchForm):
    """通知人搜索表单"""
    search_by = SelectField('搜索项', choices=[('notify_name', '通知人姓名'),
                                            ('notify_email', '邮件地址'), ('notify_tel', '电话号码')])


class BusinessNotifierForm(FlaskForm):
    """业务和通知人表单"""
    business = SelectField('业务名', coerce=int)
    notifier = SelectField('通知人', coerce=int)
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(BusinessNotifierForm, self).__init__(*args, **kwargs)
        query_all = Business.select(Business.id, Business.business_name)
        query = perm_check(query_all)

        self.business.choices = [(business.id, business.business_name)
                                 for business in query]
        self.notifier.choices = [(notifier.id, notifier.notify_name)
                                 for notifier in Notifier.select(Notifier.id, Notifier.notify_name)]


class BusinessNotifierFormNew(BusinessNotifierForm):
    """业务和通知人表单（根据status过滤）"""
    def __init__(self, *args, **kwargs):
        super(BusinessNotifierFormNew, self).__init__(*args, **kwargs)
        query_all = Business.select(Business.id, Business.business_name).where(Business.status == True)
        query = perm_check(query_all)

        self.business.choices = [(business.id, business.business_name)
                                 for business in query]
        self.notifier.choices = [(notifier.id, notifier.notify_name)
                                 for notifier in Notifier.select
                                 (Notifier.id, Notifier.notify_name).where(Notifier.status == True)]


class BusinessNotifierSearchForm(SearchForm):
    """业务和通知人搜索表单"""
    search_by = SelectField('搜索项', choices=[('business_name', '业务名'), ('notify_name', '通知人')])


class TaskForm(FlaskForm):
    """任务表单"""
    name = StringField('任务名', validators=[DataRequired(message='不能为空'), Length(3, 64, message='长度不正确')])
    url = StringField('监控URL', default=TaskMonitor.gen_uuid)
    period = StringField('循环周期', validators=[InputRequired(), validate_crontab,
                                             Regexp('^ *(\S+ +){4}\S+ *$', message='只能包含5个字段')])
    grace_time = IntegerField('超时时间', validators=[NumberRange(min=1, message='必须大于等于1')])
    status = BooleanField('生效标识')
    business = SelectField('Business', coerce=int)
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        query_all = Business.select(Business.id, Business.business_name)
        query = perm_check(query_all)

        self.business.choices = [(business.id, business.business_name)
                                 for business in query]


class TaskFormNew(TaskForm):
    """任务表单（根据status过滤）"""
    def __init__(self, *args, **kwargs):
        super(TaskFormNew, self).__init__(*args, **kwargs)
        query_all = Business.select(Business.id, Business.business_name).where(Business.status == True)
        query = perm_check(query_all)
        self.business.choices = [(business.id, business.business_name)
                                 for business in query]


class TaskSearchForm(SearchForm):
    """任务搜索表单"""
    search_by = SelectField('搜索项', choices=[('name', '任务名'), ('url', '监控URL'), ('business_name', '业务名')])


class PermissionForm(FlaskForm):
    """用户权限表单"""
    username = StringField('用户名', validators=[DataRequired(message='不能为空'), Length(8, 64, message='长度不正确')])
    password = StringField('密码', default=User.generate_init_password)
    email = StringField('邮件地址', validators=[Email(message='无效邮件地址.')])
    phone = StringField('电话号码', validators=[DataRequired(message='不能为空'), Length(11, 11, message='长度不正确')])
    api_username = StringField('API用户名', validators=[Length(8, 32, message='长度不正确')])
    api_password = StringField('API密码', validators=[Length(0, 32, message='长度不正确')])
    admin = BooleanField('是否系统管理员')
    status = BooleanField('生效标识')
    submit = SubmitField('提交')


class PermissionSearchForm(SearchForm):
    """用户权限搜索表单"""
    search_by = SelectField('搜索项', choices=[('username', '用户名')])


class SelectCheckbox(object):
    """复选框widget"""
    def __call__(self, field, **kwargs):
        html = ['']
        for val, label, selected in field.iter_choices():
            html.append(self.render_option(field.name, val, label, selected))
        return HTMLString(u''.join(html))

    @classmethod
    def render_option(cls, name, value, label, selected):
        """复选框html样式生成"""
        options = {'value': value}
        if selected:
            options['checked'] = u'checked'
        return HTMLString(u'<label class="checkbox inline col-lg-2 cbcustomed"><input type="checkbox" name="%s" %s>'
                          u'<span>%s</span></input></label>' % (name, html_params(**options), escape(label)))


class PermissionBizForm(FlaskForm):
    """业务权限表单"""
    business = SelectMultipleField(coerce=int, widget=SelectCheckbox())
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(PermissionBizForm, self).__init__(*args, **kwargs)
        query = Business.select(Business.id, Business.business_name)
        self.business.choices = [(business.id, business.business_name)
                                 for business in query]


class ResetPasswordForm(FlaskForm):
    """密码重置表单"""
    username = StringField('用户名', validators=[DataRequired(message='不能为空'), Length(8, 64, message='长度不正确')])
    new_password = PasswordField('新密码', validators=[DataRequired(message='不能为空'),
                                                    Length(8, 32, message='长度不正确'),
                                                    EqualTo('new_password_second', message='二次输入的新密码不一致')])
    new_password_second = PasswordField('新密码重输',
                                        validators=[DataRequired(message='不能为空'), Length(8, 32, message='长度不正确')])
    submit = SubmitField('提交')


class ChangePasswordForm(ResetPasswordForm):
    """密码修改表单"""
    old_password = PasswordField('原密码', validators=[DataRequired(message='不能为空'),
                                                    Length(8, 32, message='长度不正确')])
