import os

from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from pyramid.security import remember, forget
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager

import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.ext.declarative import declarative_base

from waitress import serve

HERE = os.path.dirname(os.path.abspath(__file__))
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://power_user:hownowbrownsnake@localhost:5432/test1'
    #'postgresql://power_user:nopassword@localhost:5432/test1'
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
        return instance

    @classmethod
    def get_by_id(cls, id, session=DBSession):
        return session.query(cls).filter(cls.id == id).one()

    @classmethod
    def get_by_username(cls, username, session=DBSession):
        return session.query(cls).filter(cls.username == username).one()


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
        except Exception as e:
            error = e
        return HTTPFound(request.route_url('home'))
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
    return {}


@view_config(route_name="faq", renderer='templates/faqpage.jinja2')
def faq(request):
    return {}


def app():
    debug = os.environ.get('DEBUG', True)
    settings = {}
    settings['reload_all'] = debug
    settings['debug_all'] = debug
    if not os.environ.get('TESTING', False):
        engine = sa.create_engine(DATABASE_URL)
        DBSession.configure(bind=engine)
    auth_secret = os.environ.get('JOURNAL_AUTH_SECRET', "testing")
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
    config.add_route('faq', '/faq')
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
