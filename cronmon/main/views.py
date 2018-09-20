import math
from datetime import datetime, timedelta
import peewee
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from cronmon import get_logger, get_config
from cronmon import utils
from cronmon.utils import admin_required, list_gen
from cronmon.models import DB, User, Permission, Notifier, Business, BusinessNotifier, TaskMonitor, TaskMonitorLog
from cronmon.main.forms import BusinessForm, BusinessSearchForm, NotifierForm, NotifierSearchForm, \
    BusinessNotifierForm, BusinessNotifierFormNew, BusinessNotifierSearchForm, TaskForm, TaskFormNew, TaskSearchForm, \
    PermissionForm, PermissionSearchForm, PermissionBizForm, ResetPasswordForm, ChangePasswordForm
from . import main


# 在日志中记录模块名称（__name__），以及获取全局配置
LOGGER = get_logger(__name__)
CFG = get_config()


@main.after_request
def after_request(response):
    """请求之后，如果用户是已认证用户，则记录日志"""
    if current_user.is_authenticated:
        client_ip = str(request.remote_addr)
        url = request.url
        method = request.method
        code = str(response.status_code)
        user = current_user.username
        msg = ' - '.join((client_ip, method, url, code, user))
        LOGGER.info(msg)
    return response


@main.before_request
def before_request():
    """请求之前，判断用户是否正常登录，未通过则返回错误以及是否是正确的Referer（为空则忽略）"""
    if not current_user.is_anonymous():
        if not current_user.is_active():
            abort(401)

    url_prefix = CFG.URL_ROOT.split('/')[2]
    url_check = request.headers.get("Referer")

    if not url_check:
        url_check = url_prefix
    if not url_check.startswith('http://'+url_prefix) and not url_check.startswith('https://'+url_prefix)\
            and not url_check.startswith(url_prefix):
        abort(403)


def data_count(db_model, biz_perm):
    """首页dashboard数据获取，按照biz_perm值进行区别获取

    :param db_model: 数据库model
    :param biz_perm: 用户业务权限
    :return: 目前记录数、30天前记录数以及二者直接的环比，如果30天前记录数为0，则显示为inf（无限）
    """
    day30 = datetime.now() - timedelta(days=30)

    total_query = db_model.select()
    total_query_before30 = db_model.select().where(db_model.create_datetime < day30)

    if biz_perm != ['0']:
        if db_model == Business:
            total_query = total_query.where(Business.id.in_(biz_perm))
            total_query_before30 = total_query_before30.where(Business.id.in_(biz_perm))
        elif db_model == TaskMonitorLog:
            total_query = total_query.join(TaskMonitor, on=(TaskMonitorLog.taskmon_id == TaskMonitor.id))\
                .join(Business, on=(TaskMonitor.business == Business.id)).where(Business.id.in_(biz_perm))
            total_query_before30 = total_query_before30\
                .join(TaskMonitor, on=(TaskMonitorLog.taskmon_id == TaskMonitor.id))\
                .join(Business, on=(TaskMonitor.business == Business.id)).where(Business.id.in_(biz_perm))
        else:
            total_query = total_query.join(Business).where(Business.id.in_(biz_perm))
            total_query_before30 = total_query_before30.join(Business).where(Business.id.in_(biz_perm))

    total_count = total_query.count()
    total_count_before30 = total_query_before30.count()

    if total_count_before30 == 0:
        total_count_diff_rate = float("inf")
    else:
        total_count_diff_rate = abs(round(100*(total_count-total_count_before30)/total_count_before30, 2))

    return total_count, total_count_before30, total_count_diff_rate


def get_parm():
    """获取http请求的参数以及用户业务权限列表

    :return: 操作列表、相应model id、业务id、页码、每页显示记录数、搜索内容，搜索字段、用户业务权限
    """
    action = request.values.get('action')
    id = request.values.get('id')
    bid = str(request.values.get('bid'))
    page = int(request.values.get('page')) if request.values.get('page') else 1
    length = int(request.values.get('length')) if request.values.get('length') else CFG.ITEMS_PER_PAGE
    search_content = '' if request.values.get('search_content') is None else request.values.get('search_content')
    search_by = '' if request.values.get('search_by') is None else request.values.get('search_by')
    biz_perm = Permission.select().where(Permission.perm_user == current_user.id).get().perm_list.split()

    return action, id, bid, page, length, search_content, search_by, biz_perm


