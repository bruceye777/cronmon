"""后台定时任务测试，通过监控日志实现，计划任务运行后，在一定时间段内，如果有符合关键字的文本出现，则认为符合预期，反之则不然
此文件测试用例依赖于初始化脚本中的样本数据，如果数据有过更改，则有可能会导致测试失败
"""
from cronmon.main.taskcyclecheck import taskcyclecheck, emptybusinesscheck


class TestCycleTasks:
    """Cycle tasks tests."""

    def test_empty_business(self, caplog):
        """Check empty business."""
        emptybusinesscheck()
        assert 'Empty Business' in caplog.text

    def test_monitor_job(self, caplog):
        """Check monitor jobs."""
        taskcyclecheck()
        assert 'Status is' not in caplog.text
