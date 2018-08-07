import pytest
from webtest import TestApp
from cronmon import create_app, get_config
from cronmon.models import DB as _db


CFG = get_config()
SITE_URL = CFG.URL_ROOT.split('/')[2]


@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app('testing')
    _app.config['SERVER_NAME'] = SITE_URL
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture
def db(app):
    """A database for the tests."""
    _db.app = app

    with _db.transaction() as txn:
        yield txn
        txn.rollback()

    _db.close()
