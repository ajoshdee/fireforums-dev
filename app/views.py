from flask import Flask, redirect, url_for, render_template, flash, g
from app import app, lm, db
from flask.ext.login import login_user, logout_user, login_required, current_user
from .facebook import OAuthSignIn
from .models import User
from .forms import EditForm

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    return render_template('index.html', title='Home', user=user)

@app.route('/login')
def login():
    return render_template('login.html', title='Sign In')

@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))

    return render_template('user.html',
                           user=user)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))