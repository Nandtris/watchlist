from flask import Flask
app = Flask(__name__)

# 视图函数（view funciton），你可以理解为“请求处理函数”
# 只需要写出相对地址，主机地址、端口号等都不需要写出
# http://localhost:5000/
@app.route("/") 
def hello():
    return 'Welcome to My Watchlist!'