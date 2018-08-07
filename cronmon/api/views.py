from flask import request
from cronmon.models import TaskMonitor, TaskMonitorLog
from cronmon.api.errors import bad_request
from cronmon.exceptions import ValidationError
from . import api


@api.route('/api/monlink/<cronuuid>')
def monlink(cronuuid):
    """监控url请求接口

    :param cronuuid: 监控url（uuid部分）
    :return: 如果存在此uuid，则返回‘OK’，反之则返回‘BAD REQUEST’
    """
    try:
        mon_id = TaskMonitor.select().where(TaskMonitor.url == cronuuid).get().id

        client_ip = str(request.remote_addr)
        user_agent = request.user_agent.string
        toadd = TaskMonitorLog()
        toadd.taskmon_id = mon_id
        toadd.client_ip = client_ip
        toadd.user_agent = user_agent
        toadd.save()
        return 'OK'
    except:
        return bad_request("Wrong Id")


@api.errorhandler(ValidationError)
def validation_error(e):
    """ValidationError处理"""
    return bad_request(e.args[0])
