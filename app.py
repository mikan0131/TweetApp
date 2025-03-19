from flask import Flask, render_template, send_from_directory, request, redirect, flash, url_for, session, Markup
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from datetime import datetime
import os
import hashlib
from datetime import timedelta
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
  groups = db.Column(db.JSON())
  addresses = db.Column(db.JSON())
  request = db.Column(db.JSON())

class Posts(db.Model):
  __tablename__ = 'posts'
  from_address = db.Column(db.Text())
  to_group = db.Column(db.Text())
  to_address = db.Column(db.Text())
  content = db.Column(db.Text())
  created_at = db.Column(db.DateTime, default = datetime.utcnow)
  id = db.Column(db.Integer, primary_key = True, autoincrement = True)

class Groups(db.Model):
  __tablename__ = 'groups'
  id = db.Column(db.Integer, primary_key = True, autoincrement = True)
  name = db.Column(db.Text())
  password_hash_md5 = db.Column(db.Text())
  about = db.Column(db.Text())

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
  G = []
  if (type == 'groups'):
    G = User.query.filter(User.name == name).first().groups
  if (type == 'addresses'):
    G = User.query.filter(User.name == name).first().addresses
  if type == 'requests':
    G = User.query.filter(User.name == name).first().request
  # ! G == NULLならからの配列を返す
  if G is not None:
    groups = G
    return groups
  return []

# * チャットで表示する投稿を判別
def chat_post_check(user, name, from_address, to_address):
  if ((user == from_address and name == to_address)\
    or (user == to_address and name == from_address)):
    return True
  else:
    return False
  

# * トップページ
@app.route('/')
def index():
  flash('Hello')
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

# * 新規登録

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
    return render_template('profile.html', name = name, email = User.query.filter(User.name == name)[0].mail_address, groups = print_array(name, 'groups'), \
      addresses = print_array(name, 'addresses'), requests = print_array(name, 'requests'))
  else:
    return render_template('not_found.html')

# * ログアウト
@app.route('/logout')
def logout():
  session['login'] = 'none'
  session['username'] = '????'
  return redirect(url_for('index'))


# * 新規ポスト作成
# @app.route('/new')
# def new_post():
#   if (session['login'] == 'ok'):
#     return render_template('new_post.html', groups = print_array(session['username'], 'groups'), addresses = print_array(session['username'], 'addresses'))
#   else:
#     return redirect(url_for('login_form'))

@app.route('/send_new_post', methods = ['POST'])
def send_new_post():
  content = request.form['content']
  new_post = Posts()
  new_post.content = content
  new_post.from_address = session['username']
  if 'group' in request.form:
    new_post.to_group = request.form['group']
  if 'address' in request.form:
    new_post.to_address = request.form['address']
  db.session.add(new_post)
  db.session.commit()
  return redirect(url_for('show_group', group = new_post.to_group))

# * グループを表示
@app.route('/groups/<string:group>')
def show_group(group):
  my_groups = print_array(session['username'], 'groups')
  print(my_groups)
  if (my_groups.count(group)):
    posts = Posts.query.filter(Posts.to_group == group).all()
    posts.reverse()
    return render_template('group.html', group = group, posts = posts)
  else:
    return "<h1>You can't see this group. Please login first.</h1>"

# * ポスト編集
@app.route('/edit/<int:id>', methods = ['GET'])
def edit(id):
  post = Posts.query.get(id)
  if (post.from_address == session['username']):
    default = post.content
    return render_template('edit.html', id = id, default = default)
  else:
    return "<h1>You can't edit this post. Please login first.</h1>"

# * 編集送信
@app.route('/send_edit/<int:id>', methods = ['POST'])
def send_edit(id):
  content = request.form['content']
  editted_post = Posts.query.get(id)
  editted_post.content = content
  group = editted_post.to_group
  user = editted_post.from_address
  if (user != session['username']):
    return "<h1>You can't edit post" + str(id) +". Please login first.</h1>"
  db.session.commit()
  return redirect(url_for('show_group', group = group))

# * 投稿削除
@app.route('/delete/<int:id>')
def delete_post(id):
  delete_post = Posts.query.get(id)
  db.session.delete(delete_post)
  group = delete_post.to_group
  user = delete_post.from_address
  if (user != session['username']):
    return "<h1>You can't delete this post. Please login first.</h1>"
  db.session.commit()
  return redirect(url_for('show_group', group = group))

# * 個人チャットページ
@app.route('/chat/<string:address>')
def show_chat(address):
  if (print_array(session['username'], 'addresses').count(address) == False):
    return redirect(url_for('login_form'))
  filter_condition = or_(and_(Posts.from_address == session["username"], Posts.to_address == address), \
    and_(Posts.from_address == address, Posts.to_address == session["username"]))
  posts = Posts.query.filter(filter_condition).all()
  posts.reverse()
  return render_template('chat.html', address = address, posts = posts)

# * 個人チャット送信
@app.route('/send_message', methods = ['POST'])
def send_message():
  new_message = Posts()
  new_message.from_address = request.form['from']
  new_message.to_address = request.form['to']
  new_message.content = request.form['content']
  db.session.add(new_message)
  db.session.commit()
  return redirect(url_for('show_chat', address = request.form['to']))

# * 友達申請
@app.route("/request/<string:address>")
def friend_request(address):
  user = User.query.filter(User.name == address).all()
  ok = True
  if len(user) == 0: ok = False
  if ok == True:
    user = User.query.filter(User.name == address).first()
    send = user.request
    if user.request is None:
      send = [session['username']]
    else:
      send.append(session['username'])
    user.request = send
    db.session.commit()
  return render_template("request_ok.html", ok = ok)

# * 検索
@app.route('/search', methods = ['POST', 'GET'])
def search():
  word = request.form['word']
  users = User.query.filter(word in User.name).all()
  groups = Groups.query.filter(word in User.name).all()
  size = len(users) + len(groups)
  return render_template("search.html", word = word, users = users, groups = groups, size = size)

# * リクエスト前の設定
@app.before_request
def before_request():
  if (not 'login' in session): session['login'] = 'none'
  session.permanent = True
  session.modified = True

# * 改行文字フィルター
@app.template_filter('cr')
def cr(arg):
  return Markup(arg.replace('\r', '<br>'))