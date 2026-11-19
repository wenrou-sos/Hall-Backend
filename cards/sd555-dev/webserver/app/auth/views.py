from flask import render_template, redirect, request, url_for, flash,session
from . import auth
from .forms import LoginForm
# from app.models import Admin,Adminlog
from flask_login import login_user, logout_user, login_required,current_user
from flask import request
import json
from app import login_manager




@auth.route('/login1', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        try:
            user = Admin.get(Admin.username == form.username.data)
            admineventlog(request,user.username, 'login deny' )
            Restore_Admin_permission(user)
            if admin_permission().get_permit('status') ==0 or admin_permission().get_permit('groupstatus')==0:
                flash('Permission Deny')
                admineventlog(request,user.username,'login deny')
                return render_template('auth/login.html',form=form)
            #print(user.status)
            if user.verify_password(form.password.data):
                login_user(user, form.rememberme.data)
                admineventlog(request,user.username,'login success')
                session.permanent = True
                return redirect(request.args.get('next') or url_for('main.root'))
            else:
                flash('Name or Password error !')
        except:
            flash('Name or Password error !')
    return render_template('auth/login.html', form=form)


@auth.route('/logout1')
@login_required
def logout():
    admineventlog(request,current_user.username,'logout success')
    logout_user()
    flash('Already Log-Out')
    return redirect(url_for('auth.login'))
