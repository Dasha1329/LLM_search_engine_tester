from flask_wtf  import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import InputRequired, Email, Length, EqualTo
from wtforms.fields import FieldList


class RegistrationForm(FlaskForm):
    email = StringField('Email: ', validators = [InputRequired(), Email(message='Некоррекктный email')], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', 
                             validators=[InputRequired(), 
                                         EqualTo('confirm', message='Пароли должны совпадать'), 
                                         Length(min=6, max=100, message="Слишком короткий пароль")
                                        ],
                             render_kw={"placeholder": "Password"})
    confirm  = PasswordField('Repeat Password', render_kw={"placeholder": "Repeat Password"})


class LoginForm(FlaskForm):
    email = StringField('Email: ', validators = [InputRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password:', validators = [InputRequired()], render_kw={"placeholder": "Password"})
    remember_me = BooleanField('Remember me:', default = False)
    
    
class CommentForm(FlaskForm):
    comment = TextAreaField('Комментарий: ')


class ProjectForm(FlaskForm):
    name = StringField('Название: ', validators = [InputRequired()])
    file = FileField('Файл с данными: ', validators=[FileRequired()])
