#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
# import webtest
from pyramid import testing
# import pdb; pdb.set_trace()
from cryptacular.bcrypt import BCRYPTPasswordManager
import sys
sys.path.insert(0, 'Users/jameshemmaplardh/projects/AnswerPrediction/Answer-Prediction/')
import app

#fixes test import path
# myPath = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, myPath + '/../')

TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://jameshemmaplardh:123:@localhost:5432/test-project1'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL

os.environ['TESTING'] = "True"




@pytest.fixture(scope='function')
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'admin',
        'auth.password': manager.encode('jjwt2015'),

    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req

def test_do_login_success(auth_req):
    from app import login
    auth_req.params = {'username': 'admin', 'password': 'jjwt2015'}
    assert login(auth_req)


def test_do_login_bad_pass(auth_req):
    from app import login
    auth_req.params = {'username': 'admin', 'password': 'wrong'}
    assert not login(auth_req)


def test_do_login_bad_user(auth_req):
    from app import login
    auth_req.params = {'username': 'bad', 'password': 'secret'}
    assert not login(auth_req)


def test_do_login_missing_params(auth_req):
    from app import login
    for params in ({'username': 'admin'}, {'password': 'secret'}):
        auth_req.params = params
        with pytest.raises(ValueError):
            login(auth_req)


def login_helper(username, password, app):
    """encapsulate app login for reuse in tests

    Accept all status codes so that we can make assertions in tests
    """
    login_data = {'username': username, 'password': password}
    return app.post('/login', params=login_data, status='*')


def test_start_as_anonymous(app):
    response = app.get('/', status=200)
    actual = response.body
    assert INPUT_BTN not in actual


def test_login_success(app):
    username, password = ('admin', 'secret')
    redirect = login_helper(username, password, app)
    assert redirect.status_code == 302
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert INPUT_BTN in actual


def test_login_fails(app):
    username, password = ('admin', 'wrong')
    response = login_helper(username, password, app)
    assert response.status_code == 200
    actual = response.body
    assert "Login Failed" in actual
    assert INPUT_BTN not in actual

def test_logout(app):
    # re-use existing code to ensure we are logged in when we begin
    test_login_success(app)
    redirect = app.get('/logout', status="3*")
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert INPUT_BTN not in actual

def test_urllog(app):
    pass

def test_cmdlinehack(app):
    pass

def test_database_insync(app):
    pass

