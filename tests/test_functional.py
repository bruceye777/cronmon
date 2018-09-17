"""各个功能点路由测试，部分操作按角色（系统管理员和业务管理员）进行分别测试
此文件测试用例依赖于初始化脚本中的样本数据，如果数据有过更改，则有可能会导致测试失败
在删除测试中由于未找到webtest如何在模态c中模拟点击，改为直接post请求
"""
import pytest
from flask import url_for
from cronmon import get_config
from cronmon.models import Permission, User, TaskMonitor

CFG = get_config()
SITE_URL = CFG.URL_ROOT.split('/')[2]


def login(testapp, username, password):
    """Login"""
    # Goes to homepage
    url = 'https://'+SITE_URL+'/login'
    res = testapp.get(url)
    # Fills out login form
    form = res.forms['LoginForm']
    form['username'] = username
    form['password'] = password
    # Submit login action
    res = form.submit().maybe_follow()

    return res


def logout(testapp):
    """Logout"""
    res = testapp.get(url_for('auth.logout', _external=True)).follow()

    return res


def delete_post(testapp, submit_form, link_id, post_url):
    """Delete post"""
    post_id = submit_form.html.find(id=link_id).get('data-id')
    post_bid = submit_form.html.find(id=link_id).get('data-bid')
    post_response = testapp.post(url_for(post_url, _external=True), {'action': 'del', 'id': post_id, 'bid': post_bid})
    return post_response


class TestLogInLogout:
    """Login and logout."""

    def test_can_login_logout(self, testapp):
        """Login and logout operations."""
        res = login(testapp, 'bizadmin1', 'bizadmin1')
        assert res.status_int == 200
        assert u'当前本地时间' in res

        res = logout(testapp)
        assert u'您已退出登录' in res

    def test_sees_error_message_if_username_or_password_is_incorrect(self, testapp):
        """Show error if username or password is incorrect."""
        res = login(testapp, 'wrongusr', 'bizadmin1')
        assert u'用户名错误' in res

        res = login(testapp, 'bizadmin1', 'wrongpwd')
        assert u'密码错误' in res


