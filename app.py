#!/usr/bin/env python

# python imports
import os
from random import randint
# pyramid imports
from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
# security imports
from pyramid.security import remember, forget
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager
# sqlalchemy imports
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.ext.declarative import declarative_base
# server imports
from waitress import serve

import numpy as np
#from recaptcha import captcha

HERE = os.path.dirname(os.path.abspath(__file__))
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DATABASE_URL = os.environ.get(
    'DATABASE_URL')
Base = declarative_base()


# -Models-
class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.Unicode(127), nullable=False, unique=True)
    password = sa.Column(sa.Unicode(127), nullable=False)

    @classmethod
    def new(cls, username=None, password=None, session=DBSession):
        """Stores password in database already hashed"""
        manager = BCRYPTPasswordManager()
        if not (username and password):
            raise ValueError("Username and password needed")
        hashed = unicode(manager.encode(password))
        try:
            instance = cls(username=username, password=hashed)
            session.add(instance)
            session.flush()
        except IntegrityError:
            raise ValueError("Username already in use")
        return instance

    @classmethod
    def get_by_id(cls, id, session=DBSession):
        return session.query(cls).filter(cls.id == id).one()

    @classmethod
    def get_by_username(cls, username, session=DBSession):
        return session.query(cls).filter(cls.username == username).one()


class Question(Base):
    __tablename__ = "questions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    text = sa.Column(sa.Unicode(), nullable=False, unique=True)

    @classmethod
    def new(cls, text, session=DBSession):
        instance = cls(text=text)
        session.add(instance)
        return instance

    @classmethod
    def all(cls, session=DBSession):
        return session.query(cls).all()

    @classmethod
    def get_question_by_id(cls, id, session=DBSession):
        return session.query(cls).filter(cls.id == id).one()


class Submission(Base):
    """Stores answers tied to a user id and a question id"""
    __tablename__ = "answers"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, nullable=False)
    question_id = sa.Column(sa.Integer, nullable=False)
    answer = sa.Column(sa.Integer, nullable=False)

    @classmethod
    def new(cls, user, question, answer, session=DBSession):
        instance = cls(user_id=user.id, question_id=question.id, answer=answer)
        session.add(instance)
        return instance

    @classmethod
    def all(cls, session=DBSession):
        return session.query(cls).all()

    @classmethod
    def get_all_for_question(cls, question, session=DBSession):
        return session.query(cls).filter(cls.question_id == question.id).all()

    @classmethod
    def get_all_for_user(cls, user, session=DBSession):
        return session.query(cls).filter(cls.user_id == user.id).all()

    @classmethod
    def get_answer(cls, user, question, session=DBSession):
        return session.query(cls).filter(
            cls.user_id == user.id).filter(cls.question_id == question.id
                                           ).one().answer


# -Views-
@view_config(route_name="login", renderer="templates/gatepage.jinja2")
def login_page(request):
    if request.method == "POST":
        username = request.params.get('username', '')
        authenticated = False
        try:
            authenticated = login(request)
        except ValueError as e:
            return {'error': e}

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)

        else:
            return {'error': 'Not authenticated'}
    else:
        return {}


@view_config(route_name="new_account", renderer="templates/new_account.jinja2")
def new_account_page(request):
    error = ""
    if request.method == "POST":
        try:
            username = request.params.get('username', None)
            passsword = request.params.get('password', None)
            User.new(username, passsword)
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)
        except Exception as e:
            error = e
            return {'error': error}
    return {'error': error}


def login(request):
    username = request.params.get("username", None)
    password = request.params.get("password", None)
    if not (username and password):
        raise ValueError("Username and password are required")
    manager = BCRYPTPasswordManager()
    try:
        user = User.get_by_username(username)
    except:
        raise ValueError("User does not exist")
    return manager.check(user.password, password)


@view_config(route_name="home", renderer='templates/homepage.jinja2')
def home(request):
    return {}


@view_config(route_name="logout")
def do_logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url("home"), headers=headers)