def query_string(query_type, model1, search_by='', search_content='', model2='', choice='first', many=None):
    """查询语句拼接

    :param query_type: ‘where’语句或‘orderby’语句
    :param model1: 第一个数据库model
    :param search_by: 搜索字段
    :param search_content: 搜索内容
    :param model2: 第二个数据库model
    :param choice: 'where'基于model1（first）还是model2
    :param many: 多对多关联查询switch model
    :return: 拼接后的查询字符串
    """
    if not model2:
        str1 = model1 + '.select().'
    else:
        str1 = model1 + '.select().join(' + model2 + ').'

    if many:
        str1 = many + '.select().join(' + model1 + ').switch(' + many + ').join(' + model2 + ').'

    if query_type == 'where':
        if choice == 'first':
            str2 = 'where(' + model1 + '.search_by.contains("search_content"))'
        else:
            str2 = 'where(' + model2 + '.search_by.contains("search_content"))'
    else:
        str2 = 'order_by(' + model1 + '.id)'

    query_output = (str1 + str2).replace('search_by', search_by).replace('search_content', search_content)

    return query_output


def query_limit(query_all, perm, biz_perm, page, length):
    """根据业务权限和是否分页调整查询语句

    :param query_all: 查询语句
    :param perm: 是否进行权限检查
    :param biz_perm: 用户业务权限
    :param page: 页码
    :param length: 每页显示记录数
    :return: 调整后的查询语句
    """

    # 如果不进行权限检查或用户为超级管理员（perm_list为‘0’）则不调整查询语句，否则则根据perm_list的业务id进行过滤
    if not perm or biz_perm == ['0']:
        query = query_all
    else:
        query = query_all.where(Business.id.in_(biz_perm))

    total_count = query.count()

    if page:
        query = query.paginate(page, length)

    return query, total_count


def perm_check(action, *pospara):
    """操作权限检查

    :param action: 目前只有一种，‘del’（删除）操作
    :param *pospara: 相关位置参数，包括id（model id）、bid（业务id）、biz_perm（用户业务权限）和数据库model
    :return: 无
    """
    if action == 'del':
        id, bid, biz_perm, db_model = pospara
        # 如果请求为'POST'方法，id存在且bid在perm_list中或用户为超级管理员（perm_list为‘0’），则进行删除操作，否则提示无权限
        if request.method == 'POST' and id and (bid in biz_perm or biz_perm == ['0']):
            try:
                db_model.get(db_model.id == id).delete_instance(recursive=True)
                if db_model == TaskMonitor:
                    TaskMonitorLog.delete().where(TaskMonitorLog.taskmon_id == id).execute()
                flash('删除成功')
            except:
                flash('删除失败')
        else:
            abort(403)


def get_form_validate(form):
    """GET表单校验

    :param form: 被校验表单
    :return: 通过校验后的实例化表单
    """
    form = form(request.args)
    if request.method == 'GET' and form.submit.data and not form.validate():
        abort(403)

    return form