class TestNormalUser:
    """Normal user operations."""

    def test_businessnotifier_crud(self, testapp):
        """Businessnotifier operations."""
        # Login
        login(testapp, 'bizadmin1', 'bizadmin1')

        # Create operation
        res = testapp.get(url_for('main.businessnotifieredit', _external=True))
        form = res.forms['BusinessNotifierEditForm']
        form['business'] = '3'
        form['notifier'] = '1'
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create operation(Duplicate)
        form['business'] = '3'
        form['notifier'] = '1'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Retrieve operation
        res = testapp.get(url_for('main.businessnotifierlist', _external=True)) 
        form = res.forms['BusinessNotifierSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'PEOP'
        res = form.submit()
        assert u'PEOP' in res
        assert u'王宁' in res

        # Update operation
        res = res.click(linkid='bnedit', index=0)
        form = res.forms['BusinessNotifierEditForm']
        form['notifier'] = '6'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Delete operation
        res = testapp.get(url_for('main.businessnotifierlist', _external=True))
        form = res.forms['BusinessNotifierSearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = '慕淑珍'
        res = delete_post(testapp, form.submit(), 'bndel', 'main.businessnotifierlist')
        assert u'删除成功' in res

    def test_task_crud(self, testapp):
        """Task operations."""
        # Login
        login(testapp, 'bizadmin1', 'bizadmin1')

        # Create operation
        res = testapp.get(url_for('main.taskedit', _external=True))
        form = res.forms['TaskEditForm']
        form['name'] = 'testTask1'
        form['period'] = '*/3 * * * *'
        form['grace_time'] = 1
        form['business'] = '3'
        form['status'] = True
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create operation(Duplicate)
        form['name'] = 'testTask1'
        form['period'] = '*/3 * * * *'
        form['grace_time'] = 1
        form['business'] = '3'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Create operation(Incorrect crontab format)
        form['period'] = 'a b c d e f'
        res = form.submit()
        assert u'非法的crontab格式' in res
        assert u'只能包含5个字段' in res

        # Retrieve operation
        res = testapp.get(url_for('main.tasklist', _external=True))
        form = res.forms['TaskSearchForm']
        form['search_by'] = 'name'
        form['search_content'] = 'testTask1'
        res = form.submit()
        assert u'testTask1' in res
        assert u'PEOP' in res

        # Update operation
        res = res.click(linkid='tedit')
        form = res.forms['TaskEditForm']
        form['period'] = '*/2 * * * *'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Retrieve operation(task log)
        res = res.click(linkid='tlist', index=0)
        assert res.status_int == 200

        # Delete operation
        res = testapp.get(url_for('main.tasklist', _external=True))
        form = res.forms['TaskSearchForm']
        form['search_by'] = 'name'
        form['search_content'] = 'testTask1'
        res = delete_post(testapp, form.submit(), 'tdel', 'main.tasklist')
        assert u'删除成功' in res

    def test_user_crud(self, testapp):
        """User operations."""
        # Login
        login(testapp, 'bizadmin1', 'bizadmin1')

        # Update operation(Password change)
        res = testapp.get(url_for('main.passwordchange', _external=True))
        form = res.forms['PasswordEditForm']
        form['old_password'] = 'bizadmin1'
        form['new_password'] = 'bizadmin1new'
        form['new_password_second'] = 'bizadmin1new'
        res = form.submit()
        assert u'密码修改成功' in res

        # Login (New password)
        res = login(testapp, 'bizadmin1', 'bizadmin1new')
        assert res.status_int == 200
        assert u'当前本地时间' in res

        # Update operation(Password change back)
        res = testapp.get(url_for('main.passwordchange', _external=True))
        form = res.forms['PasswordEditForm']
        form['old_password'] = 'bizadmin1new'
        form['new_password'] = 'bizadmin1'
        form['new_password_second'] = 'bizadmin1'
        res = form.submit()
        assert u'密码修改成功' in res

        # Logout
        res = logout(testapp)
        assert u'您已退出登录' in res

    def test_admin_task(self, testapp):
        """This will trigger errors,cause there's no permissions for normal user."""
        # Login
        login(testapp, 'bizadmin1', 'bizadmin1')

        # Admin task link
        res = testapp.get('https://'+SITE_URL+'/businesslist', expect_errors=True)
        assert res.status_int == 403
        res = testapp.get('https://'+SITE_URL+'/businessedit', expect_errors=True)
        assert res.status_int == 403
        res = testapp.get('https://'+SITE_URL+'/notifyedit', expect_errors=True)
        assert res.status_int == 403
        res = testapp.get('https://'+SITE_URL+'/permlist', expect_errors=True)
        assert res.status_int == 403
        res = testapp.get('https://'+SITE_URL+'/permedit', expect_errors=True)
        assert res.status_int == 403
        res = testapp.get('https://'+SITE_URL+'/permbizedit', expect_errors=True)
        assert res.status_int == 403
        res = testapp.get('https://'+SITE_URL+'/passwordreset', expect_errors=True)
        assert res.status_int == 403


class TestSuperUser:
    """Super user operations."""

    def test_business_crud(self, testapp):
        """Business Operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create operation
        res = testapp.get(url_for('main.businessedit', _external=True))
        form = res.forms['BusinessEditForm']
        form['business_name'] = 'justForTest'
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create operation(Duplicate)
        form['business_name'] = 'justForTest'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Retrieve operation
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTest'
        res = form.submit()
        assert u'justForTest' in res

        # Update operation
        res = res.click(linkid='bedit', index=0)
        form = res.forms['BusinessEditForm']
        form['business_name'] = 'justForTestAgain'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Delete operation
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTestAgain'
        res = delete_post(testapp, form.submit(), 'bdel', 'main.businesslist')
        assert u'删除成功' in res

    def test_notify_crud(self, testapp):
        """Notify Operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create operation
        res = testapp.get(url_for('main.notifyedit', _external=True))
        form = res.forms['NotifyEditForm']
        form['notify_name'] = 'notifyJustForTest'
        form['notify_email'] = 'notifyJustForTest@cronmon.com'
        form['notify_tel'] = '18919191919'
        form['status'] = True
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create operation(Duplicate)
        form['notify_name'] = 'notifyJustForTest'
        form['notify_email'] = 'notifyJustForTest@cronmon.com'
        form['notify_tel'] = '18919191919'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Retrieve operation
        res = testapp.get(url_for('main.notifylist', _external=True))
        form = res.forms['NotifySearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = 'notifyJustForTest'
        res = form.submit()
        assert u'18919191919' in res

        # Update operation
        res = res.click(linkid='nedit', index=0)
        form = res.forms['NotifyEditForm']
        form['notify_name'] = 'notifyJustForTestAgain'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Delete operation
        res = testapp.get(url_for('main.notifylist', _external=True))
        form = res.forms['NotifySearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = 'notifyJustForTestAgain'
        res = delete_post(testapp, form.submit(), 'ndel', 'main.notifylist')
        assert u'删除成功' in res

    def test_businessnotifier_crud(self, testapp):
        """Businessnotifier operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create operation
        res = testapp.get(url_for('main.businessnotifieredit', _external=True))
        form = res.forms['BusinessNotifierEditForm']
        form['business'] = '7'
        form['notifier'] = '6'
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create operation(Duplicate)
        form['business'] = '7'
        form['notifier'] = '6'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Retrieve operation
        res = testapp.get(url_for('main.businessnotifierlist', _external=True))
        form = res.forms['BusinessNotifierSearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = '慕淑珍'
        res = form.submit()
        assert u'慕淑珍' in res

        # Update operation
        res = res.click(linkid='bnedit', index=0)
        form = res.forms['BusinessNotifierEditForm']
        form['notifier'] = '12'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Delete operation
        res = testapp.get(url_for('main.businessnotifierlist', _external=True))
        form = res.forms['BusinessNotifierSearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = '和建军'
        res = delete_post(testapp, form.submit(), 'bndel', 'main.businessnotifierlist')
        assert u'删除成功' in res

    def test_task_crud(self, testapp):
        """Task operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create operation
        res = testapp.get(url_for('main.taskedit', _external=True))
        form = res.forms['TaskEditForm']
        form['name'] = 'testTask1'
        form['period'] = '*/3 * * * *'
        form['grace_time'] = 1
        form['business'] = '12'
        form['status'] = True
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create operation(Duplicate)
        form['name'] = 'testTask1'
        form['period'] = '*/3 * * * *'
        form['grace_time'] = 1
        form['business'] = '12'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Create operation(Incorrect crontab format)
        form['period'] = 'a b c d e f'
        res = form.submit()
        assert u'非法的crontab格式' in res
        assert u'只能包含5个字段' in res

        # Retrieve operation
        res = testapp.get(url_for('main.tasklist', _external=True))
        form = res.forms['TaskSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = '游戏3'
        res = form.submit()
        assert u'testTask1' in res
        assert u'游戏3' in res

        # Update operation
        res = res.click(linkid='tedit')
        form = res.forms['TaskEditForm']
        form['period'] = '*/2 * * * *'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Retrieve operation(task log)
        res = res.click(linkid='tlist', index=0)
        assert res.status_int == 200

        # Delete operation
        res = testapp.get(url_for('main.tasklist', _external=True))
        form = res.forms['TaskSearchForm']
        form['search_by'] = 'name'
        form['search_content'] = 'testTask1'
        res = delete_post(testapp, form.submit(), 'tdel', 'main.tasklist')
        assert u'删除成功' in res

    def test_system_crud(self, testapp):
        """System Operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create user operation
        res = testapp.get(url_for('main.permedit', _external=True))
        form = res.forms['PermEditForm']
        form['username'] = 'userJustForTest'
        form['email'] = 'userJustForTest@cronmon.com'
        form['phone'] = '16789898989'
        form['api_username'] = 'api_test_username'
        form['api_password'] = 'api_test_password'
        form['admin'] = False
        form['status'] = True
        res = form.submit().follow()
        assert u'初始密码' in res
        assert u'保存成功' in res

        # Create user operation(Duplicate)
        form['username'] = 'userJustForTest'
        form['email'] = 'userJustForTest@cronmon.com'
        form['phone'] = '16789898989'
        form['api_username'] = 'api_test_username'
        res = form.submit()
        assert u'Duplicate entry' in res

        # Retrieve operation
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTest'
        res = form.submit()
        assert u'16789898989' in res

        # Update operation(Perm)
        res = res.click(linkid='pedit', index=0)
        form = res.forms['PermEditForm']
        form['username'] = 'userJustForTestAgain'
        res = form.submit().follow()
        assert u'修改成功' in res

        # Update operation(PermBiz)
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTestAgain'
        res = form.submit()
        res = res.click(linkid='pbedit', index=0)
        form = res.forms['PermBizEditForm']
        form.set('business', True, index=0)
        form.set('business', True, index=6)
        res = form.submit()
        assert u'修改成功' in res

        # Incorrect permbiz link
        res = testapp.get('https://'+SITE_URL+'/permbizedit?id=999&uid=999', expect_errors=True)
        assert res.status_int == 500

        # Update operation(Password)
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTestAgain'
        res = form.submit()
        res = res.click(linkid='pwreset', index=0)
        form = res.forms['PasswordEditForm']
        form['new_password'] = 'userJustForTestAgain'
        form['new_password_second'] = 'userJustForTestAgain'
        res = form.submit().follow()
        assert u'密码重置成功' in res

        # Login and Logout(New password)
        res = login(testapp, 'userJustForTestAgain', 'userJustForTestAgain')
        assert res.status_int == 200
        assert u'当前本地时间' in res
        res = logout(testapp)
        assert u'您已退出登录' in res

        # Delete operation
        login(testapp, 'cronadmin2', 'cronadmin2')
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTestAgain'
        res = delete_post(testapp, form.submit(), 'pdel', 'main.permlist')
        assert u'删除成功' in res

    def test_user_crud(self, testapp):
        """User operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Update operation(Password change)
        res = testapp.get(url_for('main.passwordchange', _external=True))
        form = res.forms['PasswordEditForm']
        form['old_password'] = 'cronadmin2'
        form['new_password'] = 'cronadmin2new'
        form['new_password_second'] = 'cronadmin2new'
        res = form.submit()
        assert u'密码修改成功' in res

        # Login (New password)
        res = login(testapp, 'cronadmin2', 'cronadmin2new')
        assert res.status_int == 200
        assert u'当前本地时间' in res

        # Update operation(Password change back)
        res = testapp.get(url_for('main.passwordchange', _external=True))
        form = res.forms['PasswordEditForm']
        form['old_password'] = 'cronadmin2new'
        form['new_password'] = 'cronadmin2'
        form['new_password_second'] = 'cronadmin2'
        res = form.submit()
        assert u'密码修改成功' in res

        # Logout
        res = logout(testapp)
        assert u'您已退出登录' in res


@pytest.mark.usefixtures('db')
class TestStatusSwitch:
    """Status Switch operations."""

    def test_user_status_switch(self, testapp):
        """User Operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create user(status is false)
        res = testapp.get(url_for('main.permedit', _external=True))
        form = res.forms['PermEditForm']
        form['username'] = 'userJustForTest'
        form['email'] = 'userJustForTest@cronmon.com'
        form['phone'] = '16789898989'
        form['api_username'] = 'api_username'
        form['api_password'] = 'api_password'
        form['admin'] = False
        form['status'] = True
        res = form.submit().follow()
        assert u'保存成功' in res

        # Change password
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTest'
        res = form.submit()
        res = res.click(linkid='pwreset', index=0)
        form = res.forms['PasswordEditForm']
        form['new_password'] = 'userJustForTest'
        form['new_password_second'] = 'userJustForTest'
        res = form.submit().follow()
        assert u'密码重置成功' in res

        # Logout and Login with New user, trigger errors
        res = logout(testapp)
        assert u'您已退出登录' in res
        login(testapp, 'userJustForTest', 'userJustForTest')
        res = testapp.get('https://'+SITE_URL+'/taskedit?id=999&bid=999', expect_errors=True)
        assert res.status_int == 500
        res = testapp.get('https://'+SITE_URL+'/tasklistwrong', expect_errors=True)
        assert res.status_int == 404

        # Logout and login with super user,disable new user
        res = logout(testapp)
        assert u'您已退出登录' in res
        login(testapp, 'cronadmin2', 'cronadmin2')

        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTest'
        res = form.submit()
        assert u'userJustForTest' in res

        res = res.click(linkid='pedit', index=0)
        form = res.forms['PermEditForm']
        form['status'] = False
        res = form.submit().follow()
        assert u'修改成功' in res

        # Logout and Login with New user
        res = logout(testapp)
        assert u'您已退出登录' in res
        res = login(testapp, 'userJustForTest', 'userJustForTest')
        assert u'账户被禁用' in res

        # Delete new user
        login(testapp, 'cronadmin2', 'cronadmin2')
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTest'
        res = delete_post(testapp, form.submit(), 'pdel', 'main.permlist')
        assert u'删除成功' in res

    def test_business_status_switch(self, testapp):
        """Business Operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create business
        res = testapp.get(url_for('main.businessedit', _external=True))
        form = res.forms['BusinessEditForm']
        form['business_name'] = 'justForTestStatusSwitch'
        form['status'] = True
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create task
        res = testapp.get(url_for('main.taskedit', _external=True))
        form = res.forms['TaskEditForm']
        form['name'] = 'testTaskForStatusSwitch'
        form['period'] = '*/3 * * * *'
        form['grace_time'] = 1
        form['business'].select(text="justForTestStatusSwitch")
        form['status'] = True
        res = form.submit().follow()
        assert u'保存成功' in res

        # Disable business
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTestStatusSwitch'
        res = form.submit()
        res = res.click(linkid='bedit', index=0)
        form = res.forms['BusinessEditForm']
        form['status'] = False
        res = form.submit().follow()
        assert u'修改成功' in res

        # Get task status
        res = testapp.get(url_for('main.tasklist', _external=True))
        form = res.forms['TaskSearchForm']
        form['search_by'] = 'name'
        form['search_content'] = 'testTaskForStatusSwitch'
        res = form.submit()
        res = res.click(linkid='tedit')
        assert u'input checked id="status"' not in res

        # Enable task
        form = res.forms['TaskEditForm']
        form['status'] = True
        res = form.submit().follow()
        assert u'关联业务为禁用状态' in res

        # Enable business
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTestStatusSwitch'
        res = form.submit()
        res = res.click(linkid='bedit', index=0)
        form = res.forms['BusinessEditForm']
        form['status'] = True
        res = form.submit().follow()
        assert u'修改成功' in res

        # Get task status
        res = testapp.get(url_for('main.tasklist', _external=True))
        form = res.forms['TaskSearchForm']
        form['search_by'] = 'name'
        form['search_content'] = 'testTaskForStatusSwitch'
        res = form.submit()
        res = res.click(linkid='tedit')
        assert u'input checked id="status"' not in res

        # Delete business
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTestStatusSwitch'
        res = delete_post(testapp, form.submit(), 'bdel', 'main.businesslist')
        assert u'删除成功' in res

    def test_businessnotifier_status_switch(self, testapp):
        """Businessnotifier Operations."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create business
        res = testapp.get(url_for('main.businessedit', _external=True))
        form = res.forms['BusinessEditForm']
        form['business_name'] = 'justForTestStatusSwitch'
        form['status'] = False
        res = form.submit().follow()
        assert u'保存成功' in res

        # Create notify
        res = testapp.get(url_for('main.notifyedit', _external=True))
        form = res.forms['NotifyEditForm']
        form['notify_name'] = 'notifyJustForTest'
        form['notify_email'] = 'notifyJustForTest@cronmon.com'
        form['notify_tel'] = '18919191919'
        form['status'] = False
        res = form.submit().follow()
        assert u'保存成功' in res

        # Check business and notify
        res = testapp.get(url_for('main.businessnotifieredit', _external=True))
        assert u'justForTestStatusSwitch' not in res
        assert u'notifyJustForTest' not in res

        # Enable business
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTestStatusSwitch'
        res = form.submit()
        res = res.click(linkid='bedit', index=0)
        form = res.forms['BusinessEditForm']
        form['status'] = True
        res = form.submit().follow()
        assert u'修改成功' in res

        # Enable notify
        res = testapp.get(url_for('main.notifylist', _external=True))
        form = res.forms['NotifySearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = 'notifyJustForTest'
        res = form.submit()
        res = res.click(linkid='nedit', index=0)
        form = res.forms['NotifyEditForm']
        form['status'] = True
        res = form.submit().follow()
        assert u'修改成功' in res

        # Check business and notify
        res = testapp.get(url_for('main.businessnotifieredit', _external=True))
        assert u'justForTestStatusSwitch' in res
        assert u'notifyJustForTest' in res

        # Delete business
        res = testapp.get(url_for('main.businesslist', _external=True))
        form = res.forms['BusinessSearchForm']
        form['search_by'] = 'business_name'
        form['search_content'] = 'justForTestStatusSwitch'
        res = delete_post(testapp, form.submit(), 'bdel', 'main.businesslist')
        assert u'删除成功' in res

        # Delete notify
        res = testapp.get(url_for('main.notifylist', _external=True))
        form = res.forms['NotifySearchForm']
        form['search_by'] = 'notify_name'
        form['search_content'] = 'notifyJustForTest'
        res = delete_post(testapp, form.submit(), 'ndel', 'main.notifylist')
        assert u'删除成功' in res

    def test_superuser_normaluser_switch(self, testapp):
        """User level switch ."""
        # Login
        login(testapp, 'cronadmin2', 'cronadmin2')

        # Create user operation
        res = testapp.get(url_for('main.permedit', _external=True))
        form = res.forms['PermEditForm']
        form['username'] = 'userJustForTest'
        form['email'] = 'userJustForTest@cronmon.com'
        form['phone'] = '16789898989'
        form['api_username'] = 'api_username'
        form['api_password'] = 'api_password'
        form['admin'] = True
        form['status'] = True
        res = form.submit().follow()
        assert u'初始密码' in res
        assert u'保存成功' in res

        user_id = User.get(User.username == 'userJustForTest').id
        user_perm = Permission.get(Permission.perm_user == user_id).perm_list
        assert user_perm == '0'

        # Switch(from superuser to normaluser)
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTest'
        res = form.submit()
        res = res.click(linkid='pedit', index=0)
        form = res.forms['PermEditForm']
        form['admin'] = False
        res = form.submit().follow()
        assert u'修改成功' in res

        user_perm = Permission.get(Permission.perm_user == user_id).perm_list
        assert user_perm == ''

        # Switch(from normaluser to superuser)
        res = testapp.get(url_for('main.permlist', _external=True))
        form = res.forms['PermSearchForm']
        form['search_by'] = 'username'
        form['search_content'] = 'userJustForTest'
        res = form.submit()
        res = res.click(linkid='pedit', index=0)
        form = res.forms['PermEditForm']
        form['admin'] = True
        res = form.submit().follow()
        assert u'修改成功' in res

        user_perm = Permission.get(Permission.perm_user == user_id).perm_list
        assert user_perm == '0'


class TestApiCall:
    """Api call."""

    def test_tasks_all(self, testapp):
        """Test tasks all api call."""
        # Normal user
        testapp.authorization = ('Basic', ('api_bizadmin2', 'api_bizadmin2'))

        # Get user's all tasks
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks/all')
        assert u'tasks' in res
        assert res.status_int == 200

        # Get user's  all tasks with query strings
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks/all?page=2&length=2')
        assert u'tasks' in res
        assert res.status_int == 200

        # Get user's all tasks with query strings(Incorrect page number)
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks/all?page=999', expect_errors=True)
        assert u'Out of Range' in res
        assert res.status_int == 400

        # Admin user
        testapp.authorization = ('Basic', ('api_root2', 'api_pwd2'))

        # Get user's all tasks
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks/all')
        assert u'tasks' in res
        assert res.status_int == 200

    def test_task(self, testapp):
        """Test task api call."""
        testapp.authorization = ('Basic', ('api_bizadmin2', 'api_bizadmin2'))

        # Get task with keyword taskname
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks?taskname=secondTask')
        assert u'tasks' in res
        assert res.status_int == 200

        # Get task with keyword bizname
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks?bizname=PEOP')
        assert u'tasks' in res
        assert res.status_int == 200

        # Get task with keyword url
        cronmon_url = TaskMonitor.get(TaskMonitor.name == 'thirdTask').url
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks?url='+cronmon_url)
        assert u'tasks' in res
        assert res.status_int == 200

        # Get task with incorrect keyword
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks?biznamewrong=PEOP', expect_errors=True)
        assert res.status_int == 400

        # Get task with keyword(no results)
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks?bizname=PEOPwrong', expect_errors=True)
        assert u'No Records' in res
        assert res.status_int == 400

    def test_monitor_url(self, testapp):
        """Test monitor url api call."""
        testapp.authorization = None
        # Send request to monitor url with right link
        cronmon_url = TaskMonitor.get(TaskMonitor.name == 'thirdTask').url
        res = testapp.get('https://'+SITE_URL+'/api/monlink/'+cronmon_url)
        assert u'OK' in res
        assert res.status_int == 200

        # Send request to monitor url with incorrect link
        cronmon_url = 'f9e05ae0-43d2-4753-823a-wrong'
        res = testapp.get('https://' + SITE_URL + '/api/monlink/' + cronmon_url, expect_errors=True)
        assert u'Bad Request' in res
        assert res.status_int == 400

    def test_incorrect_permissions(self, testapp):
        """Test api call with incorrect permissions"""
        testapp.authorization = ('Basic', ('api_bizadmin2', 'api_bizadmin2pwd'))

        # Get user's all tasks
        res = testapp.get('https://'+SITE_URL+'/api/v1.0/tasks/all', expect_errors=True)
        assert u'Invalid credentials' in res
        assert res.status_int == 401


class TestOthers:
    """Test other functions."""

    def test_validate_code(self, testapp):
        """Test validate code."""
        testapp.authorization = None

        # Get user's all tasks
        res = testapp.get('https://'+SITE_URL+'/code')
        assert u'image' in str(res.headers)
        assert res.status_int == 200