@view_config(route_name="question", renderer='templates/questionpage.jinja2')
def question(request):
    if request.authenticated_userid:
        user = User.get_by_username(request.authenticated_userid)
        if request.method == "POST":
            answer = request.params.get("answer")
            question = Question.get_question_by_id(
                request.params.get("question_id")
            )
            if answer is not None and question.id not in Submission.get_all_for_user(user):
                Submission.new(
                    user=user,
                    question=question,
                    answer=answer
                )
        questions = Question.all()
        if questions:
            submissions = Submission.get_all_for_user(user)
            l = []
            for q in questions:
                if q.id not in [s.question_id for s in submissions]:
                    l.append(q)
            if l:
                question = l[randint(0, len(l) - 1)]
                x, u, y = make_data(question, user)
                if x != [] and y != []:
                    prediction = guess(x, u, y)
                else:
                    prediction = None
            else:
                return {"question": None, "prediction": None}
            return {"question": question, "prediction": prediction}
        else:
            return {"question": None, "prediction": None}
    else:
        return HTTPFound(request.route_url('home'))


@view_config(route_name="about", renderer='templates/faqpage.jinja2')
def faq(request):
    return {}


def make_data(question, user):
    """Gets data from the database and parses it for the Guess function"""
    questions, u = _get_data(user, question)
    users = _select_users(u, questions, user)
    x = _parse_into_matrix(questions, users)
    y = []
    for user in users:
        y.append(Submission.get_answer(user, question))
    u = [sub.answer for sub in Submission.get_all_for_user(user)]
    return x, u, y


def _select_users(u, questions, user):
    users = u[0]
    for item in u:
            users = list(
                set(users) & set(item)
            )
    return users


def _get_data(user, question):
    """Queries database for all the questions the user has answered
    then queries for all the users that have answered all those
    questions plus the question that the user is currently answering"""
    users = []
    questions = [Question.get_question_by_id(sub.question_id)
                 for sub in Submission.get_all_for_user(user)
                 ]

    questions.append(question)

    for q in questions:
        users.append([User.get_by_id(sub.user_id)
                      for sub in Submission.get_all_for_question(q)
                      ])
    return questions, users


def _parse_into_matrix(questions, users):
    """Sets matrix x to have a column for each question the
    user has answered, and fills each column with answers that
    the users have answered in the same order for each column"""
    x = [[] for q in range(len(questions) - 1)]
    for i, slot in enumerate(x):
        for user in users:
            slot.append(Submission.get_answer(user, questions[i]))
    return x


def guess(every_answer, user_answers, cur_question):
    n = len(every_answer[0])
    for each in every_answer:
        if len(each) != n:
            raise ValueError("Every list must be of the same length, asshole.")
    every_answer.append(np.ones(n))
    A = np.vstack(every_answer).T
    every_x = np.linalg.lstsq(A, cur_question)[0]
    total = 0
    user_answers.append(1)  # the last value in every_x is c.
    for the_x, u_ans in zip(every_x, user_answers):
        total += u_ans * the_x
    if total > 5:
        total = 5
    elif total < 1:
        total = 1
    return total


# -App-
def app():
    debug = os.environ.get('DEBUG', True)
    settings = {}
    settings['reload_all'] = debug
    settings['debug_all'] = debug
    if not os.environ.get('TESTING', False):
        engine = sa.create_engine(DATABASE_URL)
        DBSession.configure(bind=engine)
    auth_secret = os.environ.get('AUTH_SECRET', "testing")
    # and add a new value to the constructor for our Configurator:
    authn_policy = AuthTktAuthenticationPolicy(
        secret=auth_secret,
        hashalg='sha512'
    )
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy
    )
    config.include('pyramid_tm')
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(HERE, 'static'))
    config.add_route('home', '/')
    config.add_route('new_account', '/new_account')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('question', '/question')
    config.add_route('about', '/about')
    config.scan()
    app = config.make_wsgi_app()
    return app


def init_db():
    engine = sa.create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    app = app()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
