from flask import Flask, render_template, send_from_directory, request, redirect, flash, url_for, make_response, session
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
from datetime import timedelta
from email import message
import smtplib
# ! Flask-MarkdownのインポートはFlaskのバージョンダウンにより解決(Flask==2.3.3)
from flaskext.markdown import Markdown

app = Flask(__name__)
Markdown(app)

# ! セッションのセキュリティー
app.config['SECRET_KEY'] = b'AsDfGhJkLqWeRtY%#_e' # セッション暗号化キー
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days = 7) # セッションの永続化
app.config['SESSION_COOKIE_SECURE'] = True # HTTPSでしかセッションにアクセスできないようにする
app.config['SESSION_COOKIE_HTTPONLY'] = True # JavaScriptからセッションにアクセスできないようにする
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # クロスサイトリクエストでセッションが送信されないようにする

# * MySQLデータベースアクセス
user = 'root'
host = 'localhost'
database = 'tweet_app'
password = 'BTBmurata2348.pss'

db_uri = f'mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


class User(db.Model):
  __tablename__ = 'user'
  id = db.Column(db.Integer, primary_key = True, autoincrement = True)
  name = db.Column(db.Text())
  mail_address = db.Column(db.Text())
  password_hash_md5 = db.Column(db.Text())
  groups = db.Column(db.Text())

# * パスワードの一致をチェック
def check_login(username, password_hash):
  here = User.query.filter(User.name == username).count()
  if (here == False):
    return False
  user_data = User.query.filter(User.name == username)
  if (user_data[0].password_hash_md5 == password_hash):
    return True
  else:
    return False

def print_groups(name):
  G = User.query.filter(User.name == name)
  if G[0].groups is not None:
    groups = G[0].groups.split(',')
    return groups
  return []

# * トップページ
@app.route('/')
def index():
  login = session['login'] == 'ok'
  return render_template('index.html', login = login)

# * アプリのアイコンをリクエスト
@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static/img'), 'favicon.ico', )

"""
# login form
@app.route('/login')
def login():
  return render_template('login.html')
"""

# * ログインフォーム
@app.route('/login', methods = ['POST', 'GET'])
def login_form():
  if request.method == 'POST':
    # * 
    user_name = request.form['user_name']
    password = request.form['password']
    enc_password = bytes(password, encoding = 'utf-8')
    password_hash = hashlib.md5(enc_password).hexdigest()
    # * ログインのパスワードを確認し、OKならプロファイル表示、NGならリダイレクト
    if (check_login(user_name, password_hash)):
      # * セッション編集
      session['username'] = user_name
      session['login'] = 'ok'
      return redirect(url_for('index'))
    else:
      session['login'] = 'falied'
      return redirect(url_for('login_form'))
  login = True
  if (session['login'] == 'falied'):
    login = False
  print(login)
  return render_template('login.html', login = login)

# TODO: 新規登録
@app.route('/register', methods = ['POST', 'GET'])
def register():
  return render_template('register.html')

@app.route('/send_email_verify', methods = ['POST'])
def entry():
  name = request.form['user_name']
  password = request.form['password']
  email = request.form['email']
  if (User.query.filter(User.name == name) == False):
    return render_template('send_email_verify_error.html')
  
  #TODO:確認用メール
  '''
  smtp_host = 'smtp.gamil.com'
  smtp_port = 587
  from_email = 'mikan0131server@gmail.com'
  to_email = email
  username = 'mikan0131server@gmail.com'
  password = ''
  
  msg = message.EmailMessage()
  msg.set_content('Hello')
  msg['Subject'] = 'Test'
  msg['From'] = from_email
  msg['To'] = to_email
  server = smtplib.SMTP(smtp_host, smtp_port)
  server.ehlo()
  server.starttls()
  server.ehlo()
  server.login(username, password)
  
  server.send_message(msg)
  server.quit()
  '''
  
  new_user = User();
  new_user.name = name
  enc_password = bytes(password, encoding = 'utf-8')
  password_hash = hashlib.md5(enc_password).hexdigest()
  new_user.password_hash_md5 = password_hash
  new_user.mail_address = email
  db.session.add(new_user)
  db.session.commit()
  return render_template('send_email_verify_sccess.html', email = email)

# * ユーザーのプロファイル
@app.route('/profile/<string:name>', methods = ['GET'])
def profile(name):
  if (User.query.filter(User.name == name).count() == True):
    return render_template('profile.html', name = name, email = User.query.filter(User.name == name)[0].mail_address, groups = print_groups(name))
  else:
    return render_template('not_found.html')

# * ログアウト
@app.route('/logout')
def logout():
  session['login'] = 'none'
  return redirect(url_for('index'))

# * リクエスト前の設定
@app.before_request
def before_request():
  if (not 'login' in session): session['login'] = 'none'
  session.permanent = True
  session.modified = True