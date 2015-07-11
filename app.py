import os

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from pyramid.security import remember, forget
from cryptacular.bcrypt import BCRYPTPasswordManager

import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.ext.declarative import declarative_base

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    ""  # TODO update once database is set up
)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.Unicode(127), nullable=False, unique=True)
    password = sa.Column(sa.Unicode(127), nullable=False)

    @classmethod
    def new(cls, username=None, password=None, session=DBSession):
        manager = BCRYPTPasswordManager()
        if not (username and password):
            raise ValueError("Username and password needed")
        hashed = manager.encode(password)
        instance = cls(username=username, password=hashed)
        session.add(instance)
        session.flush()
        return instance

    @classmethod
    def get_by_id(cls, id, session=DBSession):
        return session.query(cls).filter(cls.id == id).one()

    @classmethod
    def get_by_username(cls, username, session=DBSession):
        return session.query(cls).filter(cls.username == username).one()


@view_config(route_name="login_page", renderer="string")
def login_page(request):
    username = request.params.get('username', '')
    error = ""
    if request.method == "POST":
        try:
            authenticated = login(request)
        except ValueError as e:
            error = e

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)
    return {'error': error}


@view_config(route_name="new_account", renderer="string")
def new_account_page(request):
    error = ""
    if request.method == "POST":
        try:
            make_new_account(request)
        except Exception as e:
            error = e
    return {'error': error}


def make_new_account(request):
    username = request.params.get('username', None)
    passsword = request.params.get('password', None)
    User.new(username, passsword)


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


@view_config(route_name="home", renderer="text")
def home(request):
    return "You are at the home page"


@view_config(route_name="logout")
def do_logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url("login_page"), headers=headers)