def form_edit(db_model, form, template, form2=False):
    """通用编辑模版（新增和修改）

    :param db_model: 数据库model
    :param form: 表单
    :param template: 模版
    :param form2: 第二个表单，进行权限分离时需要用到
    :return: 渲染后的模版
    """

    # 获取参数已经生成编辑和新增路径
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()
    redirect_path_edit = ('main.' + template.split('.')[0]).replace('edit', 'list')
    redirect_path_add = ('main.' + template.split('.')[0])

    # 修改操作（id存在）
    if id:
        # 如果是指定model，则记录操作前对应字段值
        if db_model == Business or db_model == TaskMonitor:
            try:
                status_old = db_model.select().where(db_model.id == id).get().status
            except:
                abort(500)
        if db_model == User:
            try:
                admin_old = db_model.select().where(db_model.id == id).get().admin
            except:
                abort(500)
        # 权限检查
        if not (bid in perm_list or perm_list == ['0']):
            abort(403)
        # 模型转表单
        model = db_model.get(db_model.id == id)
        if request.method == 'GET':
            utils.model_to_form(model, form)
        # 提交修改
        if request.method == 'POST':
            try:
                if form.validate_on_submit():
                    # 如果业务状态为禁用，则不允许操作
                    if db_model == TaskMonitor or db_model == BusinessNotifier:
                        biz_status = Business.select().join(db_model).where(Business.id == bid).get().status
                        if not biz_status:
                            flash('关联业务为禁用状态')
                            return redirect(url_for(redirect_path_edit))
                    # 如果是指定model，则记录表单提交前指定字段值
                    if db_model == Business or db_model == TaskMonitor:
                        status_new = form.status.data
                    if db_model == User:
                        admin_new = form.admin.data
                    # 提交数据
                    utils.form_to_model(form, model)
                    model.save()
                    # 如果业务状态从启用变为禁用，则对应的所有监控任务会被禁用
                    if db_model == Business:
                        if status_old != status_new and status_new is False:
                            toupdate = (TaskMonitor.update({TaskMonitor.status: False}).where(TaskMonitor.business == id))
                            toupdate.execute()
                    # 如果监控任务状态从启用变为禁用，则对应的告警状态会被重置
                    if db_model == TaskMonitor:
                        if status_old != status_new and status_new is False:
                            toupdate = (TaskMonitor.update({TaskMonitor.warning: False}).where(TaskMonitor.id == id))
                            toupdate.execute()
                    # 如果修改用户角色，则进行关联表相关操作
                    # 如果从业务管理员到系统管理员，则将perm_list修改为0
                    if db_model == User and admin_old != admin_new:
                        if admin_new is True:
                            toupdate = (Permission.update({Permission.perm_list: '0'}).where(Permission.perm_user == id))
                            toupdate.execute()
                    # 如果从系统管理员到业务管理员，则将perm_list修改为空值
                        else:
                            toupdate = (Permission.update({Permission.perm_list: ''}).where(Permission.perm_user == id))
                            toupdate.execute()
                    flash('修改成功')
                    return redirect(url_for(redirect_path_edit))
                else:
                    utils.flash_errors(form)
            except peewee.IntegrityError as e:
                flash(e)
    # 新增操作（id不存在）
    else:
        # 如果form2存在，则将form替换成form2，目前限于2种表单操作（业务联系人和任务表单）
        # 此类表单进行新增操作时，会进行‘status’是否为真的判断，在编辑操作时则不进行
        if form2:
            form = form2
        try:
            if form.validate_on_submit():
                model = db_model()
                utils.form_to_model(form, model)
                model.save()
                # 如果为用户model，则进行修改权限model操作，如果是超级管理员，则将perm_list更新为‘0’，否则保留默认值
                if db_model == User:
                    user_id = User.select().where(User.username == form.username.data).get().id
                    toadd = Permission()
                    toadd.perm_user = user_id
                    if form.admin.data:
                        toadd.perm_list = '0'
                    toadd.save()
                flash('保存成功')
                return redirect(url_for(redirect_path_add))
            else:
                utils.flash_errors(form)
        except peewee.IntegrityError as e:
            flash(e)

    return render_template(template, form=form, current_user=current_user)


