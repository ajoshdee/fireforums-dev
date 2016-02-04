from flask import Flask, redirect, url_for, render_template, flash, g
from app import app, lm, db
from flask.ext.login import login_user, logout_user, login_required, current_user
from .facebook import OAuthSignIn
from datetime import datetime
from .models import User, Post, Comment, save, delete
from .forms import EditForm, PostForm, CommentForm, EditPostForm
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
    pform = PostForm()
    eform = EditPostForm()
    if pform.validate_on_submit():
        post = Post(title=pform.post.data, date_created=datetime.utcnow(), author=g.user)
        save(post)
        flash('Your post is now live!')
        return redirect(url_for('index'))
    if g.user.sort_prefs == 'new':
        posts = Post.query.order_by(Post.date_created.desc()).paginate(page, POSTS_PER_PAGE, False)
    else:
        posts = Post.query.order_by(Post.vote_count.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html', 
                            title='Home', 
                            pform=pform,
                            eform=eform, 
                            posts=posts)

@app.route('/hot')
def hot():
    g.user.sort_prefs = 'hot'
    save(g.user)
    flash('Your changes have been saved.')
    return redirect(url_for('index'))

@app.route('/new')
def new():
    g.user.sort_prefs = 'new'
    save(g.user)
    flash('Your changes have been saved.')
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html', title='Sign In')

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    eform = EditPostForm()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))

    posts = user.posts.order_by(Post.date_created.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html',
                           user=user, posts=posts, eform=eform)

@app.route('/comments/<title>', methods=['GET', 'POST'])
@app.route('/comments/<title>/<int:page>', methods=['GET', 'POST'])
@login_required
def comments(title, page=1):
    thread = Post.query.filter_by(title=title).first()
    cform = CommentForm()
    eform = EditPostForm()

    if thread == None:
        flash('Thread %s not found.' % title)
        return redirect(url_for('index'))


    if cform.validate_on_submit():
        comment = Comment(body=cform.comment.data, date_created=datetime.utcnow(), owner=g.user, poster=thread)
        save(comment)

        flash('Your post is now live!')
        return redirect(url_for('comments', title=title))

    comments = thread.comments.paginate(page, POSTS_PER_PAGE, False)
    return render_template('thread.html',
                            title=thread.title,
                            thread=thread,
                            cform = cform,
                            eform = eform,
                            comments=comments)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        save(g.user)
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)

@app.route('/edit/post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    pform = PostForm()
    eform = EditPostForm()
    post = Post.query.get(id)
    
    if post is None:
        flash('Post not found.')
        return redirect(url_for('index'))
    if post.author.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))

    if eform.validate_on_submit():
        post.title = eform.body.data
        db.session.add(post)
        db.session.commit()
        flash('Your changes have been saved.')
        print("success")
        return redirect(url_for('index'))
    else:
        eform.body.data = post.title
        print("error")


    return redirect(url_for('index'))

@app.route('/edit/comment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_comment(id):
    cform = CommentForm()
    eform = EditPostForm()
    comment = Comment.query.get(id)
    
    if comment is None:
        flash('Comment not found.')
        return redirect(url_for('comments', title=comment.poster.title))
    if comment.owner.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('comments', title=comment.poster.title))

    if eform.validate_on_submit():
        comment.body = eform.body.data
        db.session.add(comment)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('comments', title=comment.poster.title))
    else:
        eform.body.data = comment.body


    return redirect(url_for('comments', title=comment.poster.title))

@app.route('/delete/post/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post not found.')
        return redirect(url_for('index'))
    if post.author.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))
    delete(post)
    flash('Your post has been deleted.')
    return redirect(url_for('index'))

@app.route('/delete/comment/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get(id)
    title = comment.poster.title
    
    if comment is None:
        flash('Comment not found.')
        return redirect(url_for('comments', title=title))
    if comment.owner.id != g.user.id:
        flash('You cannot delete this post.')
        return redirect(url_for('comments', title=title))
    delete(comment)
    flash('Your comment has been deleted.')
    return redirect(url_for('comments', title=title))

@app.route('/upvote/<title>')
@login_required
def upvote(title):
    post = Post.query.filter_by(title=title).first()
    if post is None:
        flash('Post %s not found.' % title)
        return redirect(url_for('index'))

    u = g.user.upvote(post)
    if u is None:
        flash('Cannot upvote ' + title + '.')
        return redirect(url_for('index'))
    save(u)

    post.vote_count =  post.upvotes.count()
    save(post)
    flash('You have now upvoted ' + title + '!')
    return redirect(url_for('index'))

@app.route('/downvote/<title>')
@login_required
def downvote(title):
    post = Post.query.filter_by(title=title).first()
    if post is None:
        flash('Post %s not found.' % title)
        return redirect(url_for('index'))

    u = g.user.downvote(post)
    if u is None:
        flash('Cannot downvote ' + title + '.')
        return redirect(url_for('index'))
    save(u)

    post.vote_count =  post.upvotes.count()
    save(post)
    flash('You have downvoted ' + title + '.')
    return redirect(url_for('index'))

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
        save(user)
    login_user(user, True)
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500