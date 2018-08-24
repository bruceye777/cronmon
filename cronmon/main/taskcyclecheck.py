from datetime import datetime
import time
from crontab import CronTab
from peewee import fn
from cronmon.models import Business, TaskMonitor, TaskMonitorLog, BusinessNotifier, Notifier, User, Permission
from cronmon.email import send_email
from cronmon import get_logger


LOGGER = get_logger(__name__)


def taskcyclecheck():
    """根据任务上次检查时间、任务下次检查时间和当前时间，当任务告警状态发生变化时，通过邮件通知到对应业务的联系人"""

    # 获取当前时间（二种格式）
    current_timestamp = int(time.time())
    current_datetime = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    # 获取状态为启用的业务列表
    query1 = TaskMonitor.select().where(TaskMonitor.status == 1)

    # 列表生成
    infolist = []

    for obj in query1:
        id = obj.id
        period = obj.period
        grace_time = int(obj.grace_time) * 60
        last_check_time = obj.last_check_time
        next_check_time = obj.next_check_time
        create_datetime = obj.create_datetime
        warning = obj.warning

        # 任务上次检查时间（last_check_time）初始化（如果为空值，则以任务创建时间为值）
        if not last_check_time:
            query0 = TaskMonitor.update(last_check_time=create_datetime).where(TaskMonitor.id == id)
            query0.execute()

        # 任务下次检查时间（next_check_time init）初始化（如果为空值，则以计算出的next_check_datetime为值）
        entry = CronTab(period)
        add = int(entry.next(default_utc=False))
        next_check_timestamp = current_timestamp + add + grace_time
        next_check_datetime = datetime.fromtimestamp(next_check_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        if not next_check_time:
            query1 = TaskMonitor.update(next_check_time=next_check_datetime).where(TaskMonitor.id == id)
            query1.execute()

        # 获取目前last_check_time值和next_check_time值
        last_check_datetime2 = TaskMonitor.select().where(TaskMonitor.id == id).get().last_check_time
        next_check_datetime2 = TaskMonitor.select().where(TaskMonitor.id == id).get().next_check_time

        # 获取通知人列表
        query3 = TaskMonitor.select().where(TaskMonitor.id == id).get().business.business_name
        query4 = BusinessNotifier.select().join(Business).\
            switch(BusinessNotifier).join(Notifier).where(Business.business_name == query3)

        # 如果当前时间大于下次检查时间且不处于告警状态或者处于告警状态
        if (str(current_datetime) >= str(next_check_datetime2) and not warning) or warning:
            try:
                # 查找TaskMonitorLog的记录，如果有大于上次检查时间的记录存在，则将其赋值给last_check_time_new
                last_check_time_new = TaskMonitorLog.select()\
                    .where(TaskMonitorLog.taskmon_id == id, TaskMonitorLog.create_datetime > last_check_datetime2)\
                    .order_by(TaskMonitorLog.id.desc()).get().create_datetime
                # 如果之前warning值为True，则将其更改为False，生成邮件相关信息，同时写入数据库和日志
                if warning:
                    for item in query4:
                        sublist = []
                        if item.notifier.status:
                            subject = 'Status is Up'
                            sublist.append(item.notifier.notify_email)
                            sublist.append(obj.name)
                            sublist.append(subject)
                            infolist.append(sublist)
                warning = False
                query2 = TaskMonitor\
                    .update(warning=warning, last_check_time=last_check_time_new, next_check_time=next_check_datetime)\
                    .where(TaskMonitor.id == id)
                query2.execute()
                msg = 'TASK ' + obj.name + ' : OK'
                LOGGER.warn(msg)
            except:
                # 如果TaskMonitorLog的记录没有大于上次检查时间的记录存在且之前warning值为False，则将其更改为True，生成邮件相关信息，
                # 同时写入数据库和日志
                if not warning:
                    for item in query4:
                        sublist = []
                        if item.notifier.status:
                            subject = 'Status is Down'
                            sublist.append(item.notifier.notify_email)
                            sublist.append(obj.name)
                            sublist.append(subject)
                            infolist.append(sublist)
                warning = True
                query2 = TaskMonitor.update(warning=warning).where(TaskMonitor.id == id)
                query2.execute()
                msg = 'TASK ' + obj.name + ' : NOT OK'
                LOGGER.error(msg)
    # 发送邮件
    send_email(infolist)


def emptybusinesscheck():
    """获取没有联系人的业务，并同时发给系统管理员和对应的业务管理员"""

    # 获取空联系人业务信息，如果结果为空，则退出后续检查
    subq = BusinessNotifier.select().where(BusinessNotifier.business_id == Business.id)
    query1 = Business.select().where((~fn.EXISTS(subq)) & (Business.status == True))
    if not query1:
        return

    # 获取管理员列表
    query2 = User.select().where((User.admin == True) & (User.status == True))

    # 列表生成（系统管理员）
    # stridlist用作和perm_list进行交叉比对
    stridlist = []
    strlist = []
    infolist = []

    subject = 'Empty Business - SystemAdmin'

    for i in query1:
        biz = str(i.id) + ' : ' + i.business_name
        strlist.append(biz)
        bizid = str(i.id)
        stridlist.append(bizid)
    mailstring = "\n".join(strlist)

    for item in query2:
        subinfolist = []
        notifier = item.email
        subinfolist.append(notifier)
        subinfolist.append(mailstring)
        subinfolist.append(subject)
        infolist.append(subinfolist)

    # 发送告警信息给系统管理员
    send_email(infolist)

    # 列表生成（业务管理员）
    strlist = []
    infolist = []

    subject = 'Empty Business - BizAdmin'

    user_perm_list = Permission.select().join(User)\
        .where((Permission.perm_list != '0') & (Permission.perm_list != '') & (User.status == 1))
    for item in user_perm_list:
        user_perm_list_item = item.perm_list.split()
        # perm_list和无联系人业务id列表进行交叉比对
        business_intersection = [x for x in user_perm_list_item if x in set(stridlist)]
        if business_intersection:
            subinfolist = []
            notifier = item.perm_user.email
            subinfolist.append(notifier)
            # 根据id获取业务名称作为邮件正文
            for perm_item in business_intersection:
                biz = Business.select().where(Business.id == perm_item).get().business_name
                strlist.append(biz)
            mailstring = "\n".join(strlist)
            subinfolist.append(mailstring)
            subinfolist.append(subject)
            infolist.append(subinfolist)

    # 发送告警信息给业务管理员
    send_email(infolist)