def index_call(template):
    """首页模版渲染

    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 模版字典生成

    count_business = data_count(Business, perm_list)
    count_businessnotifier = data_count(BusinessNotifier, perm_list)
    count_taskmonitor = data_count(TaskMonitor, perm_list)
    count_taskmonitorlog = data_count(TaskMonitorLog, perm_list)

    # 年份日期列表生成（图表X轴数据）

    list_dt = []
    now = datetime.now()

    for i in range(0, 12):
        last_month = (now.month - i if now.month > i else now.month - i + 12)
        last_year = now.year if now.month > i else now.year - 1
        last_year_month = int(str(last_year) + str('%02d' % last_month))
        list_dt.append(last_year_month)

    list_dt.reverse()  # 使列表数据从倒序变为顺序

    # API请求列表生成（图表Y轴数据）

    # SQL查询语句和参数
    query = """
    select date_format(create_datetime, %s) month,count(id)
    from apirequestlog
    where date_format(create_datetime, %s) > date_format(date_sub(curdate(), interval 12 month), %s)
    and url like %s group by month
    """

    parm_tasks_all = ('%Y%m', '%Y%m', '%Y%m', '%tasks/all%')  # tasks/all API请求
    parm_tasks = ('%Y%m', '%Y%m', '%Y%m', '%tasks?%')  # tasks API请求

    # 根据SQL查询结果生成字典，年份日期为键，count结果为值
    dict_request_tasks_all = {}
    for i in DB.execute_sql(query, parm_tasks_all):
        dict_request_tasks_all[i[0]] = i[1]

    dict_request_tasks = {}
    for i in DB.execute_sql(query, parm_tasks):
        dict_request_tasks[i[0]] = i[1]

    # 根据年份日期列表和SQL查询结果字典生成最终API请求数据列表
    list_request_tasks_all = []
    list_request_tasks = []
    for i in list_dt:  # 如果年份日期（str(i)）在查询结果字典中有值，则在最终列表中使用此值，否则则赋值为0
        if str(i) in dict_request_tasks_all:
            list_request_tasks_all.append(dict_request_tasks_all[str(i)])
        else:
            list_request_tasks_all.append(0)
        if str(i) in dict_request_tasks:
            list_request_tasks.append(dict_request_tasks[str(i)])
        else:
            list_request_tasks.append(0)

    dict = {'business': count_business, 'businessnotifier': count_businessnotifier, 'taskmonitor': count_taskmonitor,
            'taskmonitorlog': count_taskmonitorlog, 'list_dt': list_dt,
            'list_request_tasks_all': list_request_tasks_all, 'list_request_tasks': list_request_tasks}

    return render_template(template, form=dict, current_user=current_user, current_time=datetime.utcnow())


def business_list(db_model, form, template):
    """业务列表模版渲染

    :param db_model: 数据库model
    :param form: 表单
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 表单校验（GET请求）
    form = get_form_validate(form)

    # 删除操作权限检查
    perm_check(action, id, bid, perm_list, db_model)

    # 查询语句拼接
    if search_content:
        query_all = query_string('where', 'db_model', search_by, search_content)
    else:
        query_all = query_string('orderby', 'db_model')

    # 模版字典生成（form2为查询表单）
    query, total_count = query_limit(eval(query_all), True, perm_list, page, length)
    item = "{'business_name': obj.business_name, 'id': obj.id, 'status': obj.status}"
    dict = {'content': list_gen(query, item), 'total_count': total_count,
            'search_by': search_by, 'search_content': search_content,
            'total_page': math.ceil(total_count / length), 'page': page, 'length': length}

    return render_template(template, form=dict, form2=form, current_user=current_user)


