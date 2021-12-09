from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField


class LoginForm(FlaskForm):
    login = StringField('login')
    password = StringField('password')
    remember_me = BooleanField('remember_me', default=False)


class RegForm(FlaskForm):
    username = StringField('username')
    fio = StringField('fio')
    age = DateField('date')
    password = StringField('password')
