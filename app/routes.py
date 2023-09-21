from bson import ObjectId
from flask import render_template, flash, redirect, url_for, request, g
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from datetime import datetime
from flask_babel import _, get_locale



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        
        db.users.update_one(
            {'_id': current_user._id},
            {
                '$set': {
                    'last_seen': current_user.last_seen,
                    'username': current_user.username,
                    'about_me': current_user.about_me
                }
            }
        )


@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():

        user_data = db.users.find_one({'username': form.username.data})

        if user_data and User(user_data).check_password(form.password.data):
            user = User(user_data)
            login_user(user, remember=form.remember_me.data)

            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')  

            return redirect(next_page)

        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html', title=('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()

    if form.validate_on_submit():

        existing_user = User.find_by_username(form.username.data)
        if existing_user:
            flash('Username or email already exists. Please choose another.')
            return redirect(url_for('register'))
        

        new_user_data = {
            '_id': str(ObjectId()),
            'username': form.username.data,
            'email': form.email.data,
            'password_hash': None,
        }

        new_user = User(new_user_data)
        new_user.set_password(form.password.data)
        new_user.save()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.find_by_username(username)
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]

    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        
        db.users.update_one(
            {'_id': current_user._id},
            {
                '$set': {
                    'username': current_user.username,
                    'about_me': current_user.about_me
                }
            }
        )

        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)