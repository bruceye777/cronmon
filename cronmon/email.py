import os
from flask_mail import Message
from cronmon import get_logger
from . import mail
from . import create_app


LOGGER = get_logger(__name__)


def send_email(infolist):
    """发送邮件

    :param infolist: 一个由列表组成的列表，每个子列表包含收件人，正文和主体三部分信息
    :return: 无
    """
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app_ctx = app.app_context()
    app_ctx.push()
    with mail.connect() as conn:
        with app.app_context():
            for info in infolist:
                msg = Message(subject=info[2], body=info[1], recipients=[info[0]])
                conn.send(msg)
                msg = 'Send mail to ' + info[0] + ': ' + info[2] + ' --- ' + info[1]
                LOGGER.warn(msg)
