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
  owner = db.Column(db.Text())

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
    friends = User.query.filter(User.name == name).first().addresses
    request_ok = True
    if isinstance(friends, list):
      if (friends.count(session['username']) == True):
        request_ok = False
    groups = print_array(name, 'groups')
    group_profiles = []
    for g in groups:
      profile = Groups.query.filter(Groups.name == g).first()
      group_profiles.append(profile)
    return render_template('profile.html', name = name, email = User.query.filter(User.name == name)[0].mail_address, groups = group_profiles, \
      addresses = print_array(name, 'addresses'), requests = print_array(name, 'requests'), request_ok = request_ok)
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
    return redirect(url_for('invite', group = group))

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
  if (User.query.filter(User.name == address).count() == False):
    return "<h1>You can't send this request.(This user is not exist)</h1>"
  your_friend = User.query.filter(User.name == session['username']).first().addresses
  send = []
  if (not isinstance(your_friend, list)):
    send.append(session['username'])
  elif (your_friend.count(address) == True):
    return "<h1>You can't send this request.(This user is already your friend)</h1>"
  else:
    send = User.query.filter(User.name == address).first().request
    send.append(session['username'])
  User.query.filter(User.name == address).first().request = send
  db.session.commit()
  return f'You sent a request to {address} successfully!'
# * 友達申請受け入れ
@app.route('/accept_address/<string:address>')
def accept_address(address):
  requested_user = User.query.filter(User.name == session['username']).first()
  requested_list = print_array(session['username'], 'requests')
  if address in requested_list:
    requested_list.remove(address)
    accepted_user = User.query.filter(User.name == address).first()
    requested_after = requested_user.addresses
    accepted_after = accepted_user.addresses
    if (accepted_after is None):
      accepted_after = [session['username']]
      db.session.commit()
    else:
      accepted_after.append(session['username'])
    if (requested_after is None):
      requested_after = [address]
      db.session.commit()
    else:
      requested_after.append(address)
      db.session.commit()
    requested_user.addresses = requested_after
    db.session.commit()
    accepted_user.addresses = accepted_after
    db.session.commit()
    requested_user.request = requested_list
    db.session.commit()
    return redirect(url_for('show_chat', address = address))
  else:
    return redirect(url_for('index'))

# * 友達申請拒否
@app.route('/reject_address/<string:address>')
def reject_address(address):
  requested_user = User.query.filter(User.name == session['username']).first()
  db.session.commit()
  rejected_user = None
  if (User.query.filter(User.name == address).count() == True):
    rejected_user = User.query.filter(User.name == address).first()
    db.session.commit()
  if rejected_user is None:
    return "<h1>You can't reject this user. (This user is not exist)</h1>"
  if not requested_user.request.count(rejected_user.name):
    return "<h1>You can't reject this user. (This user didn't send you a request)</h1>"
  send_list = requested_user.request
  send_list.remove(rejected_user.name)
  db.session.commit()
  requested_user.request = send_list
  db.session.commit()
  return redirect(url_for("profile", name = session['username']))

# * 検索
@app.route('/search', methods = ['GET'])
def search():
  word = request.args.get("word")
  users = User.query.filter(User.name.like("%" + word + "%")).all()
  groups = Groups.query.filter(or_(Groups.name.like(f"%{word}%"), Groups.about.like(f"%{word}%"))).all()
  size = len(users) + len(groups)
  return render_template("search.html", word = word, users = users, groups = groups, size = size)

# * グループロック
@app.route('/invite/<string:group>')
def invite(group):
  if (Groups.query.filter(Groups.name == group).count() == True):
    if (User.query.filter(User.name == session['username']).first() != None):
      if (User.query.filter(User.name == session['username']).first().groups.count(group) == True):
        redirect(url_for('show_group', group = group))
    return render_template('invite.html', group = group)
  else:
    return "<h1>That group is not exist</h1>"

@app.route('/check_invite/<string:group>', methods = ['POST'])
def check_invite(group):
  if Groups.query.filter(Groups.name == group).count() == False:
    return "<h1>That group is not exist.</h1>"
  Group = Groups.query.filter(Groups.name == group).first()
  check_hash = Group.password_hash_md5
  my_password = request.form['group-password']
  enc_password = bytes(my_password, encoding = 'utf-8')
  my_password_hash = hashlib.md5(enc_password).hexdigest()
  if (my_password_hash == check_hash):
    user = User.query.filter(User.name == session['username']).first()
    send = user.groups
    if isinstance(send, list):
      send.append(group)
      db.session.commit()
    else:
      send = [group]
      db.session.commit()
    user.groups = send
    db.session.commit()
    return redirect(url_for('show_group', group = group))
  else:
    return redirect(url_for('invite', group = group))


# * 新規グループ
@app.route('/new_group')
def new_group():
  return render_template('new_group.html')

@app.route('/create_group', methods = ['POST'])
def create_group():
  group_name = request.form['name']
  if (Groups.query.filter(Groups.name == group_name).count() == True):
    return "<h1>You can't use that group name. Try again.</h1>"
  group_password = request.form['password']
  group_about = request.form['about']
  new_group = Groups()
  new_group.name = group_name
  enc_password = bytes(group_password, encoding = 'utf-8')
  password_hash = hashlib.md5(enc_password).hexdigest()
  new_group.password_hash_md5 = password_hash
  new_group.about = group_about
  new_group.owner = session['username']
  me = User.query.filter(User.name == session['username']).first()
  send = []
  if (isinstance(me.groups, list) == True):
    send = me.groups
    send.append(group_name)
  else:
    send.append(group_name)
  me.groups = send
  db.session.commit()
  db.session.add(new_group)
  db.session.commit()
  return f"<h1>Yay! You created group {group_name}! You are an owner of this group!</h1>"

# * 友達をキック
@app.route('/kick/<string:address>')
def kick(address):
  me = User.query.filter(User.name == session['username']).first()
  if (isinstance(me.addresses, list)):
    if (me.addresses.count(address) == True):
      print('!')
      send_m = me.addresses
      send_m.remove(address)
      db.session.commit()
      me.addresses = send_m
      db.session.commit()
      kick = User.query.filter(User.name == address).first()
      send_k = kick.addresses
      send_k.remove(me.name)
      db.session.commit()
      kick.addresses = send_k
      db.session.commit()
      return redirect(url_for('profile', name = session['username']))
    else:
      return f"<h1>You and {address} are not friends.</h1>"
  else:
    return redirect(url_for('profile', name = session['username']))

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