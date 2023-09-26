from bson import ObjectId
from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():

        user_data = db.users.find_one({'username': form.username.data})

        if user_data and User(user_data).check_password(form.password.data):
            user = User(user_data)
            login_user(user, remember=form.remember_me.data)

            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')  

            return redirect(next_page)

        flash(_('Invalid username or password'))
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html', title=_('Sign In'), form=form)



@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()

    if form.validate_on_submit():

        existing_user = User.find_by_username(form.username.data)
        if existing_user:
            flash(_('Username or email already exists. Please choose another.'))
            return redirect(url_for('auth.register'))
        
        new_user_data = {
            '_id': str(ObjectId()),
            'username': form.username.data,
            'email': form.email.data,
            'password_hash': None,
        }

        new_user = User(new_user_data)
        new_user.set_password(form.password.data)
        new_user.save()
        
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title=_('Register'), form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        email_user = User.find_by_email(form.email.data)

        if email_user:
            send_password_reset_email(email_user)
            flash(_('Check your email for the instructions to reset your password'))
        else:
            flash(_('This user not exists'))

        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user_data = User.verify_reset_password_token(token)

    if not user_data:
        flash(_('Invalid or expired token. Please request a new password reset link.'))
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user_data.set_password(form.password.data)
        user_data.update()
        flash(_('Your password has been reset.'))

        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)