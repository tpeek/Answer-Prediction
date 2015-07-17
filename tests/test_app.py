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
    }
    kwargs['session'] = db_session
    user = app.User.new(**kwargs)
    db_session.flush()
    u = db_session.query(app.User).filter(app.User.id == user.id).one()
    assert getattr(u, 'id', '') is not None
    assert getattr(u, 'username', '') == "Test_Username"
    manager = BCRYPTPasswordManager()
    assert manager.check(getattr(user, 'password', ''), "testpassword")


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
        'answer': '4'
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
        'answer': '4'
    }
    submission = app.Submission(**kwargs)
    db_session.add(submission)
    db_session.flush()
    return submission


# Fixture 10
# fixture to create authentication for first user
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


LOGIN = '<a href="http://localhost/login" id="loginlink" class="navlink">'
LOGOUT = '<a href="http://localhost/logout" id="logoutlink">'


# Test 5
# login with 'new_user' credentials
def test_login_success_unittest(suite):
    params = {
        'username': 'Test_Username',
        'password': 'testpassword'
    }
    suite['auth_req'].params = params

    assert app.login(suite['auth_req'])


# Test 6
# login with 'new_user' credentials
def test_login_success(suite):
    params = {
        'username': 'Test_Username',
        'password': 'testpassword'
    }
    response = suite['testapp'].post('/login', params=params, status='3*')
    redirected = response.follow()

    assert LOGOUT in redirected.body and '<main id="home">' in redirected.body
    assert LOGIN not in redirected.body


# Test 7
# use wrong password
def test_login_bad_pass_unittest(suite):
    params = {
        'username': 'Test_Username',
        'password': 'oops'
    }
    suite['auth_req'].params = params
    assert not app.login(suite['auth_req'])


# Test 8
# use wrong password
def test_login_bad_pass(suite):
    params = {
        'username': 'Test_Username',
        'password': 'oops'
    }
    response = suite['testapp'].post('/login', params=params, status='2*')

    assert 'Not authenticated' in response.body


# Test 9
# use wrong username
def test_login_bad_user_unittest(suite):
    params = {
        'username': 'whoops',
        'password': 'testpassword'
    }
    suite['auth_req'].params = params
    with pytest.raises(ValueError):    # login() raises ValueError
        app.login(suite['auth_req'])


# Test 10
# use wrong username
def test_login_bad_user(suite):
    params = {
        'username': 'whoops',
        'password': 'testpassword'
    }
    response = suite['testapp'].post('/login', params=params, status='2*')

    assert 'User does not exist' in response.body


# Test 11
# try logging in without all params
def test_login_missing_params_unittest(suite):
    params = [
        {'username': 'Test_Username'},
        {'password': 'testpassword'}
    ]
    for param in params:
        suite['auth_req'].params = param
        with pytest.raises(ValueError):
            app.login(suite['auth_req'])


# Test 12
# try logging in without password
def test_login_missing_password(suite):
    params = {
        'username': 'Test_Username'
    }
    response = suite['testapp'].post('/login', params=params, status='2*')

    assert 'Username and password are required' in response.body


# Test 13
# try logging in without username
def test_login_missing_username(suite):
    params = {
        'password': 'testpassword'
    }
    response = suite['testapp'].post('/login', params=params, status='2*')

    assert 'Username and password are required' in response.body


# Test 14
# logout logged in user
def test_logout(suite):
    test_login_success(suite)
    redirect = suite['testapp'].get('/logout', status="3*")
    response = redirect.follow()
    assert LOGIN in response.body and '<main id="home">' in response.body
    assert LOGOUT not in response.body


# Test 15
# try to create user without completing captcha
def test_create_user_without_captcha(suite):
    params = {
        'username': 'Test_Username',
        'password': 'testpassword',
        'confirm': 'testpassword'
    }
    response = suite['testapp'].post('/new_account', params=params, status='2*')

    assert 'Are you a human?' in response.body


# Test 16
# unit test trying to create a username that already exists
def test_username_already_exists(db_session, suite):
    kwargs = {
        'username': "Test_Username",
        'password': "testpassword"
    }
    user = app.User(**kwargs)
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.flush()


