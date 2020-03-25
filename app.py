from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from config import Config


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
    return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id = id)


#create a class for each form

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message = "passwords don't match")])
    confirm = PasswordField('Confirm Password')

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

#debug = True lets you not have to reload server
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)