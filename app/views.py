"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from app import app
from flask import render_template, request, redirect, url_for, jsonify, g, session, flash
from app import db

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Users, Wish, WishList
from app.forms import LoginForm, SignUpForm, WishForm, WishListForm, SendEmailForm#, UrlForm, EditForm

from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db
from app import lm


from flask import Flask, abort, make_response
import requests
from bs4 import BeautifulSoup
import urlparse
import urllib2
import sys

import smtplib
###
# Routing for your application.
###

@app.before_request
def before_request():
    g.user = current_user
    
@lm.user_loader
def load_user(id):
    return Users.query.get(int(id))

#---Creates new users
@app.route('/api/user/register', methods=['GET','POST'])
def register():
    if request.method == 'POST' and 'User-Agent' not in request.headers:
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        if name and email and password:
            if Users.query.filter_by(email = email).first() is None:
                new_user = Users(name, email, password)
                db.session.add(new_user)
                db.session.commit()
                user = Users.query.filter_by(email = email).first()
                token = user.generate_auth_token(600)  #---visit tutorial on generating this
                return jsonify({'error':'null', 'data':{'token': token.decode('ascii'), 'expires': 600, 'user':{'id': user.id, 'email': user.email, 'name': user.name}, 'message':'success'}})
            if Users.query.filter_by(email = email).first() is not None:
                user = Users.query.filter_by(email = email).first()
                return jsonify({'error': '1', 'data': {'email': user.email}, 'message':'user already exists'})
    form = SignUpForm()
    if request.method == 'POST' and 'User-Agent' in request.headers:
        if form.validate_on_submit():
            email = request.form['email']
            password = generate_password_hash(request.form['password'])
            name = request.form['name']
            new_user = Users(name, email, password)
            db.session.add(new_user)
            db.session.commit()
            # user = Users.query.filter_by(email = email).first()
            # token = user.generate_auth_token(600)  #---visit tutorial on generating this
            return redirect(url_for('login'))
    return render_template(
        'signup.html',
        title='User Signup',
        year=datetime.now().year,
        form=form,
        user=g.user
    )

#---Authenticate and login user
@app.route('/api/user/login', methods=['GET','POST'])
def login():
    if request.method == 'POST' and 'User-Agent' not in request.headers:
        email = request.form['email']
        password = request.form['password']
        if email and password:
            user = Users.query.filter_by(email=email).first()
            if user and user.verify_password(password):
                g.user = user
                token = user.generate_auth_token(600)
                return jsonify({'error':'null', 'data':{'token': token.decode('ascii'), 'expires': 600, 'user':{'id': user.id, 'email': user.email, 'name': user.name}, 'message':'success'}})
            return jsonify({'error': '1', 'data':{}, 'message':'Bad user name or password'})
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == 'POST' and 'User-Agent' in request.headers:
        if form.validate_on_submit():
            uname = request.form['username']
            pword = request.form['password']
            user = Users.query.filter_by(email=uname).first()
            if user is None:
                return redirect(url_for('login'))
            login_user(user)
            return redirect(request.args.get("next") or url_for('wishlist',id=g.user.id))
    
    return render_template(
        'login.html',
        title='User Login',
        year=datetime.now().year,
        form=form,
        user=g.user
    )
        

#---Display home page
@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template(
        'home.html',
        title='Home',
        year=datetime.now().year,
        user=g.user
    )

