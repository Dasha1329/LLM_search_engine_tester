from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

default_columns = {
    'query',
    'item_name',
    'image_link',
    'comment'
}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    
class Project(db.Model):
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=False)
    cases = db.relationship('Case', backref='project', cascade="all,delete")
    active_status = db.Column(db.Boolean, nullable=False, default=True)
    
    
class Case(db.Model):
    __tablename__ = 'case'
    
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    
    query_text = db.Column(db.String, nullable=True)
    items = db.relationship('Item', backref='case', cascade="all,delete")
    precision = db.Column(db.Float, default=0)
    item_size = db.Column(db.Integer, default=0)

    comment = db.Column(db.Text, nullable=True, default='')

class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))

    item_name = db.Column(db.String, nullable=True)
    image_link = db.Column(db.String, nullable=True)
    item_status = db.Column(db.String, nullable=True)