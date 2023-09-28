from datetime import datetime
from bson import ObjectId
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post
from app.main import bp


@bp.before_request
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
        g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    post_collection = db.posts
    if form.validate_on_submit():
        post_data ={
            'body': form.post.data,
            'user_id': current_user._id,  
            'timestamp': datetime.utcnow(),
            '__searchable__': form.post.data
        }
        post_collection.insert_one(post_data)
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
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
            "$skip": (page - 1) * current_app.config['POSTS_PER_PAGE']
        },
        {
            "$limit": current_app.config['POSTS_PER_PAGE']
        }
    ]

    posts = list(post_collection.aggregate(pipeline))
    
    next_url = url_for('main.index', page=page + 1) if len(posts) == current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.index', page=page - 1) if page > 1 else None

    if len(posts) == 0:
        flash("Nadie ha posteado nada todavía")
    
    return render_template("index.html", title=_('Home'), form=form, posts=posts, next_url=next_url, prev_url=prev_url, 
                           user=current_user) #en miguel no té lo de user


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
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
            "$skip": (page - 1) * current_app.config['POSTS_PER_PAGE']
        },
        {
            "$limit": current_app.config['POSTS_PER_PAGE']
        }
    ]
    
    posts = list(db.posts.aggregate(pipeline))
    
    total_posts = db.posts.count_documents({})
    
    next_url = url_for('main.explore', page=page + 1) if total_posts > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.explore', page=page - 1) if page > 1 else None

    return render_template('index.html', title=_('Explore'), posts=posts, next_url=next_url, prev_url=prev_url, 
                           user=current_user)#en miguel no té lo de user


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.find_by_username(username)

    page = request.args.get('page', 1, type=int)
    
    pipeline = [
        {
            "$match": {
                "user_id": user._id
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
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
            "$skip": (page - 1) * current_app.config['POSTS_PER_PAGE']
        },
        {
            "$limit": current_app.config['POSTS_PER_PAGE']
        }
    ]

    posts = list(db.posts.aggregate(pipeline))
    total_posts = db.posts.count_documents({'user_id': user._id})
    
    next_url = url_for('main.user', username=username, page=page + 1) if total_posts > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.user', username=username, page=page - 1) if page > 1 else None
    
    form = EmptyForm()
    
    return render_template('user.html', user=user, posts=posts, next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
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

        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()

    if form.validate_on_submit():
        user = User.find_by_username(username)

        if user is None:
            flash(_('User {} not found.'.format(username)))
            return redirect(url_for('main.index'))
        
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        

        current_user_id_str = str(current_user.get_id())
        user_id_str = str(user.get_id())

        if user_id_str not in current_user.following:
            current_user.follow(user)
            user.followers.append(current_user_id_str)
            user.update()
            flash(_('You are following {}!'.format(username)))

        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()

    if form.validate_on_submit():
        user = User.find_by_username(username)

        if user is None:
            flash(_('User {} not found.'.format(username)))
            return redirect(url_for('main.index'))
        
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        
        current_user_id_str = str(current_user.get_id())
        user_id_str = str(user.get_id())

        if user_id_str in current_user.following:
            current_user.unfollow(user)
            user.followers.remove(current_user_id_str)
            user.update()

        flash(_('You are not following {}.'.format(username)))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))
    

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.find_by_username(username)
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)