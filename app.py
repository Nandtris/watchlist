import os
import sys

import click
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


WIN = sys.platform.startswith('win')
if WIN:
    # windows sqlite 系统使用三斜线
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
# 关闭对模型修改的监控 （？？？）
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'

db = SQLAlchemy(app)

# 使用 Flask-Login 实现用户认证
# 初始化 Flask-Login:

# 1 实例化扩展类 
login_manager = LoginManager(app)

# 2 实现一个“用户加载回调函数”
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user

login_manager.login_view = 'login' #页面保护后，用户重定向到登录页

# 3 让存储用户的 User 模型类继承 UserMixin 类
class User(db.Model, UserMixin): # 自动创建表 user
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))

    # 表结构发生变化，要重新生成数据库 flask initdb --drop
    username = db.Column(db.String(20)) # 用户名
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


# Flask 命令行工具 
# flask initdb 
# flask forge 生成虚拟数据
# flask admin 生成管理员账户

# ???
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """create user, defaut:U-greyli P-123"""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password) #设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    
    db.session.commit()
    click.echo('Done.')

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database"""
    if drop: # flask initdb --drop
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')

@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},]
    
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done')


# 模板上下文处理函数
@app.context_processor
def inject_user():
    user = User.query.first()
    # 返回字典，等同 return {'user': user} ?
    return dict(user=user)

@app.errorhandler(404)
# e ?
def page_not_found(e):
    return render_template('404.html'), 404

# 视图函数(view funciton)--“请求处理函数”
# 只需要写出相对地址，主机地址、端口号等都不需要写出
@app.route("/", methods=['GET', 'POST']) 
def index():
    """Add a item"""

    # Flask 会在请求触发后把请求信息放到 request 里
    if request.method == 'POST':

        # 用户未认证???
        if not current_user.is_authenticated:
            return redirect(url_for('index'))

        title = request.form.get('title')
        year = request.form.get('year')

        # 通过在 <input> 元素内添加 required 属性
        # 实现的验证（客户端验证）并不完全可靠
        # 我们还要在服务器端追加验证
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') #错误提示
            return redirect(url_for('index')) # 重定向回主页
        
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.') #显示成功创建提示
        return redirect(url_for('index'))

    # user = User.query.first() # 没有上下文处理函数则要此变量
    # print(user)
    movies = Movie.query.all()
    return render_template('index.html', 
    movies = movies)

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required  # 登录保护
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year)>4 or len(title)>60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))

        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))

    # ???
    return render_template('edit.html', 
    movie=movie)

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required # 登录保护
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        #核对账户名和密码
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))

        flash('Invalid username or password.') # 验证失败，显示错误信息
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required #用于视图保护
def logout():
    logout_user()
    flash('See you later.')
    return redirect(url_for('index'))

# 设置用户名字
@app.route('/setting', methods=['GET', 'POST'])
@login_required
def setting():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name)>20:
            flash('Invalid input.')
            return redirect(url_for('setting'))

        current_user.name = name
        db.session.commit()
        flash('Setting updated.')
        return redirect(url_for('index'))
    return render_template('Setting.html')
