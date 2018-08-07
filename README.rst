cronmon
=======

crython 是一个计划任务（定时任务）监控系统，可以对循环执行的程序和脚本进行监控告警，当其未按照预期执行时，发送邮件到对应邮箱进行通知。
同时可以将监控任务划分到不同业务下面，每个业务可以分配不同的通知人，建立业务、通知人和监控任务的多层级关系。

许可: `GNU GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>`__

|Build Status|

安装
~~~~

从github下载安装

.. code:: bash

        $ git clone git@github.com:bruceye777/cronmon.git
        $ python setup.py install  # 如果无需安装到site-packages目录，此步可省略。

初始化
~~~~~~

解压缩/安装之后，需要进行初始化工作，包括全局配置修改、系统表初始化和样例数据插入。

.. code:: bash

        $ vim cronmon/conf/config.py  # 全局配置修改

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/globalConfig.png

.. code:: bash

        $ python migrate.py init  # 系统表初始化，初始用户名和密码均为cronadmin
        $ python migrate.py sample  # 样例数据插入

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/init.png

使用
~~~~

-  登录；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/login.png

-  登录之后，看到的首页；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/home.png

-  业务管理相关操作；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/businesslist.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/businessedit.png

-  通知人管理相关操作；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/notifylist.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/notifyedit.png

-  业务通知人管理相关操作；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/businessnotifylist.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/businessnotifyedit.png

-  任务管理相关操作；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/tasklist.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/taskedit.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/taskloglist.png

-  系统管理相关操作；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/permlist.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/permedit.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/passwordreset.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/permbizedit.png

-  用户相关操作；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/user.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/passwordchange.png

-  业务管理员（普通用户）操作界面，业务通知人和任务可以查询编辑，通知人仅限查询；

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/normalUser.png

数据库结构变更
~~~~~~~~~~~~~~

如果要新增表或者修改表结构，通过如下方式进行：

.. code:: bash

        $ vim migrate.py  # 修改表结构定义文件

.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/createNewTable.png
.. image:: https://raw.githubusercontent.com/bruceye777/cronmon/master/docs/images/alterCurrentTable.png

贡献
~~~~

如果您想贡献代码，只需fork本仓库，然后push您的更改并发送pull请求。

获取帮助
~~~~~~~~

如果您有任何问题或建议，请在此仓库中打开一个issue，我会尽力提供帮助。
