from bson import ObjectId
from flask import render_template, flash, redirect, url_for, request, g
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        
        db.users.update_one(
            {'_id': ObjectId(current_user._id)},
            {
                '$set': {
                    'last_seen': current_user.last_seen,
                    'username': current_user.username,
                    'about_me': current_user.about_me
                }
            }
        )


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    post_collection = db.posts
    if form.validate_on_submit():
        post_data = {
            'body': form.post.data,
            'author_id': current_user._id,  
            'timestamp': datetime.utcnow(),
        }
        post_collection.insert_one(post_data)
        flash(('Your post is now live!'))
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {
            "$unwind": "$user"
        },
        {
            "$sort": {"timestamp": -1}
        },
        {
            "$skip": (page - 1) * app.config['POSTS_PER_PAGE']
        },
        {
            "$limit": app.config['POSTS_PER_PAGE']
        }
    ]

    posts = list(post_collection.aggregate(pipeline))

    next_url = url_for('index', page=page + 1) if len(posts) == app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('index', page=page - 1) if page > 1 else None
    
    return render_template("index.html", title='Home', form=form, posts=posts, next_url=next_url, prev_url=prev_url, user=current_user)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {
            "$unwind": "$user"
        },
        {
            "$sort": {"timestamp": -1}
        },
        {
            "$skip": (page - 1) * app.config['POSTS_PER_PAGE']
        },
        {
            "$limit": app.config['POSTS_PER_PAGE']
        }
    ]
    
    posts = list(db.posts.aggregate(pipeline))
    
    total_posts = db.posts.count_documents({})
    
    next_url = url_for('explore', page=page + 1) if total_posts > page * app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('explore', page=page - 1) if page > 1 else None

    return render_template('index.html', title=('Explore'), posts=posts, next_url=next_url, prev_url=prev_url, user=current_user)


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
    page = request.args.get('page', 1, type=int)
    
    user_posts_cursor = db.posts.find({'user_id': ObjectId(user._id)}).sort('timestamp', -1)

    
    total_posts = db.posts.count_documents({'user_id':ObjectId(user._id)})
    
    posts = user_posts_cursor.skip((page - 1) * app.config['POSTS_PER_PAGE']).limit(app.config['POSTS_PER_PAGE'])
    
    next_url = url_for('user', username=username, page=page + 1) if total_posts > page * app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('user', username=username, page=page - 1) if page > 1 else None
    
    form = EmptyForm()
    
    return render_template('user.html', user=user, posts=posts, next_url=next_url, prev_url=prev_url, form=form)


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


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()

    if form.validate_on_submit():
        user = User.find_by_username(username)

        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        

        current_user_id_str = str(current_user.get_id())
        user_id_str = str(user.get_id())
        if user_id_str not in current_user.following:
            current_user.follow(user)
            user.followers.append(current_user_id_str)
            user.update()
            flash(('You are following {}!'.format(username)))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.find_by_username(username)
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        
        current_user_id_str = str(current_user.get_id())
        user_id_str = str(user.get_id())

        if user_id_str in current_user.following:
            current_user.unfollow(user)
            user.followers.remove(current_user_id_str)
            user.update()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))