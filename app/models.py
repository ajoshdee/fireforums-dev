from app import db
from flask.ext.login import UserMixin
from hashlib import md5

upvotes = db.Table('upvotes',
    db.Column('thread_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'))
)

def save(model):
    db.session.add(model)
    db.session.commit()
    
def delete(model):
    db.session.delete(model)
    db.session.commit()

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    date_created = db.Column(db.DateTime)
    vote_count = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='poster', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Post %r>' % (self.date_created)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(64), nullable=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='owner', lazy='dynamic')
    about_me = db.Column(db.String(140))
    sort_prefs = db.Column(db.String(3), default='new')
    liked = db.relationship('Post',
                            secondary=upvotes,
                            primaryjoin=(upvotes.c.follower_id == id),
                            secondaryjoin=(upvotes.c.thread_id == Post.id),
                            backref=db.backref('upvotes', lazy='dynamic'),
                            lazy='dynamic')


    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

    def upvote(self,post):
        if not self.is_liked(post):
            self.liked.append(post)
            return self
        else:
            return print('hello')

    def downvote(self, post):
        if self.is_liked(post):
            self.liked.remove(post)
            return self

    def __repr__(self):
        return '<User %r>' % (self.nickname)

    def is_liked(self, post):
        return self.liked.filter(upvotes.c.thread_id == post.id).count() > 0

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    date_created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    thread_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        return '<Comment %r>' % (self.date_created)

