import os
from cronmon import create_app, scheduler

# 创建app
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# scheduler初始化和启动
scheduler.init_app(app)
scheduler.start()

# 判断是否运行在uwsgi模式下，然后阻塞mule等待uwsgi信号
try:
    import uwsgi
    while True:
        sig = uwsgi.signal_wait()
        print(sig)
except Exception as err:
    pass
