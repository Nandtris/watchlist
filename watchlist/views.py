from flask import render_template, redirect, flash, url_for, request
from flask_login import login_required, login_user, logout_user, current_user

from watchlist import app, db
from watchlist.models import User, Movie


@app.route("/", methods=['GET', 'POST']) 
def index():
    """Add a item"""

    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))

        title = request.form.get('title')
        year = request.form.get('year')

        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') #错误提示
            return redirect(url_for('index')) # 重定向回主页
        
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.') #显示成功创建提示
        return redirect(url_for('index'))

    # user = User.query.first() # 没有上下文处理函数则要此变量
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
    flash('Goodbye.')
    return redirect(url_for('index'))

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
    return render_template('setting.html')