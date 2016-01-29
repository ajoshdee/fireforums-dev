from flask import Flask, redirect, url_for, render_template, flash, g
from app import app, lm, db
from flask.ext.login import login_user, logout_user, login_required, current_user
from .facebook import OAuthSignIn
from datetime import datetime
from .models import User, Post, Comment
from .forms import EditForm, PostForm, CommentForm
from instance.config import POSTS_PER_PAGE

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.post.data, date_created=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = Post.query.order_by(Post.date_created.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html', 
                            title='Home', 
                            form=form, 
                            posts=posts)

@app.route('/login')
def login():
    return render_template('login.html', title='Sign In')

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))

    posts = user.posts.order_by(Post.date_created.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html',
                           user=user, posts=posts)

@app.route('/comments/<title>', methods=['GET', 'POST'])
@app.route('/comments/<title>/<int:page>', methods=['GET', 'POST'])
@login_required
def comments(title, page=1):
    thread = Post.query.filter_by(title=title).first()
    form = CommentForm()

    if thread == None:
        flash('Thread %s not found.' % title)
        return redirect(url_for('index'))


    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, date_created=datetime.utcnow(), owner=g.user, poster=thread)
        db.session.add(comment)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('comments', title=title))

    comments = thread.comments.paginate(page, POSTS_PER_PAGE, False)
    return render_template('thread.html',
                            title=thread.title,
                            thread=thread,
                            form = form,
                            comments=comments)

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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500