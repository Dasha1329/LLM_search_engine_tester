import io
import json
import struct
import sqlite3
import logging
import datetime
import pandas as pd


from flask import Flask, Response, abort, render_template, flash, request, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy


from forms import CommentForm, ProjectForm, RegistrationForm, LoginForm
from models import db, Item, Case, Project, User, default_columns


app = Flask(__name__)


login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Войдите в аккаунт для продолжения'
login.login_message_category = 'success'


app.config['WTF_CSRF_ENABLED'] = False
app.secret_key = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

# with app.app_context():
#     db.drop_all()
#     db.create_all()
#     db.session.commit()


@app.route('/secret_register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    form = RegistrationForm()
    
    if form.validate_on_submit():
        status = False
        
        if User.query.filter(User.email == form.email.data).first():
            status = True
            form.email.errors.append('Данная почта уже зарегистрирована')
        if status:
            return render_template('register.html', form=form)
        u = User(email = form.email.data)
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for('main'))
    return render_template('register.html', form=form)


@login.user_loader
def load_user(id):
    return User.query.get(int(id)) 


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return render_template('login.html', form=form)
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main'))


@app.route('/')
def main():
    projects = Project.query.filter_by(active_status=True).all()
    return render_template('main.html', projects=projects)


@app.route('/archive')
def archive():
    projects = Project.query.filter_by(active_status=False).all()
    return render_template('main_archive.html', projects=projects)


@app.route('/create_project', methods=["POST", "GET"])
def create_project():   
    form = ProjectForm()
    if request.method == 'GET':
        return render_template('create_project.html', form=form)
    if request.method == 'POST':
        if form.validate_on_submit():
            # Load df
            data = io.BytesIO(form.file.data.stream.read()) 
            data = json.load(data)
            # Create project
            project = Project(name=form.name.data)
            db.session.add(project)
            counter = 0
            # Create tasks
            for key in data:
                query_data = data[key]

                case = Case(
                    num=counter,
                    project=project,
                    query_text=query_data['query']
                )
                counter += 1
                
                if 'result' in query_data:                
                    relevant = 0
                    for elem in query_data['result']:
                        item_id = elem['item_id']
                        item_status = elem['answer']
                        if item_status == 'relevant':
                            relevant += 1
                        item = Item(
                            case=case,
                            item_name=query_data['items_info'][item_id]['_source']['long_web_name'],
                            image_link='https://main-cdn.sbermegamarket.ru/big2' + query_data['items_info'][item_id]['_source']['images'][0]['image_link'],
                            item_status=item_status
                        )
                        db.session.add(item)
                    case.precision = round(relevant / len(query_data['result']) , 2)
                    case.item_size = len(query_data['result'])
                db.session.add(case)
            db.session.commit()
            return redirect(url_for('main'))
        flash("Incorrect form")
        return render_template('create_project.html', form=form)
    return redirect(url_for('main'))


@app.route('/delete_project_<id>')
def delete_project(id:int):
    item = Project.query.filter_by(id=id).first()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('main'))


@app.route('/change_project_status_<id>')
def change_project_status(id:int):
    item = Project.query.filter_by(id=id).first()
    item.active_status = not item.active_status
    db.session.commit()
    return redirect(url_for('main'))


@app.route('/download_project_<id>')
def download_project(id:int):
    conn = sqlite3.connect("instance/database.db")
    df = pd.read_sql_query(f'SELECT * FROM "case" WHERE project_id={id} AND checked=1', conn)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=Project.query.filter_by(id=id).first().name + '.csv',
        mimetype='text/csv'
    )


@app.route('/download_example')
def download_example():
    return send_file('data/example.json', as_attachment=True, mimetype='text/csv', download_name='example.json')
  

@app.route('/project_main_<id>', methods=["POST", "GET"])
def project_main(id:int):
    data = Case.query.filter_by(project_id=id).all()
    length = len(data)
    print(length)
    
    return render_template('project_main.html', data=data, stats = [length])


@app.route('/page_check_<id>', methods=["POST", "GET"])
def page_check(id:int):
    form = CommentForm()
    data = Case.query.filter_by(id=id).first()

    if request.method == 'GET':
        form.comment.data = data.comment
        return render_template('page_check.html', form=form, data=data)
    
    if request.method == 'POST':
        if form.validate_on_submit():
            data.comment = form.comment.data
            db.session.commit()
            if data.num + 1 == len(Project.query.filter_by(id=data.project_id).first().cases):
                return redirect(url_for('project_main', id=data.project_id))
            return redirect(url_for('page_check', id=int(id) + 1))
        s
        flash("Incorrect form")
        return render_template('page_check.html', form=form, data=data)
    return redirect(url_for('project_main', id=data.project_id))
  

@app.route('/show_stats')
def show_stats():
    projects = Project.query.filter_by(active_status=True).all()
    text = ''
    for project in projects:
        data = Case.query.filter_by(project_id=project.id).all()
        lenght = len(data)
        lebeled = Case.query.filter_by(project_id=project.id, checked=1).count()
        text += f'Проект: {project.name}, проверено: {int(round(lebeled / lenght * 100, 0))}%\n'
    return Response(text, mimetype='text/plain')
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)