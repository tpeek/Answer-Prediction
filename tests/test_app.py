#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import pytest
from pyramid import testing
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from cryptacular.bcrypt import BCRYPTPasswordManager
import sys

TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    # 'postgresql://jameshemmaplardh:123:@localhost:5432/test-project1'
    'postgresql://jesse:Jjk5646!@localhost:5432/test-project1'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL

os.environ['TESTING'] = "True"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app


# Fixture 1
# create session connection
@pytest.fixture(scope="session")
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
        'password': "testpassword"
        # 'password2': "testpassword"
    }
    kwargs['session'] = db_session
    user = app.User.new(**kwargs)
    db_session.flush()
    u = db_session.query(app.User).filter(app.User.id == user.id).one()
    assert getattr(u, 'id', '') is not None
    assert getattr(u, 'username', '') == "Test_Username"
    manager = BCRYPTPasswordManager()
    assert manager.check(getattr(user, 'password', ''), "testpassword")
    # assert getattr(user, 'password2', '') == "testpassword"


# Test 2
# submission of answer
def test_provide_answer(db_session):
    kwargs = {
        'question_id': '1',
        'user_id': '2',
        'answer': '3'
    }
    submission = app.Submission(**kwargs)
    db_session.add(submission)
    db_session.flush()
    s = db_session.query(app.Submission).filter(
        app.Submission.id == submission.id
    ).one()
    assert getattr(s, 'id', '') is not None
    assert getattr(s, 'question_id', '') is '1'
    assert getattr(s, 'user_id', '') is '2'
    assert getattr(s, 'answer', '') is '3'


# Test 3
# submission of answer sans answer
def test_provide_no_answer(db_session):
    kwargs = {
        'question_id': '5',
        'user_id': '14'
    }
    submission = app.Submission(**kwargs)
    db_session.add(submission)
    with pytest.raises(IntegrityError):
        db_session.flush()


# Test 4
# leaving second field blank
def test_create_user_failure(db_session):
    kwargs = {'username': "Test_Username"}
    kwargs['session'] = db_session
    with pytest.raises(ValueError):
        app.User.new(**kwargs)


# Fixture 3
# create webtest app
@pytest.fixture(scope="function")
def testapp():
    from webtest import TestApp
    app_ = app.app()
    return TestApp(app_)


# Fixture 4
# fixture to create new question
@pytest.fixture(scope="function")
def new_question(db_session):
    kwargs = {
        'text': "1?",
    }
    kwargs['session'] = db_session
    question = app.Question.new(**kwargs)
    db_session.flush()
    return question


# Fixture 5
# fixture to create 2nd question
@pytest.fixture(scope="function")
def new_question2(db_session):
    kwargs = {
        'text': "2?",
    }
    kwargs['session'] = db_session
    question = app.Question.new(**kwargs)
    db_session.flush()
    return question


# Fixture 6
# fixture to create user
@pytest.fixture(scope="function")
def new_user(db_session):
    kwargs = {
        'username': "Test_Username",
        'password': "testpassword"
        # 'password2': "testpassword"
    }
    kwargs['session'] = db_session
    user = app.User.new(**kwargs)
    db_session.flush()
    return user


# Fixture 7
# fixture to create 2nd user
@pytest.fixture(scope="function")
def new_user2(db_session):
    kwargs = {
        'username': "Test_Username2",
        'password': "testpassword2"
        # 'password2': "testpassword"
    }
    kwargs['session'] = db_session
    user = app.User.new(**kwargs)
    db_session.flush()
    return user


# Fixture 8
# fixture to create new answer submission
@pytest.fixture(scope="function")
def new_submission(db_session, new_question, new_user2):
    kwargs = {
        'question_id': new_question.id,
        'user_id': new_user2.id,
        'answer': '3'
    }
    submission = app.Submission(**kwargs)
    db_session.add(submission)
    db_session.flush()
    return submission


# Fixture 9
# fixture to create second answer submission
@pytest.fixture(scope="function")
def new_submission2(db_session, new_question2, new_user2):
    kwargs = {
        'question_id': new_question2.id,
        'user_id': new_user2.id,
        'answer': '3'
    }
    submission = app.Submission(**kwargs)
    db_session.add(submission)
    db_session.flush()
    return submission


# Fixture 10
# fixture to create authentication
@pytest.fixture(scope="function")
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'Test_Username',
        'auth.password': manager.encode('testpassword'),
    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req