def notify_list(db_model, form, template):
    """通知人列表模版渲染

    :param db_model: 数据库model
    :param form: 表单
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 表单校验（GET请求）
    form = get_form_validate(form)

    # 删除操作权限检查
    perm_check(action, id, bid, perm_list, db_model)

    # 查询语句拼接
    if search_content:
        query_all = query_string('where', 'db_model', search_by, search_content)
    else:
        query_all = query_string('orderby', 'db_model')

    # 模版字典生成（form2为查询表单）
    query, total_count = query_limit(eval(query_all), False, perm_list, page, length)
    item = "{'id': obj.id, 'notify_name': obj.notify_name, 'notify_email': obj.notify_email, " \
           "'notify_tel': obj.notify_tel, 'status': obj.status}"
    dict = {'content': list_gen(query, item), 'total_count': total_count,
            'search_by': search_by, 'search_content': search_content,
            'total_page': math.ceil(total_count / length), 'page': page, 'length': length}

    return render_template(template, form=dict, form2=form, current_user=current_user)


def business_notifier_list(db_model, db_model2, form, template):
    """业务和通知人列表模版渲染

    :param db_model: 数据库model
    :param db_model2: 关联数据库model
    :param form: 表单
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 表单校验（GET请求）
    form = get_form_validate(form)

    # 删除操作权限检查
    perm_check(action, id, bid, perm_list, BusinessNotifier)

    # 查询语句拼接
    if search_by == 'business_name' and search_content:
        query_all = query_string('where', 'db_model', search_by, search_content,
                                 'db_model2', choice='first', many='BusinessNotifier')
    elif search_by == 'notify_name' and search_content:
        query_all = query_string('where', 'db_model', search_by, search_content,
                                 'db_model2', choice='second', many='BusinessNotifier')
    else:
        query_all = query_string('orderby', 'db_model', model2='db_model2', many='BusinessNotifier')

    # 模版字典生成（form2为查询表单）
    query, total_count = query_limit(eval(query_all), True, perm_list, page, length)
    item = "{'business_name': obj.business.business_name, 'id': obj.id, " \
           "'notify_name': obj.notifier.notify_name, 'bid': obj.business.id}"
    dict = {'content': list_gen(query, item), 'total_count': total_count,
            'search_by': search_by, 'search_content': search_content,
            'total_page': math.ceil(total_count / length), 'page': page, 'length': length}

    return render_template(template, form=dict, form2=form, current_user=current_user)


def task_list(db_model, db_model2, form, template):
    """任务列表模版渲染

    :param db_model: 数据库model
    :param db_model2: 关联数据库model
    :param form: 表单
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限以及监控URL公共部分
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()
    prefix = CFG.URL_ROOT

    # 表单校验（GET请求）
    form = get_form_validate(form)

    # 删除操作权限检查
    perm_check(action, id, bid, perm_list, db_model)

    # 查询语句拼接
    if search_content and search_by == 'business_name':
        query_all = query_string('where', 'db_model', search_by, search_content, 'db_model2', choice='second')
    elif search_content:
        query_all = query_string('where', 'db_model', search_by, search_content, 'db_model2')
    else:
        query_all = query_string('orderby', 'db_model', model2='db_model2')

    # 任务列表不采用按id排序，而是按照warning和status倒序排序，即处于告警的，禁用状态的任务在前
    query_all = query_all.replace('db_model.id', 'db_model.warning.desc(), db_model.status, db_model.id')

    # 模版字典生成（form2为查询表单）
    query, total_count = query_limit(eval(query_all), True, perm_list, page, length)
    item = "{'warning': obj.warning, 'name': obj.name, 'id': obj.id, 'url': obj.url, 'period': obj.period," \
           "'grace_time': obj.grace_time,'status': obj.status, " \
           "'business_name': obj.business.business_name, 'bid': obj.business.id}"
    dict = {'content': list_gen(query, item), 'total_count': total_count,
            'search_by': search_by, 'search_content': search_content,
            'total_page': math.ceil(total_count / length), 'page': page, 'length': length}

    return render_template(template, form=dict, form2=form, current_user=current_user, prefix=prefix)


def tasklog_list(db_model, template):
    """任务日志列表模版渲染

    :param db_model: 数据库model
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限以及监控URL公共部分
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 模版字典生成（join 'Business' model是因为query_limit函数需要使用Business.id）
    query_all = 'db_model.select().join(TaskMonitor, on=(TaskMonitorLog.taskmon_id == TaskMonitor.id))' \
                '.join(Business, on=(TaskMonitor.business == Business.id))' \
                '.where(TaskMonitor.id==id).order_by(db_model.id.desc()).limit(1000)'
    query, total_count = query_limit(eval(query_all), True, perm_list, page, length)
    item = "{'id': obj.id, 'client_ip': obj.client_ip, 'user_agent': obj.user_agent, " \
           "'create_datetime': obj.create_datetime}"
    dict = {'content': list_gen(query, item), 'total_count': total_count, 'task_id': id, 'bid': bid,
            'total_page': math.ceil(total_count / length), 'page': page, 'length': length}

    return render_template(template, form=dict, current_user=current_user)


