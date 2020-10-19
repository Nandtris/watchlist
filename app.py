import os
import sys

import click
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy 


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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


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
    return dict(user=user)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# 视图函数(view funciton)--“请求处理函数”
# 只需要写出相对地址，主机地址、端口号等都不需要写出
# http://localhost:5000/
@app.route("/", methods=['GET', 'POST']) 
def index():
    # Flask 会在请求触发后把请求信息放到 request 里
    if request.method == 'POST':
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
    return render_template('edit.html', movie=movie)

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))