# Fixture 11
# fixture to create suite
@pytest.fixture(scope="function")
def suite(
    testapp,
    new_user,
    new_user2,
    new_question,
    new_question2,
    new_submission,
    new_submission2,
    auth_req
):
    return {
        'testapp': testapp,
        'new_user': new_user,
        'new_user2': new_user2,
        'new_question': new_question,
        'new_question2': new_question2,
        'new_submission': new_submission,
        'new_submission2': new_submission2,
        'auth_req': auth_req
    }


# Test 5
# getting homepage
def test_homepage(suite):
    response = suite['testapp'].get('/')
    assert response.status_code == 200
    assert "<main id=home>" in response.body


# Test 6
# try to create a username that already exists
def test_username_already_exists(suite):
    params = {
        'username': "Test_Username",
        'password': "testpassword"
        # 'password2': "testpassword"
    }
    response = suite['testapp'].post('/new_account', params=params, status='2*')
    assert "<strong>Error</strong>" in response.body


# Test 7
# getting the question page from an unauthenticated hacker
def test_get_question_view_unauth(suite):
    response = suite['testapp'].get('/question', status='3*')
    assert response.status_code == 302  # redirect out
    redirected = response.follow()
    assert "<main id=home>" in redirected.body


# Test 8
# posting a submission from an unauthenticated hacker
def test_post_to_question_view_unauth(suite):
    params = {
        'question_id': '5',
        'user_id': '14',
        'answer': '3'
    }
    response = suite['testapp'].post('/question', params=params, status='3*')
    assert response.status_code == 302  # redirect out
    redirected = response.follow()
    assert "<main id=home>" in redirected.body


# Test 9
# login with 'new_user' credentials
def test_login_success(suite):
    params = {
        'username': 'Test_Username',
        'password': 'testpassword'
    }
    suite['auth_req'].params = params

    assert app.login(suite['auth_req'])

    response = suite['testapp'].post('/login', params=params, status='3*')
    assert response.status_code == 302
    redirected = response.follow()
    assert "<main id=home>" in redirected.body


# Test 9.5
#
def test_login_bad_pass(suite):
    params = {
        'username': 'Test_Username',
        'password': 'oops'
    }
    suite['auth_req'].params = params
    assert not app.login(suite['auth_req'])


# Test 10
# trying to submit without answer
def test_submit_with_no_answer(suite):
    test_login_success(suite)
    params = {
        'question_id': suite['new_question'].id
    }
    response = suite['testapp'].post('/question', params=params, status='2*')
    assert 'class="question_form"' in response.body   # allow user to skip


# Test 11
# trying to submit with answer
def test_submit_with_answer(suite):
    test_login_success(suite)
    params = {
        'question_id': suite['new_question'].id,
        'answer': '2'
    }
    response = suite['testapp'].post('/question', params=params, status='2*')
    assert 'class="question_form"' in response.body


# Fixture 11.5
# fixture to create authentication
"""@pytest.fixture(scope='function')
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'user1',
        'auth.password': manager.encode('secret'),

    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req"""


"""def test_login_bad_user(auth_req):
    from journal import login
    auth_req.params = {'username': 'bad', 'password': 'secret'}
    assert not login(auth_req)


def test_login_missing_params(auth_req):
    from journal import login
    for params in ({'username': 'admin'}, {'password': 'secret'}):
        auth_req.params = params
        with pytest.raises(ValueError):
            login(auth_req)

INPUT_BTN = '<input type="submit" value="Share" name="Share"/>'
"""

# def login(username, password, testapp):
#     """encapsulate app login for reuse in tests

#     Accept all status codes so that we can make assertions in tests
#     """
#     login_data = {'username': username, 'password': password}
#     return app.post('/login', params=login_data, status='*')

"""
def test_start_as_anonymous(testapp):
    response = app.get('/', status=200)
    actual = response.body
    assert INPUT_BTN not in actual


def test_login_success(app):
    username, password = ('admin', 'secret')
    redirect = login(username, password, testapp)
    assert redirect.status_code == 302
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert INPUT_BTN in actual


def test_login_fails(testapp):
    username, password = ('admin', 'wrong')
    response = login(username, password, testapp)
    assert response.status_code == 200
    actual = response.body
    assert "Login Failed" in actual
    assert INPUT_BTN not in actual

def test_logout(testapp):
    # re-use existing code to ensure we are logged in when we begin
    test_login_success(testapp)
    redirect = testapp.get('/logout', status="3*")
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert INPUT_BTN not in actual

"""