def perm_list(db_model, db_model2, form, template):
    """权限列表模版渲染

    :param db_model: 数据库model
    :param db_model2: 关联数据库model
    :param form: 模版
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限以及监控URL公共部分
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 表单校验（GET请求）
    form = get_form_validate(form)

    # 删除操作权限检查
    perm_check(action, id, bid, perm_list, db_model2)

    # 查询语句拼接
    if search_content:
        query_all = query_string('where', 'db_model', search_by, search_content, 'db_model2', choice='second')
    else:
        query_all = query_string('orderby', 'db_model')

    # 模版字典生成（form2为查询表单）
    query, total_count = query_limit(eval(query_all), False, perm_list, page, length)
    item = "{'uid': obj.perm_user.id, 'id': obj.id, 'username': obj.perm_user.username, 'perm_list': obj.perm_list, " \
           "'email': obj.perm_user.email, 'phone': obj.perm_user.phone, 'status': obj.perm_user.status, " \
           "'api_username': obj.perm_user.api_username, 'api_password': obj.perm_user.api_password, " \
           "'admin': obj.perm_user.admin}"
    dict = {'content': list_gen(query, item), 'total_count': total_count,
            'search_by': search_by, 'search_content': search_content,
            'total_page': math.ceil(total_count / length), 'page': page, 'length': length}

    return render_template(template, form=dict, form2=form, current_user=current_user)


def perm_biz_edit(db_model, form, template):
    """业务权限编辑模版渲染

    :param db_model: 数据库model
    :param form: 模版
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限以及监控URL公共部分
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()
    uid = request.args.get('uid')

    # 模型转表单
    try:
        # 根据uid获取对应的业务权限
        perm_list_now = db_model.select().where(db_model.perm_user == uid).get().perm_list.split()
        form = form(business=perm_list_now)
    except:
        abort(500)

    # 修改记录
    if id:
        # 检查是否存在对应id的记录
        try:
            db_model.get(db_model.id == id)
        except:
            abort(500)
        # 提交操作
        if request.method == 'POST':
            if form.validate_on_submit():
                perm_list_new = ' '.join([str(i) for i in form.business.data])
                query = (db_model.update({db_model.perm_list: perm_list_new}).where(db_model.perm_user == uid))
                query.execute()
                flash('修改成功')
            else:
                utils.flash_errors(form)
    else:
        abort(403)

    return render_template(template, form=form, current_user=current_user)


def password_reset(db_model, form, template):
    """密码重置模版渲染

    :param db_model: 数据库model
    :param form: 模版
    :param template: 模版
    :return: 渲染后的模版
    """

    # 获取请求参数和用户权限以及监控URL公共部分
    action, id, bid, page, length, search_content, search_by, perm_list = get_parm()

    # 修改记录
    if id:
        # 查询
        model = db_model.get(db_model.id == id)
        if request.method == 'GET':
            utils.model_to_form(model, form)
        # 提交操作
        if request.method == 'POST':
            if form.validate_on_submit():
                new_password_hash = generate_password_hash(form.new_password.data)
                query = (db_model.update({db_model.password: new_password_hash}).where(db_model.id == id))
                query.execute()
                flash('密码重置成功')
                return redirect(url_for('main.permlist'))
            else:
                utils.flash_errors(form)
    else:
        abort(403)

    return render_template(template, form=form, current_user=current_user)


def password_change(db_model, form, template):
    """密码修改模版渲染

    :param db_model: 数据库model
    :param form: 模版
    :param template: 模版
    :return: 渲染后的模版
    """

    # 修改记录
    id = current_user.id
    if id:
        # 查询
        model = db_model.get(db_model.id == id)
        if request.method == 'GET':
            utils.model_to_form(model, form)
        # 提交操作
        if request.method == 'POST':
            if form.validate_on_submit():
                user = User.get(User.username == form.username.data)
                if user.verify_password(form.old_password.data):
                    new_password_hash = generate_password_hash(form.new_password.data)
                    query = (db_model.update({db_model.password: new_password_hash}).where(db_model.id == id))
                    query.execute()
                    flash('密码修改成功')
                else:
                    flash('原密码不对')
            else:
                utils.flash_errors(form)
    else:
        abort(403)

    return render_template(template, form=form, current_user=current_user)


