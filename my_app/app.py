from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import CSRFProtect  # Import CSRFProtect
from forms import RegistrationForm, LoginForm
from models import db, User, Reference
from flask_limiter import Limiter  # Import Flask-Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from models import db, User, Reference
import bleach
import validators
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_fallback_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db.init_app(app)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize CSRF protection
csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def home():
    # Fetch all references marked as public
    public_references = Reference.query.filter_by(public=True).all()
    return render_template('home.html', references=public_references)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Apply rate limit to prevent rapid brute-force attempts
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # Check if the account is currently locked
        if user and user.lockout_until and user.lockout_until > datetime.now():
            flash("Account is locked. Try again later.", "danger")
            return redirect(url_for('login'))

        # Verify password if the user exists and is not locked
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Reset failed attempts and lockout on successful login
            user.failed_attempts = 0
            user.lockout_until = None
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            # Increment failed attempts on unsuccessful login
            if user:
                user.failed_attempts += 1
                if user.failed_attempts >= 5:  # Lock account after 5 failed attempts
                    user.lockout_until = datetime.now() + timedelta(minutes=15)  # Lock for 15 minutes
                    flash("Too many failed attempts. Account locked for 15 minutes.", "danger")
                else:
                    flash("Login unsuccessful. Check username and password.", "danger")
                db.session.commit()
            else:
                flash("Login unsuccessful. Check username and password.", "danger")

    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    references = Reference.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', references=references)

@app.route('/add_reference', methods=['GET', 'POST'])
@login_required
def add_reference():
    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        url = bleach.clean(request.form['url'])
        public = 'public' in request.form
        reference = Reference(title=title, url=url, public=public, user_id=current_user.id)
        db.session.add(reference)
        db.session.commit()
        if not validators.url(request.form['url']):
            flash('Invalid URL format', 'danger')
            return redirect(url_for('add_reference'))
        else:
            flash('Reference added successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('add_reference.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.errorhandler(400)
def csrf_error(error):
    return render_template('csrf_error.html'), 400

if __name__ == '__main__':
    app.run(debug=False)
