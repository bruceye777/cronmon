import os
import random
import string
import uuid
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import URLSafeSerializer
from peewee import __exception_wrapper__
from playhouse.migrate import MySQLDatabase, MySQLMigrator, Model, CharField, DateTimeField, IntegerField, \
    BooleanField, ForeignKeyField, OperationalError
from werkzeug.security import check_password_hash, generate_password_hash
from cronmon import login_manager
from cronmon.conf.config import config


class RetryOperationalError(object):
    """数据库空闲连接重试"""
    def execute_sql(self, sql, params=None, commit=True):
        """执行超类的execute_sql函数，如果发生错误，如果连接打开则关闭连接，最后重新执行一次sql"""
        try:
            cursor = super(RetryOperationalError, self).execute_sql(sql, params, commit)
        except OperationalError:
            if not self.is_closed():
                self.close()
            with __exception_wrapper__:
                cursor = self.cursor(commit)
                cursor.execute(sql, params or ())
                if commit and not self.in_transaction():
                    self.commit()
        return cursor


class RetryDB(RetryOperationalError, MySQLDatabase):
    """封装数据库重试类"""
    pass


CFG = config[os.getenv('FLASK_CONFIG') or 'default']
DB = RetryDB(host=CFG.DB_HOST, user=CFG.DB_USER, passwd=CFG.DB_PASSWD, database=CFG.DB_DATABASE)
MIGRATOR = MySQLMigrator(DB)
SERIALIZER = URLSafeSerializer(CFG.SECRET_KEY)


def session_token_generate():
    """随机session token生成"""
    return SERIALIZER.dumps(str(uuid.uuid1()))


class BaseModel(Model):
    """基类初始化"""
    class Meta:
        """数据库初始化"""
        database = DB


class User(UserMixin, BaseModel):
    """用户model"""
    username = CharField(unique=True)  # 用户名
    password = CharField()  # 密码
    email = CharField(unique=True)  # 邮箱
    phone = CharField(unique=True)  # 电话
    status = BooleanField(default=True)  # 是否启用状态
    admin = BooleanField(default=False)  # 是否超级管理员
    api_username = CharField(unique=True, null=True)  # API用户名
    api_password = CharField(null=True)  # API密码
    create_datetime = DateTimeField(default=datetime.now)  # 创建时间
    session_token = CharField(unique=True, default=session_token_generate)  # 随机session token

    @property
    def password_hash(self):
        """'password'不可读"""
        raise AttributeError('密码为只读属性')

    @password_hash.setter
    def password_hash(self, raw_password):
        """输出密码散列值"""
        self.password = generate_password_hash(raw_password)

    def verify_password(self, raw_password):
        """检查登录密码是否正确"""
        return check_password_hash(self.password, raw_password)

    def verify_api_password(self, api_password):
        """检查api密码是否正确"""
        return bool(self.api_password == api_password)

    @staticmethod
    def generate_init_password():
        """生成用户初始化密码"""
        raw_password = ''.join(random.sample(string.ascii_letters + string.digits, 10))
        return raw_password

    def is_admin(self):
        """检查用户是否超级管理员"""
        return self.admin

    def is_active(self):
        """检查用户是否启用状态"""
        return self.status

    def is_anonymous(self):
        """对是否匿名返回‘False’"""
        return False

    def get_id(self):
        return self.session_token


class Permission(BaseModel):
    """权限model"""
    perm_list = CharField(default='')  # 权限列表
    perm_user = ForeignKeyField(User, related_name='perm')  # 所属user
    create_datetime = DateTimeField(default=datetime.now)  # 创建时间


class Notifier(BaseModel):
    """通知人model"""
    notify_name = CharField(unique=True)  # 通知人姓名
    notify_email = CharField(unique=True)  # 邮件地址
    notify_tel = CharField(unique=True)  # 电话号码
    status = BooleanField(default=True)  # 生效失效标识
    create_datetime = DateTimeField(default=datetime.now)  # 创建时间


class Business(BaseModel):
    """业务model"""
    business_name = CharField(unique=True)  # 业务名
    status = BooleanField(default=True)  # 生效失效标识
    create_datetime = DateTimeField(default=datetime.now)  # 创建时间


class BusinessNotifier(BaseModel):
    """业务和通知人model"""
    business = ForeignKeyField(Business)
    notifier = ForeignKeyField(Notifier)
    create_datetime = DateTimeField(default=datetime.now)  # 创建时间

    class Meta:
        """设置唯一性复合索引"""
        indexes = (
            (('business', 'notifier'), True),
        )


class TaskMonitor(BaseModel):
    """任务model"""
    name = CharField(unique=True)  # 监控任务名
    url = CharField(unique=True)  # 监控URL
    period = CharField()  # 循环周期
    grace_time = IntegerField(default=0)  # 超时时间，以分钟为单位
    status = BooleanField(default=True)  # 生效失效标识
    last_check_time = DateTimeField(null=True)  # 上次任务检查时间
    next_check_time = DateTimeField(null=True)  # 下次任务检查时间
    warning = BooleanField(default=False)  # 是否处于告警状态
    create_datetime = DateTimeField(default=datetime.now)  # 创建时间
    business = ForeignKeyField(Business, related_name='biz')  # 所属业务

    @staticmethod
    def gen_uuid():
        """生成监控任务唯一ID"""
        cronid = str(uuid.uuid1())
        return cronid


class TaskMonitorLog(BaseModel):
    """任务日志model"""
    create_datetime = DateTimeField(default=datetime.now)  # 请求发生时间
    client_ip = CharField()  # 客户端ip
    user_agent = CharField()  # 客户端类型
    taskmon_id = IntegerField()  # 关联监控任务（此处未使用外键，考虑到插入速度和mysql分区）


class ApiRequestLog(BaseModel):
    """接口请求日志model"""
    create_datetime = DateTimeField(default=datetime.now)  # 请求发生时间
    client_ip = CharField()  # 客户端ip
    user_agent = CharField()  # 客户端类型
    url = CharField()  # 请求URL
    method = CharField()  # 请求方法
    code = IntegerField()  # 响应代码
    user_id = IntegerField()  # 关联监控任务（此处未使用外键，考虑到插入速度和mysql分区）


class AnonymousUser(AnonymousUserMixin):
    """匿名用户处理"""
    def is_admin(self):
        """对是否管理员返回‘False’"""
        return False

    def is_anonymous(self):
        """对是否匿名返回‘True’"""
        return True


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(session_token):
    """用户回调"""
    try:
        user = User.get(User.session_token == session_token)
        return user
    except:
        return None


if __name__ == '__main__':
    pass