@main.route('/', methods=['GET'])
def root():
    """根目录路由函数（跳转至index）"""
    return redirect(url_for('main.index'))


@main.route('/index', methods=['GET'])
@login_required
def index():
    """首页路由函数"""
    return index_call('index.html')


@main.route('/businesslist', methods=['GET', 'POST'])
@login_required
@admin_required
def businesslist():
    """业务列表路由函数（仅限超级管理员访问）"""
    return business_list(Business, BusinessSearchForm, 'businesslist.html')


@main.route('/businessedit', methods=['GET', 'POST'])
@login_required
@admin_required
def businessedit():
    """业务编辑路由函数（仅限超级管理员访问）"""
    return form_edit(Business, BusinessForm(), 'businessedit.html')


@main.route('/notifylist', methods=['GET', 'POST'])
@login_required
def notifylist():
    """联系人列表路由函数"""
    return notify_list(Notifier, NotifierSearchForm, 'notifylist.html')


@main.route('/notifyedit', methods=['GET', 'POST'])
@login_required
@admin_required
def notifyedit():
    """通知人编辑路由函数（仅限超级管理员访问）"""
    return form_edit(Notifier, NotifierForm(), 'notifyedit.html')


@main.route('/businessnotifierlist', methods=['GET', 'POST'])
@login_required
def businessnotifierlist():
    """业务和通知人列表路由函数"""
    return business_notifier_list(Business, Notifier, BusinessNotifierSearchForm, 'businessnotifierlist.html')


@main.route('/businessnotifieredit', methods=['GET', 'POST'])
@login_required
def businessnotifieredit():
    """业务和通知人编辑路由函数"""
    return form_edit(BusinessNotifier, BusinessNotifierForm(), 'businessnotifieredit.html', BusinessNotifierFormNew())


@main.route('/tasklist', methods=['GET', 'POST'])
@login_required
def tasklist():
    """任务列表路由函数"""
    return task_list(TaskMonitor, Business, TaskSearchForm, 'tasklist.html')


@main.route('/taskedit', methods=['GET', 'POST'])
@login_required
def taskedit():
    """任务编辑路由函数"""
    return form_edit(TaskMonitor, TaskForm(), 'taskedit.html', TaskFormNew())


@main.route('/taskloglist', methods=['GET', 'POST'])
@login_required
def taskloglist():
    """任务日志列表路由函数"""
    return tasklog_list(TaskMonitorLog, 'taskloglist.html')


@main.route('/permlist', methods=['GET', 'POST'])
@login_required
@admin_required
def permlist():
    """用户权限列表路由函数（仅限超级管理员访问）"""
    return perm_list(Permission, User, PermissionSearchForm, 'permlist.html')


@main.route('/permedit', methods=['GET', 'POST'])
@login_required
@admin_required
def permedit():
    """用户权限编辑路由函数（仅限超级管理员访问）"""
    return form_edit(User, PermissionForm(), 'permedit.html')


@main.route('/permbizedit', methods=['GET', 'POST'])
@login_required
@admin_required
def permbizedit():
    """业务权限编辑路由函数（仅限超级管理员访问）"""
    return perm_biz_edit(Permission, PermissionBizForm, 'permbizedit.html')


@main.route('/passwordreset', methods=['GET', 'POST'])
@login_required
@admin_required
def passwordreset():
    """密码重置路由函数（仅限超级管理员访问）"""
    return password_reset(User, ResetPasswordForm(), 'passwordreset.html')


@main.route('/passwordrchange', methods=['GET', 'POST'])
@login_required
def passwordchange():
    """密码修改路由函数"""
    return password_change(User, ChangePasswordForm(), 'passwordchange.html')
