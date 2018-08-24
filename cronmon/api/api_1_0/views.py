import math
from flask import request, g, url_for, jsonify
from cronmon import get_logger, get_config
from cronmon.api.errors import bad_request
from cronmon.models import TaskMonitor, Permission, Business, ApiRequestLog
from cronmon.utils import list_gen
from cronmon.exceptions import ValidationError
from . import api_1_0

LOGGER = get_logger(__name__)
CFG = get_config()


@api_1_0.after_request
def after_request(response):
    """请求之后，记录日志，根据需要选择记录输出到文件或数据库"""
    try:
        user_id = g.current_user.id
    except:
        return response

    client_ip = str(request.remote_addr)
    user_agent = request.user_agent.string
    url = request.url.replace(request.url_root, '/')
    method = request.method
    code = str(response.status_code)

    # 如果需要记录到日志文件，可以取消注释LOGGER
    # msg = ' - '.join((client_ip, method, url, code, user_agent, user_id))
    # LOGGER.info(msg)

    toadd = ApiRequestLog()
    toadd.client_ip = client_ip
    toadd.user_agent = user_agent
    toadd.url = url
    toadd.method = method
    toadd.code = code
    toadd.user_id = user_id
    toadd.save()

    return response


@api_1_0.route('/tasks/all', methods=['GET'])
def tasks_all():
    """获取全部监控任务请求接口

    请求参数包括page（页码）和length（每页显示记录数），根据api用户对应业务权限进行过滤

    :return: json格式输出，包括tasks（任务信息）、prev（上页url）、next（下页url）和count（记录数）
    """

    page = int(request.args.get('page')) if request.args.get('page') else 1
    length = int(request.args.get('length')) if request.args.get('length') else CFG.ITEMS_PER_PAGE
    perm_list = Permission.select().where(Permission.perm_user == g.current_user.id).get().perm_list.split()

    if perm_list == ['0']:
        query = TaskMonitor.select().order_by(TaskMonitor.id)
    else:
        query = TaskMonitor.select().join(Business).where(Business.id.in_(perm_list)).order_by(TaskMonitor.id)

    # 对page、length和返回记录数进行有效性检查
    total_count = query.count()

    if total_count == 0:
        return bad_request("No Records")

    if length < 1:
        return bad_request("Out of Range")

    total_page = math.ceil(total_count / length)

    if page < 1 or page > total_page:
        return bad_request("Out of Range")

    # 分页处理，如果prev和next无对应的有效值存在，则赋值‘None’
    prev = None
    if page != 1:
        prev = url_for("api_1_0.tasks_all", page=page-1, length=length, _external=True)

    next = None
    if page < total_page:
        next = url_for("api_1_0.tasks_all", page=page+1, length=length, _external=True)

    if page:
        query = query.paginate(page, length)

    item = "{'name': obj.name, 'url': obj.url, 'period': obj.period, 'grace_time': obj.grace_time," \
           "'status': obj.status, 'warning': obj.warning, 'business_name': obj.business.business_name}"

    return jsonify({
        'tasks': list_gen(query, item),
        'prev': prev,
        'next': next,
        'count': total_count
    })


@api_1_0.route('/tasks', methods=['GET'])
def tasks_filter():
    """根据请求参数获取监控任务请求接口

    请求参数包括bizname（业务名）、url（监控url uuid部分）和taskname（任务名），根据api用户对应业务权限进行过滤，并对参数进行有效性检查

    :return: json格式输出，包括tasks（任务信息）
    """

    bizname = request.args.get('bizname')
    url = request.args.get('url')
    taskname = request.args.get('taskname')
    perm_list = Permission.select().where(Permission.perm_user == g.current_user.id).get().perm_list.split()

    # 对参数名称、参数个数和返回记录数进行有效性检查
    if len(request.args) > 1 or len(request.args) == 0:
        return bad_request("Only One Keyword Allowed")
    elif bizname:
        query = TaskMonitor.select().join(Business)\
            .where(((perm_list == ['0']) & (Business.business_name == bizname)) |
                   ((Business.id.in_(perm_list)) & (Business.business_name == bizname)))
    elif url:
        query = TaskMonitor.select().join(Business).where(((perm_list == ['0']) & (TaskMonitor.url == url)) |
                                                          ((Business.id.in_(perm_list)) & (TaskMonitor.url == url)))
    elif taskname:
        query = TaskMonitor.select().join(Business)\
            .where(((perm_list == ['0']) & (TaskMonitor.name == taskname)) |
                   ((Business.id.in_(perm_list)) & (TaskMonitor.name == taskname)))
    else:
        return bad_request("Keyword Doesn't Exist")

    if query.count() == 0:
        return bad_request("No Records")

    item = "{'warning': obj.warning, 'name': obj.name, 'id': obj.id, 'url': obj.url, 'period': obj.period," \
           "'grace_time': obj.grace_time,'status': obj.status, 'business_name': obj.business.business_name, " \
           "'bid': obj.business.id}"

    return jsonify({
        'tasks': list_gen(query, item)
    })


@api_1_0.errorhandler(ValidationError)
def validation_error(e):
    """ValidationError处理"""
    return bad_request(e.args[0])
