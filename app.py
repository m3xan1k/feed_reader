from flask import Flask, render_template, redirect, url_for, request, flash
from wtforms import Form, StringField, PasswordField, validators
from flask_mongoengine import MongoEngine
import uuid
from parser import parse_feeds
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from passlib.hash import sha256_crypt


app = Flask(__name__)
app.config.from_pyfile('config.py')
db = MongoEngine(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# db schema
class User(UserMixin, db.Document):
    email = db.StringField(required=True, unique=True)
    username = db.StringField(required=True, unique=True, max_length=30)
    password = db.StringField(required=True, max_length=80)
    feeds = db.ListField(db.StringField(), default=list)


# Forms
class RegisterForm(Form):
    email = StringField([validators.InputRequired(), validators.Email(), validators.Length(max=30)])
    username = StringField([validators.InputRequired(), validators.Length(max=30)])
    password = PasswordField([validators.InputRequired(), validators.Length(min=8, max=80)])

class LoginForm(Form):
    username = StringField([validators.InputRequired()])
    password = PasswordField([validators.InputRequired()])


@login_manager.user_loader
def load_user(id):
    return User.objects(id=id).first()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        feed_url = request.form['feed_url']
        data = parse_feeds([feed_url])
        context = {
            'feed_url': feed_url,
            'data': data
        }
        return render_template('index.html', context=context)

    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        hashed_password = sha256_crypt.encrypt(form.password.data)
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=hashed_password
        )
        user.save()
        flash('You were successfully registered!')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('You logged out!')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.objects(username=form.username.data).first()

        if user:
            is_correct_password = sha256_crypt.verify(
                form.password.data,
                user.password
                )
            if is_correct_password:
                login_user(user)
                flash('Successed login!')
                return redirect(url_for('index'))

        flash('Username or password is incorrect!')
        return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/feed/add', methods=['POST'])
@login_required
def add():
    user = current_user
    if request.form['feed_url'] in user.feeds:
        flash('You already have this feed!')
        return redirect(url_for('index'))

    user.feeds.append(request.form['feed_url'])
    user.save()
    flash('{} successfully added to your feed!'.format(request.form['feed_url']))
    return redirect(url_for('index'))

@app.route('/feed', methods=['GET', 'POST'])
@login_required
def feed():
    user = current_user
    if request.method == 'POST':
        pass
    
    feeds = parse_feeds(user.feeds)
    return render_template('feed.html', feeds=feeds)

@app.route('/feed/delete', methods=['POST'])
@login_required
def delete():
    user = current_user
    url = request.form['feed_url']
    user.feeds.remove(url)
    user.save()
    flash('{} was removed from your feed!'.format(url))
    return redirect(url_for('feed'))

@app.route('/feed/edit', methods=['GET', 'POST'])
@login_required
def edit():
    user = current_user
    if request.method == 'POST':
        old_url = request.args.get('old_url')
        new_url = request.form['feed_url']

        index = user.feeds.index(old_url)
        user.feeds[index] = new_url

        user.save()

        flash('{} feed was changed to {}'.format(old_url, new_url))
        return redirect(url_for('feed'))

    url = request.args.get('feed_url')
    return render_template('edit.html', url=url)


if __name__ == '__main__':
    app.run(debug=True)