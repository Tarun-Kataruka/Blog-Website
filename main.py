#--------------------------------------------------Imports------------------------------------------------------
from flask import Flask, render_template, redirect, url_for,request,flash,abort
from functools import wraps
from flask_bootstrap import Bootstrap4
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager,current_user, logout_user
from forms import CreatePostForm,RegisterUserForm,LoginUserForm,DeleteForm,CommentsForm
import os
import random


#--------------------------------------------------Initialization------------------------------------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///posts2.db"
ckeditor = CKEditor(app)
bootstrap = Bootstrap4(app)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)
# Secret Things 
app.secret_key = "aygwedtqawueiquwy8722"



#--------------------------------------------------Tables------------------------------------------------------
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id=db.Column(db.Integer)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(250),nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password=db.Column(db.String(250),nullable=False)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    commenter_name=db.Column(db.String(250),nullable=False)
    commenter_email=db.Column(db.String(250),nullable=False)
    comment_post_id=db.Column(db.Integer,nullable=False)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)        
    return decorated_function


#--------------------------------------------------Main Routes------------------------------------------------------
@app.route("/")
def home():
    db.create_all()
    data=db.session.query(BlogPost).order_by(BlogPost.id.desc())
    print(data)
    return render_template("index.html",blog_data=data,logged_in=current_user.is_authenticated)


@app.route('/admin_dashboard')
@admin_only
def admin_page():
    blog_data=db.session.query(BlogPost).order_by(BlogPost.id)
    user_data=db.session.query(User).order_by(User.id)
    comments_data=db.session.query(Comment).order_by(Comment.comment_post_id)
    return render_template("admindashboard.html",blog_data=blog_data,user_data=user_data,comments_data=comments_data)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#--------------------------------------------------User Routes------------------------------------------------------

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegisterUserForm()
    if request.method == 'POST':
        if form.login.data:  
            return redirect(url_for('login'))
        else:
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                flash('Username Already Exists.Please Login Instead')
                return redirect(url_for('login')) 
            else:
                hashed_password= generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
                new_user=User(
                    name=form.name.data,
                    email=form.email.data,
                    password=hashed_password
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('login',logged_in=current_user.is_authenticated))
    return render_template("register.html",form=form)

@app.route('/login',methods=["GET","POST"])
def login():
    form=LoginUserForm()
    if request.method == 'POST':
        if form.register.data:  
            return redirect(url_for('register'))
        else:
            email=form.email.data
            password=form.password.data
            user = User.query.filter_by(email=email).first()
            if not user:
                flash('Invalid Email')
                return redirect(url_for('login'))
            else:
                if check_password_hash(user.password, password):
                    login_user(user)
                    return redirect(url_for('home'))
                else:
                    flash('Invalid Password')
                    return redirect(url_for('login'))        
    return render_template("login.html",form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

#--------------------------------------------------Post Routes------------------------------------------------------
@app.route("/post/<num>",methods=["GET","POST"])
def render_post(num):
    x= int(num)
    form=CommentsForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        new_comment=Comment(
            text=form.comment.data,
            commenter_name=current_user.name,
            commenter_email=current_user.email,
            comment_post_id=x
        )
        db.session.add(new_comment)
        db.session.commit()
    form.comment.data=""
    post=BlogPost.query.filter_by(id=x).first()
    comments=db.session.query(Comment).all()
    first_post=db.session.query(BlogPost).order_by(BlogPost.id.desc()).first()
    last_post=db.session.query(BlogPost).order_by(BlogPost.id).first()
    list_of_posts=db.session.query(BlogPost).all()
    list_of_posts.remove(post)
    recommended_posts=[]
    for i in range(3):
        random_post=random.choice(list_of_posts)
        recommended_posts.append(random_post)
        list_of_posts.remove(random_post)
    url=post.img_url
    return render_template("post.html",post=post,url=url,logged_in=current_user.is_authenticated,form=form,comments=comments,first_post=first_post,last_post=last_post,recommended_posts=recommended_posts)

@app.route("/post/<num>",methods=["GET","POST"])
def next_post(num):
    pass


@app.route("/post/<num>",methods=["GET","POST"])
def previous_post(num):
    pass


@app.route("/editpost/?id=<num>",methods=["POST","GET"])
def edit_post(num):
    x=int(num)
    form=CommentsForm()
    post=BlogPost.query.filter_by(id=x).first()
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    elif current_user.id==post.author_id or current_user.id==1:
        edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
        )
        if edit_form.validate_on_submit():
            post.title=edit_form.title.data
            post.subtitle=edit_form.subtitle.data
            post.img_url=edit_form.img_url.data
            post.name=edit_form.author.data
            post.body=edit_form.body.data
            db.session.commit()
            url=post.img_url
            first_post=db.session.query(BlogPost).order_by(BlogPost.id.desc()).first()
            last_post=db.session.query(BlogPost).order_by(BlogPost.id).first()
            return render_template("post.html",post=post,url=url,logged_in=current_user.is_authenticated,form=form,first_post=first_post,last_post=last_post)
    else:
        return abort(403)
    return render_template('createpost.html',form=edit_form,editer=True,logged_in=current_user.is_authenticated)

@app.route("/createpost",methods=["POST","GET"])
def create_post():
    form = CreatePostForm()
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
        
    if form.validate_on_submit():
        last_post=db.session.query(BlogPost).order_by(BlogPost.id.desc()).first()
        date = dt.today()
        x=(str(date).split()[0].split("-"))
        date_today=f"{x[2]}-{x[1]}-{x[0]}"
        new_post=BlogPost(id=last_post.id +1,
        body=form.body.data,
        title=form.title.data,
        subtitle=form.subtitle.data,
        author=form.author.data,
        img_url=form.img_url.data,
        date=date_today,
        author_id=current_user.id
    )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home',logged_in=current_user.is_authenticated)) 
    return render_template('createpost.html',form=form,logged_in=current_user.is_authenticated)
    
@app.route('/delete_post/<num>',methods=["GET","POST"])
@admin_only
def delete_post(num):
    x=int(num)
    form=DeleteForm()
    if form.validate_on_submit():
        post=BlogPost.query.filter_by(id=x).first()
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for("home",logged_in=current_user.is_authenticated))
    return render_template("delete.html",form=form)

@app.route('/delete_comment/<num>',methods=["GET","POST"])
@admin_only
def delete_comment(num):
    x=int(num)
    comment = Comment.query.filter_by(id=x).first()
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for("home",logged_in=current_user.is_authenticated))

    
#--------------------------------------------------Other Routes------------------------------------------------------
@app.route("/about")
def open_about_page():
    return render_template("about.html",logged_in=current_user.is_authenticated)

@app.route('/contact', methods=['GET', 'POST'])
def open_contact_page():
    if request.method == "POST":
        return render_template("contact.html", message="Successfully sent your message.",logged_in=current_user.is_authenticated)
    return render_template("contact.html", message="Contact Akash!",logged_in=current_user.is_authenticated)
if __name__=="__main__":
    app.run(debug=True)
# if __name__=="__main__":
#     app.run(debug=True)
