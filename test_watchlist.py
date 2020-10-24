import unittest

from app import app, db, Movie, User, forge, initdb

class WatchlistTestCase(unittest.TestCase):
    """ Flask App programm test"""

    # 测试固件
    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
        )
        db.create_all()
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie Title', year='2020')
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()
        self.runner = app.test_cli_runner()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_app_exist(self):
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    # 测试客户端
    def test_404_page(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data) 
        self.assertEqual(response.status_code, 404)

    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data) 
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    # 辅助方法， 用于用户登录
    def login(self):
        self.client.post('/login', data=dict(
            username = 'test',
            password = '123'
        ), follow_redirects=True)

    # 测试创建 更新 删除条目
    def test_create_item(self):
        self.login()

        # 将 follow_redirects 参数设为 True 可以跟随重定向，
        # 最终返回的会是重定向后的响应
        response = self.client.post('/', data=dict(
            title = 'New Movie',
            year = '2020'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)

        response = self.client.post('/', data=dict(
            title = '',
            year = '2020'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data) 
        self.assertIn('Invalid input.', data)

        response = self.client.post('/', data=dict(
            title = 'New Movie',
            year = ''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

    def test_update_item(self):
        self.login()

        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2020', data)

        response = self.client.post('/movie/edit/1', data=dict(
            title = 'New Movie Edited',
            year = '2020'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('New Movie Edited', data)
        self.assertIn('Item updated.', data)

        # title == ' ' maybe bug
        response = self.client.post('/movie/edit/1', data=dict(
            title = ' ',
            year = '2020'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item updated.', data)
        self.assertIn(' ', data)

        # year = ' ' maybe bug
        response = self.client.post('/movie/edit/1', data=dict(
            title = 'New Movie Edited Again',
            year = ' '
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item updated.', data)
        self.assertIn('New Movie Edited Again', data)
        self.assertIn(' ', data)

    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item deleted.', data)
        self.assertNotIn('Test Movie Title', data)

    # 测试登录保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
     
        self.assertNotIn('Logout', data)
        self.assertNotIn('Setting', data)
        self.assertNotIn('<form method="POST">', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Add', data)

    def test_login(self):

        # 测试登录
        response = self.client.post('/login', data=dict(
            username = 'test',
            password = '123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Setting', data)
        self.assertIn('Logout', data)
        self.assertIn('Edit', data)
        self.assertIn('Delete', data)
        self.assertIn('<form method="POST">', data)

        # 测试错误密码、用户名
        response = self.client.post('/login', data=dict(
            username = 'test',
            password = '456'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        response = self.client.post('/login', data=dict(
            username = ' ',
            password = '123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 测试空密码 空用户 ，此处与书上代码不同，因为
        # login 函数 Invalid input 部分作用？
        response = self.client.post('/login', data=dict(
            username = 'greyli',
            password = '  '
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        response = self.client.post('/login', data=dict(
            username=' ',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

    # 测试登出
    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Setting', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="POST">', data)

    # 测试设置 
    def test_setting(self):
        self.login()

        response = self.client.get('/setting')
        data = response.get_data(as_text=True)
        self.assertIn('Setting', data)
        self.assertIn('Your Name', data)

        response = self.client.post('/setting', data=dict(
            name ='Grey Li',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Setting updated.', data)
        self.assertIn('Grey Li', data)

        # 更新时， 名称为空 ' '有空格符？
        # response = self.client.post('/setting', data=dict(
        #     name = ' ',
        # )follow_redirects=True)
        # data = response.get_data(as_text=True)
        # self.assertNotIn('Setting updated.', data)
        # self.assertIn('Invalid input.', data)


    # 测试自定义命令行命令
    def test_forge_command(self):
        result = self.runner.invoke(forge)
        self.assertIn('Done', result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'grey', '--password', '123'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'grey')
        self.assertTrue(User.query.first().validate_password('123'))

    def test_admin_command_update(self):
        result = self.runner.invoke(args=['admin', '--username', 'peter', '--password', '456'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'peter')
        self.assertTrue(User.query.first().validate_password('456'))

if __name__ == "__main__":
    unittest.main()
