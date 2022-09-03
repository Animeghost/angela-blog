import imp
from flask import Flask, render_template, redirect, url_for, flash,g,request,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI']=os.environ.get("DATABASE_URL",'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Base=declarative_base()

login_manager=LoginManager()
login_manager.init_app(app)
##CONFIGURE TABLES


class User(UserMixin,db.Model,Base):
    __tablename__ ="user"
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(250), nullable=False)
    email=db.Column(db.String(250), unique=True,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    posts=relationship("BlogPost",back_populates='author')#posts #parent of blogpost fills author field
    comments=relationship("Comments",back_populates='author')#comments

    def __repr__(self):
        return f'<User {self.name}>'

    def check_password(self,password):
        self.password_hash=generate_password_hash(password=password,method="pbkdf2:sha256",salt_length=16)
        return check_password_hash(pwhash=self.password_hash,password= password)

class BlogPost(db.Model,Base):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author =relationship("User",back_populates='posts')#author is a user object
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id=db.Column(db.Integer,db.ForeignKey('user.id'))#get user id
    comments=relationship("Comments",back_populates='parent_post')#parent of comment class 

    def __repr__(self):
        return f'<User {self.author}>'

class Comments(db.Model,Base):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author =relationship("User",back_populates='comments')#gets author user object
    author_id=db.Column(db.Integer,db.ForeignKey('user.id'))#gets user_id
    parent_post=relationship("BlogPost",back_populates='comments')#gets blog_post objects
    post_id=db.Column(db.Integer,db.ForeignKey('blog_posts.id'))#gets blog_post id
    text=db.Column(db.Text)#gets comment text
    date = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<User {self.author}>'
db.create_all()

def admin_only(funct):
    @wraps(funct)
    def wrapper(*args, **kwargs) :
        if current_user.id!=1: #the problem with your code was getting the id  
            return abort(403)
        return funct(*args, **kwargs)        
    return wrapper


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register',methods=['POST','GET'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        name=form.name.data
        email=form.email.data
        password=form.password.data
        passwor= generate_password_hash(password=password,method= "pbkdf2:sha256", salt_length= 16)
        
        user=User(name=name,email=email,password=passwor)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html",form=form)


@app.route('/login',methods=['POST','GET'])
def login():
    form=LoginForm()
    error=None
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
        user=User.query.filter_by(email=email).first()
        
        if user != None:        
            if check_password_hash(pwhash=user.password,password=password) == True:        
                flash('log in approved')
                login_user(user=user)            
                return redirect(url_for('get_all_posts'))
            else:
                error="That's the wrong password"
        else:
            error = "There's no such email registered"  
    return render_template("login.html",error=error,form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['POST','GET'])
def show_post(post_id):
    comment=CommentForm()
    error=None
    requested_post = BlogPost.query.get(post_id)
    comments= Comments.query.filter_by(post_id=post_id).all()
    if comment.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comments(
                text=comment.comment.data,
                author_id=current_user.id,
                post_id=post_id,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_comment)
            db.session.commit()
            
            return redirect(url_for('show_post',post_id=post_id))
        else:
            error="Login to post a comment"
            flash(message='Login to post a comment',category='error')
            
    return render_template("post.html", post=requested_post,form=comment,comment=comments,error=error)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post",methods=['POST','GET'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>",methods=['POST','GET'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        # author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        # post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>",methods=['POST','GET'])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
