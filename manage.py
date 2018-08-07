import os
from flask_script import Manager, Server
from cronmon import create_app

# 创建app，初始化manager
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

# 添加‘runserver’命令，‘use_reloader’参数防止app被加载2次（会导致scheduler脚本邮件发送2次）
server = Server(host="0.0.0.0", port=5000, use_reloader=False)
manager.add_command("runserver", server)

if __name__ == '__main__':
    manager.run()
