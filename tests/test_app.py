#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
import webtest
from pyramid import testing
from cryptacular.bcrypt import BCRYPTPasswordManager
import sys

TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://jameshemmaplardh:123:@localhost:5432/test-project1'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL

os.environ['TESTING'] = "True"

sys.path.insert(0, '/Users/jameshemmaplardh/projects/AnswerPrediction/Answer-Prediction')
import app


#makes db
createdb test-project1

# Fixture 1
# create session connection
@pytest.fixture(scope='session')
def connection(request):
    engine = create_engine(TEST_DATABASE_URL)
    app.Base.metadata.create_all(engine)
    connection = engine.connect()
    app.DBSession.registry.clear()
    app.DBSession.configure(bind=connection)
    app.Base.metadata.bind = engine
    request.addfinalizer(app.Base.metadata.drop_all)
    return connection


# Fixture 2
# create session transaction
@pytest.fixture(scope="function")
def db_session(request, connection):
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)

    return app.DBSession


# Test 1
# database creation of user
def test_create_user(db_session):
    kwargs = {
        'username': "Test_Username",
        'password': "testpassword",
        # 'password2': "testpassword"
    }
    kwargs['session'] = db_session
    user = app.User.new(**kwargs)
    db_session.flush()
    assert getattr(user, 'id', '') is not None
    assert getattr(user, 'username', '') == "Test_Username"
    manager = BCRYPTPasswordManager()
    assert manager.check(getattr(user, 'password', ''), "testpassword")
    # assert getattr(user, 'password2', '') == "testpassword"


# Test 2
# submission of answer
"""def test_provide_answer(db_session):
    kwargs = {
        'question_id': 5,
        'user_id': 14,
        # 'answer': 3
    }
    kwargs['session'] = db_session
    entry = app.Question.new(**kwargs)
    db_session.flush()
    assert getattr(entry, id, '') is not None
    assert getattr(entry, 'question_id', '') is 5
    assert getattr(entry, 'user_id', '') is 14
    # assert getattr(entry, 'answer', '') is 3"""


# Test 3
# leaving second password field blank
def test_create_user_failure(db_session):
    kwargs = {'username': "Test_Username"}
    kwargs['session'] = db_session
    with pytest.raises(ValueError):
        app.User.new(**kwargs)


# Fixture 3
# create webtest app
@pytest.fixture()
def testapp():
    from webtest import TestApp
    app_ = app.app()
    return TestApp(app_)


# Fixture 4
# fixture to create new user
@pytest.fixture()
def new_user(db_session):
    kwargs = {
        'username': "Test_Username",
        'password': "testpassword",
        # 'password2': "testpassword"
    }
    kwargs['session'] = db_session
    user = app.User.new(**kwargs)
    db_session.flush()
    return user


# Fixture 5
# fixture to create new answer submission
"""@pytest.fixture()
def new_submission(db_session):
    kwargs = {
        'question_id': 5,
        'user_id': 14,
        # 'answer': 3
    }
    kwargs['session'] = db_session
    submission = app.Question.new(**kwargs)
    db_session.flush()
    return submission"""


# Test 4
# getting homepage with a user in the database ready to be used
def test_homepage(testapp, new_user):
    response = testapp.get('/')
    assert response.status_code == 200
    assert getattr(new_user, 'username', '') == "Test_Username"
    manager = BCRYPTPasswordManager()
    assert manager.check(getattr(new_user, 'password', ''), "testpassword")
    # assert getattr(new_user, 'password2', '') == "testpassword"


# Test 5
# getting homepage with a user in the database ready to be used
"""def test_post_to_add_view(testapp, new_submission):
    params = {
        'question_id': 5,
        'user_id': 14,
        # 'answer': 3
    }
    response = testapp.post('/add', params=params, status='3*')
    assert response.status_code == 300
    assert getattr(new_submission, 'question_id', '') is 5
    assert getattr(new_submission, 'user_id', '') is 14
    # assert getattr(new_submission, 'answer', '') is 3"""


# Test 6
# trying to get '/add'
def test_try_to_get(testapp):
    with pytest.raises(webtest.AppError):
        testapp.get('/add')


# Test 7
# trying to submit without params
"""def test_add_no_params(testapp):
    test_login_success(testapp)
    response = testapp.post('/add', status=500)
    assert 'IntegrityError' in response.body"""
