import os
from playhouse.migrate import migrate, CharField, BooleanField, ForeignKeyField
from flask_script import Manager
from werkzeug.security import generate_password_hash
from cronmon import create_app
from cronmon.models import User, Permission, Notifier, Business, BusinessNotifier, TaskMonitor, TaskMonitorLog,\
    ApiRequestLog, BaseModel, DB, MIGRATOR


# 创建app，初始化manager
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


def create_table():
    """初始化数据库表结构，包括所有model，后续调整使用migrate.py"""
    DB.create_tables([User, Permission, Notifier, Business, BusinessNotifier, TaskMonitor, TaskMonitorLog,
                      ApiRequestLog])


def drop_table():
    """初始化数据库表结构，包括所有model，后续调整使用migrate.py"""
    DB.drop_tables([User, Permission, Notifier, Business, BusinessNotifier, TaskMonitor, TaskMonitorLog, ApiRequestLog])


def insert_first_admin():
    """插入系统初始管理员帐号，相关用户属性可后续自行更改"""
    first_admin = User()
    first_admin.username = 'cronadmin'
    first_admin.password_hash = 'cronadmin'
    first_admin.email = 'super@cronmon.com'
    first_admin.phone = '13912345678'
    first_admin.status = True
    first_admin.admin = True
    first_admin.api_username = 'api_cronadmin'
    first_admin.api_password = 'api_cronadmin'
    first_admin.save()

    first_admin_perm = Permission()
    first_admin_perm.perm_list = '0'
    first_admin_perm.perm_user = 1
    first_admin_perm.save()


@manager.command
def init():
    """系统初始化，创建所有表，插入初始超级管理员帐号"""
    create_table()
    insert_first_admin()


@manager.command
def reinit():
    """系统重新初始化，删除所有初始化表，然后完成初始化工作"""
    confirm = input('此操作会删除所有现有数据，确定（y/n）？')
    if str(confirm).lower() == 'y':
        print('开始操作')
        drop_table()
        create_table()
        insert_first_admin()
    else:
        print('终止操作')


# 业务表样例数据
business_fields = [Business.business_name, Business.status]
business_data = [
    ('全金属狂潮', False),
    ('龙行天下', True),
    ('PEOP', True),
    ('天上天下', True),
    ('无间道1', True),
    ('热血传奇3', True),
    ('业务2', True),
    ('游戏2', True),
    ('游戏1', True),
    ('业务1', False),
    ('业务3', True),
    ('游戏3', True)]

# 通知人表样例数据
notifier_fields = [Notifier.notify_name, Notifier.notify_email, Notifier.notify_tel, Notifier.status]
notifier_data = [
    ('王宁', '13822223366@139.com', '13764321006', True),
    ('文林', 'super@cronmon.com', '13812188886', False),
    ('湛鹏', 'cronabc@qq.com', '13962427283', True),
    ('钟强', 'sendmail@cronmon.com', '13812188822', True),
    ('毛云', 'sendmail2@cronmon.com', '13612188111', True),
    ('慕淑珍', 'sendmail3@cronmon.com', '13412128888', True),
    ('童颖', 'sendmail4@cronmon.com', '13512138888', True),
    ('范磊', 'sendmail5@cronmon.com', '13812148888', True),
    ('呼斌', 'sendmail6@cronmon.com', '13912158888', True),
    ('王小毛', 'op@cronmon.com', '13762453125', True),
    ('刘统勋', 'it@cronmon.com', '13812188880', False),
    ('和建军', 'sendmail7@cronmon.com', '13798764321', True)]

# 业务通知人表样例数据
businessnotifier_fields = [BusinessNotifier.business, BusinessNotifier.notifier]
businessnotifier_data = [
    (1, 2),
    (1, 10),
    (2, 1),
    (3, 5),
    (3, 11),
    (4, 1),
    (5, 1),
    (5, 8),
    (6, 4),
    (6, 9),
    (7, 1),
    (8, 10),
    (8, 9),
    (9, 3),
    (10, 7)]

# 任务表样例数据
taskmonitor_fields = [TaskMonitor.name, TaskMonitor.url, TaskMonitor.period, TaskMonitor.grace_time,
                      TaskMonitor.status, TaskMonitor.last_check_time, TaskMonitor.next_check_time,
                      TaskMonitor.warning, TaskMonitor.business]
