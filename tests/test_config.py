"""app初始化时，各种环境的变量配置测试
此文件测试用例依赖于初始化脚本中的样本数据，如果数据有过更改，则有可能会导致测试失败
"""
from cronmon import create_app


def test_development_config():
    """Production config."""
    app = create_app('development')
    assert app.config['DEBUG'] is True


def test_testing_config():
    """Development config."""
    app = create_app('testing')
    assert app.config['TESTING'] is True


def test_production_config():
    """Development config."""
    app = create_app('production')
    assert app.config['PRODUCTION'] is True


def test_default_config():
    """Development config."""
    app = create_app('default')
    assert app.config['DEBUG'] is True
    assert app.config['DB_DATABASE'] == 'cronmon'
