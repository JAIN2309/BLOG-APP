import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from models import db, User, Blog
from forms import LoginForm, BlogForm, RegisterForm
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Create tables before the first request (only once)
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Define the home route (to avoid "BuildError")
@app.route("/")
def home():
    blogs = Blog.query.order_by(Blog.date_posted.desc()).all()
    return render_template("home.html", blogs=blogs)

# Define the registration route
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the username or email already exists
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("register"))
        email = User.query.filter_by(email=form.email.data).first()
        if email:
            flash("Email already registered. Please use a different one.", "danger")
            return redirect(url_for("register"))
        
        # Create a new user and hash the password
        hashed_password = generate_password_hash(form.password.data,method='pbkdf2:sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        
        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html", form=form)
from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):  # Use check_password_hash
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard" if user.is_admin else "user_dashboard"))
        flash("Invalid credentials!", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out.", "info")
    return redirect(url_for("home"))

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for("home"))
    blogs = Blog.query.all()
    return render_template("admin.html", blogs=blogs)

@app.route("/user/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    form = BlogForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        blog = Blog(title=form.title.data, content=form.content.data, image=filename, user_id=current_user.id)
        db.session.add(blog)
        db.session.commit()
        flash("Blog created successfully!", "success")
        return redirect(url_for("user_dashboard"))
    user_blogs = Blog.query.filter_by(user_id=current_user.id).all()
    return render_template("user_dashboard.html", blogs=user_blogs, form=form)

@app.route("/blog/<int:blog_id>")
def blog_detail(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template("blog_detail.html", blog=blog)

@app.route("/blog/edit/<int:blog_id>", methods=["GET", "POST"])
@login_required
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))
    form = BlogForm(obj=blog)
    if form.validate_on_submit():
        blog.title = form.title.data
        blog.content = form.content.data
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            blog.image = filename
        db.session.commit()
        flash("Blog updated successfully!", "success")
        return redirect(url_for("user_dashboard"))
    return render_template("add_blog.html", form=form)

@app.route("/blog/delete/<int:blog_id>", methods=["POST"])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))
    db.session.delete(blog)
    db.session.commit()
    flash("Blog deleted successfully!", "success")
    return redirect(url_for("user_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
