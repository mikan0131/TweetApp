from flask import Flask, render_template, send_from_directory, request, redirect, flash, url_for, make_response, session
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
from datetime import timedelta
# ! Flask-MarkdownのインポートはFlaskのバージョンダウンにより解決(Flask==2.3.3)
# from flaskext.markdown import Markdown

app = Flask(__name__)
# Markdown(app)

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
  groups = db.Column(db.JSON())
  addresses = db.Column(db.JSON())

class Posts(db.Model):
  __tablename__ = 'posts'
  id = db.Column(db.Integer, primary_key = True, autoincrement = True)
  from_address = db.Column(db.Text())
  to_address = db.Column(db.JSON())
  to_groups = db.Column(db.JSON())
  created_at = db.Column(db.Date)

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

# * データベースから配列出力
def print_array(name, type):
  if (type == 'groups'):
    G = User.query.filter(User.name == name).first().groups
  if (type == 'addresses'):
    G = User.query.filter(User.name == name).first().addresses
  # ! G == NULLならからの配列を返す
  if G is not None:
    groups = G
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
  
  # TODO:確認用メール
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
    return render_template('profile.html', name = name, email = User.query.filter(User.name == name)[0].mail_address, groups = print_array(name))
  else:
    return render_template('not_found.html')

# * ログアウト
@app.route('/logout')
def logout():
  session['login'] = 'none'
  session['username'] = '????'
  return redirect(url_for('index'))

# * 新規ポスト作成
@app.route('/new')
def new_post():
  if (session['login'] == 'ok'):
    return render_template('new_post.html', groups = print_array(session['username'], 'groups'), addresses = print_array(session['username'], 'addresses'))
  else:
    return redirect(url_for('login_form'))

@app.route('/send_new_post', methods = ['POST'])
def send_new_post():
  content = request.form['content']
  to_groups = []
  to_addresses = []
  for group in print_array(session['username'], 'group'):
    if request.form[group] == True:
      to_groups.append(group)
  for address in print_array(session['username'], 'address'):
    if request.form[address] == True:
      to_addresses.append(address)
  new_post = Posts()
  new_post.from_address = request.form['from_address']
  new_post.to_address = to_addresses
  new_post.to_groups = to_groups
  db.session.add(new_post)
  db.session.commit()

# * リクエスト前の設定
@app.before_request
def before_request():
  if (not 'login' in session): session['login'] = 'none'
  session.permanent = True
  session.modified = True