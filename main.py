from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditor, CKEditorField
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import datetime
import email_senderr
import requests

msg = email_senderr.Email()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)

##SETTING UP LOGGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


##CONFIGURE TABLE
class UserT(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    blog = relationship("Blog", backref="user", cascade="all,delete,save-update")
    comments = relationship("CommentT", backref="user", cascade="all,delete,save-update")


##CONFIGURE TABLE
class Blog(db.Model):
    __tablename__ = "blogs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))
    comments = relationship("CommentT", backref="post", cascade="all,delete,save-update")


# CONFIGURE COMMENTS TABLE
class CommentT(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))
    post_id = db.Column(db.Integer, ForeignKey("blogs.id", ondelete="CASCADE", onupdate="CASCADE"))


##CONFIGURE USER LOADER
@login_manager.user_loader
def load_user(user_id):
    return UserT.query.get(int(user_id))


##WTForm-Register
class User(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


##WTForm-login
class Login(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


##WTForm-comments
class Comment(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("post")


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


@app.route('/')
def get_all_posts():
    posts = db.session.query(Blog).all()
    authors = db.session.query(UserT).all()
    return render_template("index.html", authors=authors, all_posts=posts, logged_in=current_user.is_authenticated,
                           id=current_user)


@app.route("/post/<int:index>", methods=["POST", "GET"])
def show_post(index):
    # date time for the comment
    date = datetime.datetime.now()
    # Get all authors and comments for the current post
    authors = db.session.query(UserT).all()
    comments = db.session.query(CommentT).all()
    # Get the requested post by the index from the URL parameter and populate the form with its data if the request method is POST
    form = Comment()
    posts = db.session.query(Blog).all()
    requested_post = db.session.query(Blog).filter(Blog.id == index).first()
    for blog_post in posts:
        if blog_post.id == index:
            requested_post = blog_post
            if form.validate_on_submit():
                if current_user.is_authenticated:
                    comment = CommentT(text=form.comment.data, user_id=current_user.id, post_id=index)
                    db.session.add(comment)
                    db.session.commit()
                else:
                    flash("Please login to comment on this post.")
                    return redirect(url_for("login"))

    return render_template("post.html", authors=authors, post=requested_post, logged_in=current_user.is_authenticated,
                           id=current_user,
                           form=form,
                           comments=comments,
                           date=date.date(),
                           )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        # phone_num = request.form["number"]
        message = request.form["message"]
        s = msg.message(name, f"email={email}\nmessage={message}")
        return render_template("contact.html", send=s, p=True)
    elif request.method == "GET":
        return render_template('contact.html', p=False)
    else:
        return "error"


@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    if current_user.id == 1:
        requested_post = db.session.query(Blog).filter(Blog.id == post_id).first()
        form = CreatePostForm(
            title=requested_post.title,
            subtitle=requested_post.subtitle,
            author=requested_post.author,
            img_url=requested_post.img_url,
            body=requested_post.body
        )
        if form.validate_on_submit():
            requested_post.title = form.title.data
            requested_post.subtitle = form.subtitle.data
            requested_post.author = form.author.data
            requested_post.img_url = form.img_url.data
            requested_post.body = form.body.data
            db.session.commit()
            return redirect(url_for('get_all_posts'))
        return render_template("make-post.html", form=form, edit=False, logged_in=current_user.is_authenticated)
    else:
        return "<h1 style='color: red; text-align: center '> eurrer: not allowed </h1>"


@app.route("/new-post", methods=["POST", "GET"])
@login_required
def create_post():
    if current_user.id == 1:
        form = CreatePostForm()
        if form.validate_on_submit():
            new_post = Blog(
                title=form.title.data,
                subtitle=form.subtitle.data,
                author=form.author.data,
                img_url=form.img_url.data,
                body=form.body.data,
                date=f"{datetime.datetime.now().year}-{datetime.datetime.now().month}-{datetime.datetime.now().day}"
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('get_all_posts'))
        return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)
    else:
        return "<h1 style='color: red; text-align: center '> eurrer: not allowed </h1>"


@app.route("/delete/<post_id>", methods=["POST", "GET"])
@login_required
def delete(post_id):
    if current_user.id == 1:
        item = db.session.query(Blog).filter(Blog.id == post_id).one_or_none()
        if item:
            db.session.delete(item)
            db.session.commit()
            return redirect(url_for('get_all_posts'))
        else:
            return redirect(url_for('get_all_posts'))
    else:
        return "<h1 style='color: red; text-align: center '> eurrer: not allowed </h1>"


@app.route("/register", methods=["POST", "GET"])
def register():
    form = User()
    if form.validate_on_submit():
        if db.session.query(UserT).filter(UserT.email == form.email.data).first():
            flash("Email already exists")
            return redirect(url_for("login"))
        else:
            new_user = UserT(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data, salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()
            user = db.session.query(UserT).filter(UserT.email == form.email.data).first()
            login_user(user)
            return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = Login()
    if form.validate_on_submit():
        all = db.session.query(UserT).all()
        email = form.email.data
        password = form.password.data
        for user in all:
            if user.email == email and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                if user.email != email:
                    flash("Email does not exist")
                    return redirect(url_for("login"))
                else:
                    flash("Incorrect password")
                    return redirect(url_for("login"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("get_all_posts", logged_in=current_user.is_authenticated))


if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
