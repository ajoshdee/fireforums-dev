from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length
from app.models import User

class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired(), Length(min=0, max=64)])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        if self.nickname.data != User.make_valid_nickname(self.nickname.data):
            self.nickname.errors.append('This nickname has invalid characters. Please use letters, numbers, dots and underscores only.')
            return False
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True
    
class EditPostForm(Form):
    body = TextAreaField('body', validators=[DataRequired() , Length(min=0, max=140)])

class PostForm(Form):
    post = StringField('post', validators=[DataRequired() , Length(min=0, max=140)])

class CommentForm(Form):
    comment = StringField('body', validators=[DataRequired() , Length(min=0, max=140)])