from flask import Flask, request, render_template, redirect, url_for, flash, send_file
import sqlalchemy.exc
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from flask_bootstrap import Bootstrap
from flask_gravatar import Gravatar
from functools import wraps
import smtplib
import os


MY_EMAIL = os.environ.get('my_email')
MY_PASSWORD = os.environ.get('email_password')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('secret_key')
Bootstrap(app)
ckeditor = CKEditor(app)

# Connect DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('database_uri')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup Gravitar

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# Setup Login Manager

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create Flask Forms
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    snippet = StringField("Snippet", validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CreateProject(FlaskForm):
    project_name = StringField("Project Name", validators=[DataRequired()])
    project_type = StringField("Project Type", validators=[DataRequired()])
    client = StringField("Client Name", validators=[DataRequired()])
    about_client = TextAreaField("About Client", validators=[DataRequired()])
    project_year = IntegerField("Project Year", validators=[DataRequired()])
    about_project = TextAreaField("About Project", validators=[DataRequired()])
    project_description = CKEditorField("Project Descrption", validators=[DataRequired()])
    img_url_1 = StringField("First Image Url", validators=[DataRequired(), URL()])
    img_url_2 = StringField("Second Image Url", validators=[DataRequired(), URL()])
    img_url_3 = StringField("Third Image Url", validators=[DataRequired(), URL()])
    img_url_4 = StringField("Fourth Image Url", validators=[DataRequired(), URL()])
    img_url_5 = StringField("Project Preview Url", validators=[DataRequired(), URL()])
    img_url_6 = StringField("Add a # here", validators=[DataRequired(), URL()])
    submit = SubmitField("Add Project")

# Configure Tables

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False, unique=True)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)

    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='comment_author')


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    author = relationship('User', back_populates='posts')

    title = db.Column(db.String(250), unique=True, nullable=False)
    snippet = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(250), nullable=False)

    comments = relationship('Comment', back_populates='parent_post')


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(250), unique=True, nullable=False)
    project_type = db.Column(db.String(250), nullable=False)
    client = db.Column(db.String(250), nullable=False)
    about_client = db.Column(db.Text, nullable=False)
    about_project = db.Column(db.Text, nullable=False)
    project_year = db.Column(db.Integer, nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    img_url_1 = db.Column(db.String(250), nullable=False)
    img_url_2 = db.Column(db.String(250), nullable=False)
    img_url_3 = db.Column(db.String(250), nullable=False)
    img_url_4 = db.Column(db.String(250), nullable=False)
    img_url_5 = db.Column(db.String(250), nullable=False)
    img_url_6 = db.Column(db.String(250), nullable=False)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer,  db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return render_template('unauthorised.html')
        if current_user.id != 1:
            return render_template('unauthorised.html')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET'])
def home():
    # project_name = Project.query.all()[::-1][0].project_name.upper() or ''
    project_name = 'CED UDUS ERP'
    return render_template('index.html', project_name=project_name)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        try:
            new_user = User(email=request.form.get('email'),
                            name=request.form.get('name'),
                            password=generate_password_hash(password=request.form.get('password'), method='pbkdf2:sha256', salt_length=8))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
        except sqlalchemy.exc.IntegrityError:
            flash("Email already exist please login to continue")
            return redirect(url_for('login'))
        return redirect(url_for('blog_home'))
    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if not user:
            flash("Invalid Credentials")
        elif not check_password_hash(user.password, request.form.get('password')):
            flash("Invalid credentials")
        else:
            login_user(user)
            return redirect(url_for('blog_home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('blog_home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/works', methods=['GET'])
def works():
    projects = Project.query.all()[::-1]
    return render_template('works.html', projects=projects)


@app.route('/work-details')
def work_details():
    project_id = request.args.get('project_id')
    requested_project = Project.query.get(project_id)
    if requested_project is None:
        requested_project = Project.query.get(13)
    return render_template('work-detail.html', project=requested_project)

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['POST', 'GET'])
def contact():

    if request.method == 'POST':
        with smtplib.SMTP_SSL('smtp.gmail.com') as connection:
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(from_addr=MY_EMAIL,
                                to_addrs='binyaminbgod@gmail.com',
                                msg=f'Subject:{request.form.get("subject")}\n\n'
                                    f'Name: {request.form.get("name")}\n'
                                    f'Email: {request.form.get("email")}\n'
                                    f'Message: {request.form.get("message")}')
            flash('Message Sent Successfully, Thank you!')
            return render_template('contact-me.html')
    return render_template('contact-me.html')

@app.route('/credentials')
def credentials():
    return render_template('credentials.html')

@app.route('/blog-home')
def blog_home():
    posts = BlogPost.query.all()
    return render_template('blog-posts.html', all_posts=posts)

@app.route('/blog-post', methods=['POST', 'GET'])
def blog_post():
    post_id = request.args.get('post_id')
    requested_post = BlogPost.query.get(post_id)
    if request.method == 'POST':
        try:


            new_comment = Comment(text=request.form.get('message'),
                                  comment_author=current_user,
                                  parent_post=requested_post)
            db.session.add(new_comment)
            db.session.commit()
        except:
            flash("You need to login to post a comment")
            return redirect(url_for('login'))
    comments_len = len(requested_post.comments)
    return render_template('post.html', post=requested_post, comments_len=comments_len)

@app.route('/new-post', methods=['POST', 'GET'])
@admin_only
def new_post():
    form = CreatePostForm()
    form.submit.render_kw = {'class_': 'theme-btn'}
    if form.validate_on_submit():
        try:
            new_post = BlogPost(title=form.title.data,
                                body=form.body.data,
                                image_url=form.img_url.data,
                                snippet=form.snippet.data,
                                author=current_user,
                                date=date.today().strftime("%B %d, %Y"))
            db.session.add(new_post)
            db.session.commit()
            flash("New Post added successfully")
            return redirect(url_for('blog_home'))
        except sqlalchemy.exc.IntegrityError:
            flash("Post With that name already exist")
    return render_template('new-post.html', form=form)


@app.route('/delete-post', methods=['POST', 'GET'])
@admin_only
def delete_post():
    post_id = request.args.get('post_id')
    requested_post = BlogPost.query.get(post_id)
    db.session.delete(requested_post)
    db.session.commit()
    flash("Post Deleted successfully")
    return redirect(url_for('blog_home'))

@app.route('/add-project', methods=['POST', 'GET'])
@admin_only
def add_project():
    form = CreateProject()
    if form.validate_on_submit():
        new_project = Project(project_name=form.project_name.data,
                              project_type=form.project_type.data,
                              client=form.client.data,
                              about_client=form.about_client.data,
                              about_project=form.about_project.data,
                              project_year=form.project_year.data,
                              project_description=form.project_description.data,
                              img_url_1=form.img_url_1.data,
                              img_url_2=form.img_url_2.data,
                              img_url_3=form.img_url_3.data,
                              img_url_4=form.img_url_4.data,
                              img_url_5=form.img_url_5.data,
                              img_url_6=form.img_url_6.data)
        db.session.add(new_project)
        db.session.commit()
        flash("New Project Added Successfully")
        return redirect(url_for('works'))
    return render_template('add-project.html', form=form)


@app.route('/delete-project')
@admin_only
def delete_project():
    project_id = request.args.get('project_id')
    print(project_id)
    requested_project = Project.query.get(project_id)
    print(requested_project)
    db.session.delete(requested_project)
    db.session.commit()
    flash("Project deleted Successfully")
    return redirect(url_for('works'))


@app.route('/404-page')
def unauthorised_page():
    return render_template('404-page.html')



if __name__ == '__main__':
    app.run(debug=False)