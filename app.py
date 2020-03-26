from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from config import Config
from functools import wraps


#instance of the flask class
# jinja template engine
# {%%} is logic  {{}} to insert value 

app = Flask(__name__)

#config for MySQL
app.config['MYSQL_HOST'] = Config['MYSQL_HOST']
app.config['MYSQL_USER'] = Config['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = Config['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = Config['MYSQL_DB']
#cursor is kind of like a handler
app.config['MYSQL_CURSORCLASS'] = Config['MYSQL_CURSORCLASS']
#initialize mysql
mysql = MySQL(app)




Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "no articles found"
        return render_template('articles.html', msg=msg)
    cur.close()

    

@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)


#create a class for each form

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message = "passwords don't match")])
    confirm = PasswordField('Confirm Password')
#use register

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #creating cursor
        cur = mysql.connection.cursor()
        #use this cursor to execute commands
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)", (name,email,username,password))
        #commit to db
        mysql.connection.commit()
        #close connection
        cur.close()
        #message 
        flash('you are now registered and can login','success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #getting form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #creating cursor
        cur = mysql.connection.cursor()
        #use this cursor to execute commands
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        #if there are rows found store it in hash
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            #compare password
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('Password Matched')
                #put logged in in session
                session['logged_in'] = True
                session['username'] = username
                flash('you are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "invalid login"
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = "username not found"
            return render_template('login.html', error=error)
        #commit to db
        # mysql.connection.commit()
        # #close connection
        # cur.close()
        # #message 
        # flash('you are now registered and can login','success')
        # return redirect(url_for('login'))
    return render_template('login.html')


#checking if login
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('unauthorized', 'danger')
            return redirect(url_for('login'))
    return wrap

#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "no articles found"
        return render_template('dashboard.html', msg=msg)
    cur.close()

    

#article form
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#add article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        
        mysql.connection.commit()

        cur.close()

        flash('article create','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)


#edit article
@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    #getting article by ID
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()

    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']
   
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        
        mysql.connection.commit()

        cur.close()

        flash('article updated','success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)


#delete
@app.route('/delete_article/<string:id>', methods= ['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id = %s", [id])
        
    mysql.connection.commit()

    cur.close()

    flash('Deleted','success')
    return redirect(url_for('dashboard'))
  

#logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("you are now logged out","success")
    return redirect(url_for('login'))


#debug = True lets you not have to reload server
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)