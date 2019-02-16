

from flask import Flask, render_template, redirect, request, session, flash
import re
import time, datetime
from datetime import date
from mysqlconnection import MySQLConnector
import md5 # imports the md5 module to generate a hash

app = Flask(__name__)
app.secret_key = 'ThisIsSecret' 

NUM_REGEX = re.compile('\d')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+.[a-zA-Z]+$')
UPPER_REGEX = re.compile('[A-Z]')
mysql = MySQLConnector(app,'wall')

@app.route('/')
def index():
  session['first_name'] = ""
  session['last_name'] = ""
  return render_template("index.html")

@app.route('/process/register', methods=['POST'])
def registerUser():
    error = False
    info = {}
    info['First Name'] = request.form['first_name']
    info['Last Name'] = request.form['last_name']
    info['Email'] = request.form['email']
    info['Password'] = request.form['password']
    info['Confirm Password'] = request.form['con_password']

    for key in info:
      if info[key] == "":
        flash(key+" cannot be empty!","Error")
        error = True

      if key == 'First Name' or key == 'Last Name':
          if NUM_REGEX.search(info[key]):
            flash(key+" cannot have numbers!","Error")
            error = True
          if (len(info[key]) < 2):
            flash(key+" should be 2 or more characters!","Error")
            error = True

      if key == 'Password':
        if len(info[key]) > 8:
          flash(key+" cannot be more than 8 characters!")
          error = True
        if info[key] != info['Confirm Password']:
          flash("Password and Confirm Password do not match!")
          error = True
        
      if key == 'Email':
        if not EMAIL_REGEX.match(info[key]):
            flash("Invalid email!")
            error = True
      
    if error == True:
      print flash
      return redirect('/') 
    else:      
      query = "INSERT INTO users (first_name, last_name, email, password ) VALUES (:first_name,:last_name,:email,:password)"
      data = {
              'first_name': request.form['first_name'],
              'last_name': request.form['last_name'],
              'email': request.form['email'],
              'password': md5.new(request.form['password']).hexdigest()
          }
    
      mysql.query_db(query, data)
      print flash("You have registered successfully!")
      return redirect('/')

@app.route('/process/login', methods=['POST'])
def loginUser():
    error = False

    query = 'SELECT email, password, first_name, last_name, id FROM users'                         
    emails = mysql.query_db(query)   
    print emails
    for user in emails:

      if request.form['email'] == user['email']:
        if request.form['password'] != request.form['con_password']:
          print flash("Password does not match confirm password!")
          return redirect('/') 
        else:
          if md5.new(request.form['password']).hexdigest() != user['password']:
            print flash("Password is incorrect!")
            return redirect('/') 
          else:
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['id'] = user['id']
            return redirect('/success')

    print flash("Login is not valid")
    return redirect('/') 
 
@app.route('/success')
def success():
 
   query = "SELECT users.first_name, users.last_name, messages.message, messages.created_at,messages.user_id, messages.id as message_id FROM users JOIN messages ON users.id = messages.user_id"
   messages = mysql.query_db(query)                           # run query with query_db()

   query = "SELECT users.first_name, users.last_name, comments.comment, comments.message_id as msg_id,comments.user_id,comments.created_at, messages.id FROM comments JOIN users ON users.id = comments.user_id JOIN messages ON messages.id = comments.message_id"    
   comments = mysql.query_db(query)                           # run query with query_db()

   return render_template('success.html', all_messages=messages, comments=comments )

@app.route('/processMessage', methods=['POST'])
def processMessage():
  query = "INSERT INTO messages (message, user_id ) VALUES (:message,:id)"
  data = {
          'message': request.form['message'],
          'id': request.form['id']
          }
    
  mysql.query_db(query, data)
  
  return redirect('/success')

@app.route('/processComment', methods=['POST'])
def processComment():
  query = "INSERT INTO comments (comment, user_id, message_id ) VALUES (:comment,:user_id,:message_id)"
  data = {
          'comment': request.form['comment'],
          'user_id': request.form['user_id'],
          'message_id': request.form['message_id']
          }
    
  mysql.query_db(query, data)
  
  return redirect('/success')

app.run(debug=True) 