#---Returns json list of images
@app.route('/api/thumbnail/process', methods=['GET','POST'])
def process():
    if request.method == 'POST' and 'User-Agent' not in request.headers:
        url = request.form['url']
        headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0',\
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'en-US,en;q=0.5',\
        'Accept-Encoding':'none','Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3','Connection': 'keep-alive'}

        request_ = urllib2.Request(url, headers=headers)
        data = urllib2.urlopen(request_)
        soup = BeautifulSoup(data, 'html.parser')

        links = []
        og_image = (soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'}))  
        if og_image and og_image['content']:
            links.append(og_image['content'])
            print og_image['content']

        thumbnail_spec = soup.find('link', rel='image_src')
        if thumbnail_spec and thumbnail_spec['href']:
            links.append(thumbnail_spec['href'])
            print thumbnail_spec['href']

        for img in soup.find_all("img", class_="a-dynamic-image", src=True):
            if "sprite" not in img["src"] and "data:image/jpeg" not in img["src"]:
                links.append(urlparse.urljoin(url, img["src"]))
                print urlparse.urljoin(url, img["src"])

        response = jsonify({'error': '1', 'data':'', 'message':'Unable to extract thumbnails'})

        if len(links)>0:
            response = jsonify({'error': 'null', 'data': {'thumbnails': links }, 'message':'success'})
        return response
    if request.method == 'POST' and 'User-Agent' in request.headers:
        return "yo"
    return render_template(
        'url.html',
        title='Process',
        year=datetime.now().year
    )

def process_(url):
    headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0',\
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'en-US,en;q=0.5',\
    'Accept-Encoding':'none','Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3','Connection': 'keep-alive'}
    
    request_ = urllib2.Request(url, headers=headers)
    data = urllib2.urlopen(request_)
    soup = BeautifulSoup(data, 'html.parser')

    links = []  
    og_image = (soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'}))
    if og_image and og_image['content']:
        links.append(og_image['content'])
        print og_image['content']

    thumbnail_spec = soup.find('link', rel='image_src')
    if thumbnail_spec and thumbnail_spec['href']:
        links.append(thumbnail_spec['href'])
        print thumbnail_spec['href']

    for img in soup.find_all("img", class_="a-dynamic-image", src=True):
        if "sprite" not in img["src"] and "data:image/jpeg" not in img["src"]:
            links.append(urlparse.urljoin(url, img["src"]))
            print urlparse.urljoin(url, img["src"])

    images = []
    if len(links)>0:
        for t in range(0, len(links)):
            l = '<div  class=\'btn grab\'><img id=\'tick' + str(t) +  '\' height=\'100px\' width=\'100px\' src=' + links[t] + '></img></div>'
            images.append(l)

    set_ = ""
    for i in images:
        set_ += i
    return set_
    # return images

#---Adds a wish
@app.route('/api/user/<int:id>/wishlist', methods=['POST', 'GET'])
@login_required
def wishlist(id):
    f = id
    wishlist = WishList.query.filter_by(owner=id).all()
    if request.method == 'POST' and 'User-Agent' not in request.headers:
        url = request.form['url']
        title = request.form['title']
        description = request.form['description']
        url = request.form['url']
        thumbnail = request.form['thumbnail']
        user = Users.query.filter_by(id=id).first()
        if user:
            new_wish = WishList(id, title, description, url, thumbnail)
            db.session.add(new_wish)
            db.session.commit()
            wlst = []
            wishlist = WishList.query.filter_by(owner=id).all()
            for wish_ in wishlist:
                wlst.append({'title':wish_.title, 'description':wish_.description, 'url':wish_.url, 'thumbnail':wish_.thumbnail})
            resp = ({'error':'null', 'data':{'wishes': wlst}, 'message':'success'})
            return jsonify(resp)
        return jsonify({'error':'1', 'data':'', 'message':'no such wishlist exists'})
    
    if request.method == 'GET' and 'User-Agent' not in request.headers:
        user = Users.query.filter_by(id=id).first()
        if user:
            wishlist = WishList.query.filter_by(owner=id).all()
            wlst = []
            for wish_ in wishlist:
                wlst.append({'title':wish_.title, 'description':wish_.description, 'url':wish_.url, 'thumbnail':wish_.thumbnail})
            resp = ({'error':'null', 'data':{'wishes': wlst}, 'message':'success'})
            return jsonify(resp)
        return jsonify({'error':'1', 'data':'', 'message':'no such wishlist exists'})
    
    form = WishForm()
    
    if request.method == 'POST' and 'User-Agent' in request.headers:
        if len(request.form) == 1:
            # print "hello world  "
            try:
                url = request.form['url']
                choice = process_(url)
                return "{}".format(choice)
            except Exception as e:
                try:
                    wish = request.form['wish']
                    db.session.execute("DELETE FROM wish_list WHERE thumbnail=\'"+ wish + "\'")
                    db.session.commit()
                except Exception as d:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
        
            return render_template(
                    'wishlist.html',
                    title='Wishlist',
                    year=datetime.now().year,
                    f=f,
                    form=form,
                    user=g.user
                )
        if form.validate_on_submit():
            title = request.form['title']
            descr = request.form['description']
            url = request.form['url']
            thumb = request.form['thumbnail']
            user = Users.query.filter_by(id=id).first()
            if user:
                new_wish = WishList(id, title, descr, url, thumb)
                db.session.add(new_wish)
                db.session.commit()
                wishlist_ = WishList.query.filter_by(owner=id).all()
                return render_template(
                    'wishlist.html',
                    title='Wishlist',
                    year=datetime.now().year,
                    f=f,
                    form=form,
                    wishlist=wishlist_,
                    user=g.user
                )
    e_form = SendEmailForm()

    return render_template(
        'wishlist.html',
        title='Wishlist',
        year=datetime.now().year,
        f=f,
        wishlist=wishlist,
        form=form,
        e_form = e_form,
        user=g.user
    )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    """Render the website's about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.',
        user=g.user
    )


@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=8888)

 #-/-\-/-\-/-\-/-\-/-\-/-\-/-\-/-\-/-\-/-\-/-\-/-\

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = SendEmailForm()
    if request.method =='POST':
        sendmail()
    return render_template('contact.html', form=form)

def sendmail():
    fromaddr = request.form['email']
    toaddr  = 'cmclaren89@gmail.com'
    message = """From: {} <{}>
    To: {} <{}>
    Subject: {}

    {}
    """
    msg = request.form['message']
    fromname = request.form['name']
    toname = "Craig McLaren"
    subject = request.form['subject']
    messagetosend = message.format(
                             fromname,
                             fromaddr,
                             toname,
                             toaddr,
                             subject,
                             msg)
    username = 'cmclaren89@gmail.com'
    password = 'uwdaqbgqxdmhbdzo'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddr, messagetosend)
    server.quit()
    return