# Test 17
# getting homepage as anonymous
def test_homepage_as_anon(suite):
    response = suite['testapp'].get('/')
    assert LOGIN in response.body and '<main id="home">' in response.body
    assert LOGOUT not in response.body


# Test 18
# getting the question page from an unauthenticated user
def test_get_question_view_unauth(suite):
    response = suite['testapp'].get('/question', status='3*')
    assert response.status_code == 302  # redirect out
    redirected = response.follow()
    assert '<main id="home">' in redirected.body


# Test 19
# posting a submission from an unauthenticated hacker
def test_post_to_question_view_unauth(suite):
    params = {
        'question_id': '5',
        'user_id': '14',
        'answer': '4'
    }
    response = suite['testapp'].post('/question', params=params, status='3*')
    assert response.status_code == 302  # redirect out
    redirected = response.follow()
    assert '<main id="home">' in redirected.body


# Test 20
# trying to submit without answer
def test_submit_with_no_answer(suite):
    test_login_success(suite)
    params = {
        'question_id': suite['new_question'].id
    }
    response = suite['testapp'].post('/question', params=params, status='2*')
    assert 'class="question_form"' in response.body   # allow user to skip


# Test 21
# trying to submit with answer
def test_submit_with_answer(suite):
    test_login_success(suite)
    params = {
        'question_id': suite['new_question'].id,
        'answer': '4'
    }
    response = suite['testapp'].post('/question', params=params, status='2*')
    assert 'class="question_form"' in response.body


# # # # # # #
# BIG DATA  #
# # # # # # #


# Fixture 12
# create more questions
@pytest.fixture(scope="function")
def new_questions(db_session):
    questions = []
    for i in range(3, 101):
        kwargs = {
            'text': str(i) + '?'
        }
        kwargs['session'] = db_session
        question = app.Question.new(**kwargs)
        questions.append(question)
        db_session.flush()
    return questions


# Fixture 13
# create more users
@pytest.fixture(scope="function")
def new_users(db_session):
    users = []
    for i in range(3, 101):
        kwargs = {
            'username': "Test_Username" + str(i),
            'password': "testpassword" + str(i)
        }
        kwargs['session'] = db_session
        user = app.User.new(**kwargs)
        users.append(user)
        db_session.flush()
    return users


# Fixture 14
# create more submissions
@pytest.fixture(scope="function")
def new_submissions(db_session, new_questions, new_users):
    submissions = []
    for question in new_questions:
        for user in new_users:
            kwargs = {
                'question_id': question.id,
                'user_id': user.id,
                'answer': '4'
            }
            submission = app.Submission(**kwargs)
            db_session.add(submission)
            submissions.append(submission)
            db_session.flush()
    return submissions


# Fixture 15
# create submissions for first user
@pytest.fixture(scope="function")
def new_submissions_for_user1(db_session, new_questions, new_user):
    submissions = []
    for question in new_questions:
        kwargs = {
            'question_id': question.id,
            'user_id': new_user.id,
            'answer': '4'
        }
        submission = app.Submission(**kwargs)
        db_session.add(submission)
        submissions.append(submission)
        db_session.flush()
    return submissions


# Fixture 15
# fixture to create big data suite
@pytest.fixture(scope="function")
def big_data(
    new_questions,
    new_users,
    new_submissions
):
    return {
        'new_questions': new_questions,
        'new_users': new_users,
        'new_submissions': new_submissions,
    }


# Test 22
# submit answer of '4'
def test_submit_big_data_not_enough_data(suite, big_data):
    test_login_success(suite)
    params = {
        'question_id': suite['new_question'].id,  # question has one submission
        'answer': '4'
    }
    response = suite['testapp'].post('/question', params=params, status='2*')
    with open('aaa.html', 'w') as fh:
        fh.write(response.body)
    assert 'Prediction: Not enough data to predict this question.' in response.body


# Test 23
# submit answer of '4'
def test_submit_big_data_get_prediction(suite, big_data):
    test_login_success(suite)
    params = {
        'question_id': big_data['new_questions'][57].id,  # has 100 submissions
        'answer': '4'
    }
    response = suite['testapp'].post('/question', params=params, status='2*')
    assert 'Prediction: 4' in response.body

#test 25
def test_no_questions(suite):
    assert 1 == 1
    pass

def test_user_answers_question_frist_time(suite):
    pass