taskmonitor_data = [('secondTask', TaskMonitor.gen_uuid(), '3 15 * * *', 6, True, None, None, True, 3),
                    ('thirdTask', TaskMonitor.gen_uuid(), '30 8 * * 1,3', 360, False, None, None, False, 1),
                    ('mysqlPartition', TaskMonitor.gen_uuid(), '15 2 * * *', 10, True, None, None, True, 4),
                    ('cmBackup', TaskMonitor.gen_uuid(), '*/30 * * * *', 3, True, None, None, False, 2),
                    ('gameService1', TaskMonitor.gen_uuid(), '*/5 * * * *', 1, True, None, None, False, 1),
                    ('firstTask', TaskMonitor.gen_uuid(), '* * * * *', 1, True, None, None, True, 5),
                    ('errorCheck', TaskMonitor.gen_uuid(), '* * * * *', 2, False, None, None, False, 10),
                    ('real1', TaskMonitor.gen_uuid(), '*/15 * * * *', 1, False, None, None, False, 10),
                    ('mainService1', TaskMonitor.gen_uuid(), '* */2 * * *', 5, True, None, None, False, 7),
                    ('webRsync', TaskMonitor.gen_uuid(), '45 2 * * *', 10, True, None, None, True, 6),
                    ('remoteBackup', TaskMonitor.gen_uuid(), '25 4 * * *', 60, True, None, None, True, 8),
                    ('clearCache', TaskMonitor.gen_uuid(), '* */3 * * *', 10, True, None, None, False, 9),
                    ('checkResource', TaskMonitor.gen_uuid(), '25 5 * * *', 5, False, None, None, False, 5)]

# 用户表样例数据
user_fields = [User.username, User.password, User.email, User.phone, User.status, User.admin, User.api_username,
               User.api_password]
user_data = [
    ('bizadmin1', generate_password_hash('bizadmin1'), 'cronabc@qq.com', '18727897662', True, False, 'api_root',
     'api_passwd'),
    ('bizadmin2', generate_password_hash('bizadmin2'), 'sendmail@qq.com', '13725432345', True, False, 'api_bizadmin2',
     'api_bizadmin2'),
    ('bizadmin3', generate_password_hash('bizadmin3'), 'sendmail2@qq.com', '13765432345', False, False, 'api_bizadmin3',
     'api_bizadmin3_pwd'),
    ('cronadmin2', generate_password_hash('cronadmin2'), '13822223366@139.com', '13812689754', True, True, 'api_root2',
     'api_pwd2')]

# 权限表样例数据
permission_fields = [Permission.perm_list, Permission.perm_user]
permission_data = [
    ('1 3', 2),
    ('1 3 4 6', 3),
    ('9 12', 4),
    ('0', 5)]


@manager.command
def sample():
    """插入样例数据"""
    Business.insert_many(business_data, fields=business_fields).execute()
    Notifier.insert_many(notifier_data, fields=notifier_fields).execute()
    BusinessNotifier.insert_many(businessnotifier_data, fields=businessnotifier_fields).execute()
    TaskMonitor.insert_many(taskmonitor_data, fields=taskmonitor_fields).execute()
    User.insert_many(user_data, fields=user_fields).execute()
    Permission.insert_many(permission_data, fields=permission_fields).execute()


# model定义
class BusinessNew(BaseModel):
    """业务model"""
    business_name = CharField(unique=True)  # 业务名
    status = BooleanField(default=True)  # 生效失效标识


@manager.command
def create():
    """新建表（注意在此处创建的新表需要复制model定义到models.py）"""
    DB.create_tables([BusinessNew])


# 字段类型定义
status_field = BooleanField(default=False)
notifier_id_field = ForeignKeyField(Notifier, to_field=Notifier.id, default=1, null=True)


@manager.command
def update():
    """修改表（注意在此处所做变要同步相关model定义到models.py）"""
    with DB.transaction():  # 使‘migrate’运行在事务中
        migrate(
            MIGRATOR.add_column('business', 'status999', status_field),  # 增加列
            MIGRATOR.add_column('business', 'status', status_field),  # 增加列
            MIGRATOR.add_column('businessnotifier', 'notifier_id', notifier_id_field),  # 增加外键列
            MIGRATOR.drop_column('business', 'status'),  # 删除列
            MIGRATOR.rename_column('business', 'status', 'status_mod'),  # 重命名列
            MIGRATOR.drop_not_null('permission', 'perm_list'),  # 允许为空
            MIGRATOR.add_not_null('permission', 'perm_list'),  # 不允许为空
            MIGRATOR.rename_table('perm', 'permission'),  # 重命名表
            MIGRATOR.add_index('user', ('username',), True),  # 增加唯一性单一索引
            MIGRATOR.add_index('user', ('username', 'email'), True),  # 增加唯一性复合索引
            MIGRATOR.drop_index('user', 'username'),  # 删除索引
        )


if __name__ == '__main__':
    manager.run()
