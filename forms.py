from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField,EmailField
from wtforms.validators import DataRequired, URL,InputRequired,Email,Length
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    email= EmailField("Email", validators=[InputRequired(),Email()])
    password=PasswordField("Password",validators=[InputRequired(),Length(min=6)])
    name=StringField("Name",validators=[InputRequired()])
    submit=SubmitField("Sign Up")

class LoginForm(FlaskForm):
    email= EmailField("Email", validators=[InputRequired(),Email()])
    password=PasswordField("Password",validators=[InputRequired(),Length(min=6)])
    submit=SubmitField("Sign In")

class CommentForm(FlaskForm):
    comment = CKEditorField("Comment")
    submit=SubmitField("Submit")