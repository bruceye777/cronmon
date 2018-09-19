import os


class Config:
    """公共配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'  # 密钥
    DB_HOST = '127.0.0.1'  # 数据库地址
    DB_USER = 'cronmon_user'  # 数据库用户名
    DB_PASSWD = 'cronmon_pwd'  # 数据库密码
    DB_DATABASE = 'cronmon'  # 数据库名
    ITEMS_PER_PAGE = 10  # 每页显示记录数
    URL_ROOT = 'http://cronmon.yoursite.io/api/monlink/'  # 监控URL公共部分
    VALIDATE_CODE_USE = False  # 登陆时是否开启验证码
    SESSION_COOKIE_SECURE = False  # session cookie是否仅通过HTTPS发送
    REMEMBER_COOKIE_SECURE = False  # remember cookie是否仅通过HTTPS发送
    SESSION_COOKIE_HTTPONLY = True  # 是否允许JavaScrip读取session cookie
    REMEMBER_COOKIE_HTTPONLY = True  # 是否允许JavaScript读取remember cookie
    MAIL_SERVER = 'smtp.yoursite.io'  # 邮件SMTP服务器
    MAIL_PORT = 465  # 邮件服务器端口
    MAIL_USE_SSL = True  # 邮件服务器是否使用SSL
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # 邮件服务器登录用户名
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # 邮件服务器登录密码
    MAIL_MAX_EMAILS = 5  # 一次连接中发送的最大邮件数
    MAIL_DEFAULT_SENDER = 'CRONMON <sendmail@yoursite.io>'  # 发件人显示名称和地址
    # 后台循环任务，job1为crontab监控检查任务，job2为空业务检查任务
    JOBS = [
        {
            'id': 'job1',
            'func': 'cronmon.main.taskcyclecheck:taskcyclecheck',
            'trigger': 'interval',
            'seconds': 60
        },
        {
            'id': 'job2',
            'func': 'cronmon.main.taskcyclecheck:emptybusinesscheck',
            'trigger': 'interval',
            'seconds': 3600
        }
    ]

    @staticmethod
    def init_app(app):
        """配置初始化任务"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class TestingConfig(Config):
    """测试环境配置"""
    MAIL_SUPPRESS_SEND = True
    TESTING = True


class ProductionConfig(Config):
    """生产环境配置"""
    PRODUCTION = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
