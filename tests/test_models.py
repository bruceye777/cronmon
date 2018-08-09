"""各个用户模型测试，包括默认值、空值，类型的测试
此文件测试用例依赖于初始化脚本中的样本数据，如果数据有过更改，则有可能会导致测试失败
"""
from datetime import datetime
import pytest
import pymysql
from werkzeug.security import generate_password_hash
from cronmon.models import Business, Notifier, BusinessNotifier, TaskMonitor, TaskMonitorLog, Permission, User


@pytest.mark.usefixtures('db')
class TestUserAndPermission:
    """User and permission tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User(username='test1', password=generate_password_hash('cronmonpwd'), email='test1@cronmon.com',
                    phone='13912340001', status=True, admin=False)
        user.save()
        retrieved = User.get_by_id(user.id)
        assert retrieved == user

        permission = Permission(perm_list='', perm_user=user.id)
        permission.save()
        retrieved = Permission.get_by_id(permission.id)
        assert retrieved == permission

    def test_column_default_value(self):
        """Test column default value."""
        user = User(username='test2', password=generate_password_hash('cronmonpwd'), email='test2@cronmon.com',
                    phone='13912340002')
        user.save()
        assert user.status is True
        assert user.admin is False
        assert user.api_username is None
        assert user.api_password is None

        permission = Permission(perm_user=user.id)
        permission.save()
        assert permission.perm_list == ''

    def test_column_type(self):
        """Test columns type."""
        user = User(username='test4', password=generate_password_hash('cronmonpwd'), email='test4@cronmon.com',
                    phone='13912340004')
        user.save()
        assert isinstance(user.username, str)
        assert isinstance(user.password, str)
        assert isinstance(user.email, str)
        assert isinstance(user.phone, str)
        assert isinstance(user.status, bool)
        assert isinstance(user.admin, bool)

        permission = Permission(perm_user=user.id)
        permission.save()
        assert isinstance(permission.perm_list, str)
        assert isinstance(permission.perm_user, User)

    def test_check_password(self):
        """Check password."""
        user = User(username='test5', password=generate_password_hash('cronmonpwd'), email='test5@cronmon.com',
                    phone='13912340005', api_username='test5_api_usr', api_password='test5_api_pwd')
        assert user.verify_password('cronmonpwd') is True
        assert user.verify_password('yourpwd') is False
        assert user.verify_api_password('test5_api_pwd') is True
        assert user.verify_api_password('test5_api_wrongpwd') is False


    def test_password_is_nullable(self):
        """Test null password."""
        with pytest.raises(Exception) as excinfo:
            user = User(username='test3', email='test3@cronmon.com', phone='13912340003')
            user.save()
        assert "Field 'password' doesn't have a default value" in str(excinfo.value)


@pytest.mark.usefixtures('db')
class TestBusinessAndNotifier:
    """Business and notifier tests."""

    def test_get_by_id(self):
        """Get business by ID."""
        business = Business(business_name='biz1', status=True)
        business.save()
        retrieved = Business.get_by_id(business.id)
        assert retrieved == business

        notifier = Notifier(notify_name='nfy1', notify_email='nfy1@cronmon.com', notify_tel='13912347777', status=True)
        notifier.save()
        retrieved = Notifier.get_by_id(notifier.id)
        assert retrieved == notifier

        business_notifer = BusinessNotifier(business=business.id, notifier=notifier.id)
        business_notifer.save()
        retrieved = BusinessNotifier.get_by_id(business_notifer.id)
        assert retrieved == business_notifer

    def test_column_default_value(self):
        """Test column default value."""
        business = Business(business_name='biz2')
        business.save()
        assert business.status is True

        notifier = Notifier(notify_name='nfy2', notify_email='nfy2@cronmon.com', notify_tel='23912347777')
        notifier.save()
        assert notifier.status is True

    def test_column_type(self):
        """Test columns type."""
        business = Business(business_name='biz3')
        business.save()
        assert isinstance(business.business_name, str)
        assert isinstance(business.status, bool)

        notifier = Notifier(notify_name='nfy3', notify_email='nfy3@cronmon.com', notify_tel='33912347777')
        notifier.save()
        assert isinstance(notifier.notify_name, str)
        assert isinstance(notifier.notify_email, str)
        assert isinstance(notifier.notify_tel, str)
        assert isinstance(notifier.status, bool)

        business_notifier = BusinessNotifier(business=business.id, notifier=notifier.id)
        business_notifier.save()
        assert isinstance(business_notifier.business, Business)
        assert isinstance(business_notifier.notifier, Notifier)


@pytest.mark.usefixtures('db')
class TestTaskonitorAndLog:
    """Taskmonitor and taskmonitorlog tests."""

    def test_get_by_id(self):
        """Get business by ID."""
        taskmonitor = TaskMonitor(name='task1', url=TaskMonitor.gen_uuid(), period='* * * * *', grace_time=1,
                                  status=True, business=1)
        taskmonitor.save()
        retrieved = TaskMonitor.get_by_id(taskmonitor.id)
        assert retrieved == taskmonitor

        taskmonitor_log = TaskMonitorLog(occur_time=datetime.now(), client_ip='1.2.3.4', user_agent='Curl',
                                         taskmon=taskmonitor.id)
        taskmonitor_log.save()
        retrieved = TaskMonitorLog.get_by_id(taskmonitor_log.id)
        assert retrieved == taskmonitor_log

    def test_column_default_value(self):
        """Test column default value."""
        taskmonitor = TaskMonitor(name='task2', url=TaskMonitor.gen_uuid(), period='* * * * *', business=1)
        taskmonitor.save()
        assert taskmonitor.grace_time == 0
        assert taskmonitor.status is True
        assert taskmonitor.last_check_time is None
        assert taskmonitor.next_check_time is None
        assert taskmonitor.warning is False

    def test_column_type(self):
        """Test columns type."""
        taskmonitor = TaskMonitor(name='task3', url=TaskMonitor.gen_uuid(), period='* * * * *', business=1)
        taskmonitor.save()
        assert isinstance(taskmonitor.name, str)
        assert isinstance(taskmonitor.url, str)
        assert isinstance(taskmonitor.period, str)
        assert isinstance(taskmonitor.grace_time, int)
        assert isinstance(taskmonitor.status, bool)
        assert isinstance(taskmonitor.warning, bool)
        assert isinstance(taskmonitor.create_datetime, datetime)
        assert isinstance(taskmonitor.business, Business)

        taskmonitor_log = TaskMonitorLog(occur_time=datetime.now(),
                                         client_ip='1.2.3.4', user_agent='Curl', taskmon=taskmonitor.id)
        taskmonitor_log.save()
        assert isinstance(taskmonitor_log.occur_time, datetime)
        assert isinstance(taskmonitor_log.client_ip, str)
        assert isinstance(taskmonitor_log.user_agent, str)
        assert isinstance(taskmonitor_log.taskmon, TaskMonitor)
