import sys
import pathlib
import os
parent_parent_path = str(pathlib.Path(__file__).parent.parent.absolute())
sys.path.append(os.path.join(parent_parent_path, 'utils'))
sys.path.append(os.path.join(parent_parent_path, 'database'))

import chatroom
import utils
import security
import search_engine
import operators
import mailing
from dictianory import slef_made_codes, slef_made_codes_inv_map
import flask
from threading import Thread
from markupsafe import Markup

import datetime as dt
from flask_sessionstore import Session
from flask_sqlalchemy import SQLAlchemy

from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
import flaskcode

from functools import wraps

import waitress

def add_admin(db_configs, app_configs):
    conn = db_configs.conn
    cursor = conn.cursor()
    cursor.execute('select * from users where username=?', ('admin',))
    users = cursor.fetchall()
    if len(users)==0:
        cursor.execute('insert into users values (?,?,?,?,?,?)', ('admin', 'admin', 1, None, None, None))
        conn.commit()
        utils.init_user(app_configs, db_configs, 'admin')

class WebApp():
    def __init__(self, db_configs, ip, port, static_folder, recaptcha_bool, num_threads, mailing_bool, host_url): 
        self.ip = ip
        self.port = port
        self.num_threads = num_threads
        self.db_configs = db_configs
        self.mailing_bool = mailing_bool
        self.host_url = host_url
        self.app = flask.Flask(__name__, static_folder=static_folder)
        self.parent_path = str(pathlib.Path(__file__).parent.absolute())
        self.parent_parent_path = str(pathlib.Path(__file__).parent.parent.absolute())
        self.app.config['RECAPTCHA_ENABLED'] = recaptcha_bool
        self.app.config['DATABASE_FOLDER'] = os.path.join(self.parent_parent_path ,'database')
        self.app.config['UPLOAD_FOLDER'] = os.path.join(self.parent_parent_path ,'database' ,'uploaded_files')
        self.app.config['FAMILY_TREE_FOLDER'] = os.path.join(self.app.config['DATABASE_FOLDER'], 'family_tree')
        self.app.config['CONDITIONS_JSON_FOLDER'] = os.path.join(self.app.config['DATABASE_FOLDER'], 'conditions')
        self.app.config['CONDITIONS_JSON'] = os.path.join(self.app.config['DATABASE_FOLDER'], 'conditions', 'default.json')
        self.app.config['CONDITIONS_JSON_DEFAULT'] = 'default.json'
        self.app.config['TEMPLATES_FOLDER'] = os.path.join(self.parent_parent_path, 'web', 'templates')
        self.app.config['CREDS_FILE_PATH'] = os.path.join(self.app.root_path, 'creds.json')
        self.app.config['CREDS_FILE'] = utils.load_creds(self.app.config['CREDS_FILE_PATH'])
        self.app.config['SECRET_KEY'] = self.app.config['CREDS_FILE']['SECRET_KEY']
        self.app.config['RECAPTCHA_PUBLIC_KEY'] = self.app.config['CREDS_FILE']['RECAPTCHA_PUBLIC_KEY']
        self.app.config['RECAPTCHA_PRIVATE_KEY'] = self.app.config['CREDS_FILE']['RECAPTCHA_PRIVATE_KEY']

        self.app.config.from_object(flaskcode.default_config)
        self.app.config['FLASKCODE_RESOURCE_BASEPATH'] = os.path.join(self.app.config['DATABASE_FOLDER'], 'conditions')
        self.app.register_blueprint(flaskcode.blueprint, url_prefix='/editor')

        self.ChatRoom = chatroom.ChatRoom(self.db_configs)

        add_admin(self.db_configs, self.app.config)

        print(f'App initialized. Server running on http://{self.ip}:{self.port}')
    
    class RecaptchaForm(FlaskForm):
        username = StringField("username", validators=[DataRequired()])
        password = PasswordField("password", validators=[DataRequired()])
        recaptcha = RecaptchaField()
    
    
    def logger(self, f):
        @wraps(f)
        def wrap(*args, **kwargs):
            time = dt.datetime.now()
            conn = self.db_configs.conn
            cursor = conn.cursor()
            try:
                action = f.__name__
                username = flask.session['username']
                cursor.execute('insert into logs values (?,?,?,?,?,?)', (username, action, time, 'pass', None, None))
                conn.commit()
                return f(*args, **kwargs)
            except Exception as e:
                cursor.execute('update logs set status=?, error=? where username=? and action=? and date=?', ('fail', str(e), username, action, time))
                print(e)
                conn.commit()
                flask.flash('An error occured. Please try again later.')
                return flask.redirect(flask.url_for('index'))
        return wrap

    def run(self):
        app = self.app

        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if flask.request.method == 'POST':
                username = flask.request.form['username']
                password = flask.request.form['password']
                conn = self.db_configs.conn
                cursor = conn.cursor()
                cursor.execute('select * from users where username=? and password=?', (username, password))
                users = cursor.fetchall()

                form = self.RecaptchaForm()
                if len(users)==0:
                    return flask.render_template('login.html', error='Invalid username or password', form=form)
                elif form.validate_on_submit() or not app.config['RECAPTCHA_ENABLED']:
                    flask.session['username'] = username
                    flask.session['password'] = password
                    flask.session['logged_in'] = True
                    flask.session['admin'] = users[0][2]
                    return flask.redirect(flask.url_for('index'))
                else:
                    form = self.RecaptchaForm()
                    return flask.render_template('login.html', error='Invalid Captcha', form=form)

            else:
                form = self.RecaptchaForm()
                return flask.render_template('login.html', form=form)

        @app.route('/', methods=['GET', 'POST'])
        @security.login_required
        def index():
            entries_list = search_engine.entries_time_line(self.db_configs.conn)
            entries_html = flask.render_template('entries_list.html', entries_list=entries_list)
            entries_html = Markup(entries_html)
            return flask.render_template('index.html', entries_html=entries_html)

        @app.route('/logout')
        @security.login_required
        def logout():
            flask.session.pop('logged_in', None)
            flask.session.pop('username', None)
            flask.session.pop('password', None)
            flask.session.pop('admin', None)
            return flask.redirect(flask.url_for('login'))

        @app.route('/add_user', methods=['GET', 'POST'])
        @security.admin_required
        def add_user():
            return flask.render_template('add_user.html')

        @app.route('/add_user_to_db', methods=['GET', 'POST'])
        @security.admin_required
        @self.logger
        def add_user_to_db():
            username = flask.request.form['username']
            password = flask.request.form['password']
            repeat_password = flask.request.form['repeat_password']
            admin = flask.request.form['admin'] == 'True'
            name = flask.request.form['name']
            email = flask.request.form['email']

            if username == '' or password == '' or admin == '' or name == '' or email == '':
                flask.flash('Please fill all the fields')
                return flask.render_template('add_user.html')

            if password != repeat_password:
                flask.flash('Passwords do not match')
                return flask.render_template('add_user.html')

            conn = self.db_configs.conn
            cursor = conn.cursor()
            cursor.execute('select * from users where username=?', (username,))
            users = cursor.fetchall()

            if len(users)>0:
                flask.flash('Username already exists')
                return flask.render_template('add_user.html')

            else:
                cursor.execute('insert into users (username, password, admin, name, email) values (?,?,?,?,?)', (username, password, admin, name, email))
                utils.init_user(app.config, self.db_configs, username)
                conn.commit()
                flask.flash('User added successfully')
                # send email to the new user
                if self.mailing_bool:
                    mail_args = {'receiver_email': email,
                                'sender_email': app.config['CREDS_FILE']['SENDER_EMAIL_ADDRESS'],
                                'password': app.config['CREDS_FILE']['SENDER_EMAIL_PASSWORD'],
                                'subject': 'Welcome to the datamanager',
                                'username': username,
                                'name': name,
                                'user_password': password,
                                'website_url': self.host_url,
                                }
                    mailing.send_welcome_mail(mail_args)
                return flask.redirect(flask.url_for('index'))
    
        @app.route("/update_user_in_db/<int:id>", methods=['POST', 'GET'])
        @security.login_required
        @self.logger
        def update_user_in_db(id):
            if flask.request.method == 'POST':
                password = flask.request.form['password']
                repeat_password = flask.request.form['repeat_password']
                if flask.session['admin']:
                    admin = flask.request.form['admin'] == 'True'
                else:
                    admin = 0
                name = flask.request.form['name']
                email = flask.request.form['email']

                if password == '' or admin == '':
                    flask.flash('Please fill all the fields')
                    user = flask.request.form
                    return flask.render_template('profile.html', user=user)

                if password != repeat_password:
                    flask.flash('Passwords do not match')
                    user = flask.request.form
                    return flask.render_template('profile.html', user=user)

                conn = self.db_configs.conn
                cursor = conn.cursor()
                cursor.execute('select * from users where id=?', (id,))
                users = cursor.fetchall()

                if len(users)==0:
                    flask.flash('Username does not exist')
                    user = flask.request.form
                    return flask.render_template('profile.html', user=user)

                else:
                    cursor.execute('update users set password=?, admin=?, name=?, email=? where id=?', (password, admin, name, email, id))
                    conn.commit()
                    flask.flash('User updated successfully')
                    return flask.render_template('index.html')

        @app.route("/delete_user/<int:id>", methods=['POST', 'GET'])
        @security.admin_required
        @self.logger
        def delete_user(id):
            conn = self.db_configs.conn
            cursor = conn.cursor()
            cursor.execute('select * from users where id=?', (id,))
            users = cursor.fetchall()

            if len(users)==0:
                flask.flash('Username does not exist')
                return flask.redirect(flask.url_for('user_management'))

            else:
                cursor.execute('delete from users where id=?', (id,))
                conn.commit()
                flask.flash('User deleted successfully')
                return flask.redirect(flask.url_for('user_management'))
        
        @app.route('/user_management', methods=['GET', 'POST'])
        @security.admin_required
        def user_management():
            users = utils.get_users(self.db_configs.conn)

            users_html = [flask.render_template('user_profile_template.html', user=user) for user in users]
            users_html = [Markup(user_html) for user_html in users_html]

            return flask.render_template('user_management.html', users_html=users_html, users=users)

        @app.route('/entries', methods=['GET', 'POST'])
        @security.login_required
        def entries():
            conditions = utils.read_json_file(self.app.config['CONDITIONS_JSON'])
            conditions = utils.modify_conditions_json(conditions, target_conditions=[])
            conditions_html = flask.render_template('conditions.html', conditions=conditions)
            conditions_html = Markup(conditions_html)

            tomorrow_date = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
            yesterday_date = (dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

            dates = [yesterday_date, tomorrow_date]

            if flask.request.method == 'POST' and len(flask.request.form):
                entries_list = search_engine.filter_entries(self.db_configs.conn, flask.request.form)
                entries_html = flask.render_template('entries_list.html', entries_list=entries_list)
                entries_html = Markup(entries_html)
                return flask.render_template('entries.html', entries_html=entries_html, conditions_html=conditions_html, dates=dates)

            else:
                return flask.render_template('entries.html', entries_html=None, conditions_html=conditions_html, dates=dates)

        @app.route('/insert_entry', methods=('GET', 'POST'))
        @security.login_required
        def insert_entry():
            conditions_list = utils.list_user_conditoins_templates(self.db_configs.conn, self.app.config, flask.session)
            methods_list = utils.get_methods_list(self.app.config)
            today_date = dt.datetime.now().strftime("%Y-%m-%d")
            return flask.render_template('insert_entry.html', conditions_list=conditions_list, today_date=today_date, methods_list=methods_list)

        @app.route('/insert_entry_to_db', methods=['GET', 'POST'])
        @security.login_required
        @self.logger
        def insert_entry_to_db():
            if flask.request.method == 'POST':
                try:
                    Author = flask.session['username']
                    date = flask.request.form['date']
                    Tags = flask.request.form['Tags']
                    File_Path = flask.request.form['File_Path']
                    Notes = flask.request.form['Notes']
                    Files = flask.request.files.getlist('Files')
                    entry_name = flask.request.form['entry_name']
                    parent_entry = flask.request.form['parent_entry']

                except:
                    flask.flash('Please fill all the forms')
                    return flask.redirect(flask.url_for('insert_entry'))

                if not utils.check_hash_id_existence(self.db_configs.conn, parent_entry) and parent_entry != '':
                    flask.flash('Parent entry does not exist')
                    return flask.redirect(flask.url_for('insert_entry'))


                if Author == '' or date == '' or entry_name == '':
                    flask.flash('Please fill all the forms')
                    return flask.redirect(flask.url_for('insert_entry'))

                conditions = []

                for form_input in flask.request.form:
                    if 'condition' == form_input.split('&')[0]:
                        conditions.append('&'.join(form_input.split('&')[1:]))
                    elif 'PARAM' == form_input.split('&')[0]:
                        list_tmp = form_input.split('&')[2:]
                        list_tmp.append(flask.request.form[f"PARAMVALUE&{'&'.join(form_input.split('&')[1:])}"].split('&')[-1])
                        list_tmp = '&'.join(list_tmp)
                        conditions.append(list_tmp)
                conditions = ','.join(conditions)
                success_bool, hash_id = operators.insert_entry_to_db(conn=self.db_configs.conn, Author=Author, date=date, Tags=Tags, File_Path=File_Path, Notes=Notes, conditions=conditions, entry_name=entry_name, parent_entry=parent_entry)
                
                if hash_id:
                    utils.upload_files(self.app.config, hash_id, Files)

                if success_bool:
                    message = Markup(f'entry is added successfully! hash_id: {hash_id}')

                else:
                    message = 'Something went wrong'

                flask.flash(message)
                return flask.redirect(flask.url_for('index', session=flask.session))

        @app.route("/author_search", methods=["POST", "GET"])
        @security.login_required
        def author_search():
            searchbox = flask.request.form.get("text")
            return search_engine.author_search_in_db(conn=self.db_configs.conn, keyword=searchbox)
        
        @app.route("/email_search", methods=["POST", "GET"])
        @security.login_required
        def email_search():
            searchbox = flask.request.form.get("text")
            return search_engine.email_search_in_db(conn=self.db_configs.conn, keyword=searchbox)

        @app.route("/tags_search", methods=["POST", "GET"])
        @security.login_required
        def tags_search():
            searchbox = flask.request.form.get("text")
            return search_engine.tags_search_in_db(conn=self.db_configs.conn, keyword=searchbox)

        @app.route("/text_search", methods=["POST", "GET"])
        @security.login_required
        def text_search():
            searchbox = flask.request.form.get("text")
            return search_engine.text_search_in_db(conn=self.db_configs.conn, keyword=searchbox)

        @app.route("/entry/<int:id>", methods=["POST", "GET"])
        @security.login_required
        def entry(id):
            cursor = self.db_configs.conn.cursor()
            cursor.execute("SELECT * FROM entries WHERE id=?", (id,))
            entry = cursor.fetchone()
            target_conditions = entry[6]
            entry = list(entry)
            entry[6] = utils.parse_conditions(entry[6])
            for i in range(len(entry[6])):
                if len(entry[6][i].split('&')) ==3:
                    entry[6][i] = entry[6][i].split('&')[-1]
                else:
                    entry[6][i] = '->'.join(entry[6][i].split('&')[-2:])
            hash_id = entry[0]
            dirName = os.path.join(app.config['UPLOAD_FOLDER'], hash_id)
            List = os.listdir(dirName)

            # family_tree_html = utils.family_tree_to_html(self.db_configs.conn, hash_id, self.app.config['FAMILY_TREE_FOLDER'])
            # family_tree_html = Markup(family_tree_html)
            family_tree_html = None

            for count, filename in enumerate(List):
                List[count] = [os.path.join(app.config['UPLOAD_FOLDER'], hash_id, filename), f"{slef_made_codes_inv_map['remove']}&{filename}", filename]

            Files = List
            conditions = utils.read_json_file(self.app.config['CONDITIONS_JSON'])
            entry = tuple(entry)
            conditions = utils.modify_conditions_json(conditions, target_conditions)
            conditions_html = flask.render_template('conditions.html', conditions=conditions)
            conditions_html = Markup(conditions_html)
            return flask.render_template('entry.html', entry=entry, Files=Files, conditions_html=conditions_html, family_tree_html=family_tree_html)

        @app.route("/entry_by_hash_id/<string:hash_id>", methods=["POST", "GET"])
        @security.login_required
        def entry_by_hash_id(hash_id):
            id = utils.get_id_by_hash_id(self.db_configs.conn, hash_id)
            return flask.redirect(flask.url_for('entry', id=id))

        @app.route("/entry/<int:id>/update_entry", methods=["POST", "GET"])
        @security.login_required
        @self.logger
        def update_entry(id):
            post_form = flask.request.form
            entry = utils.get_entry_by_id(self.db_configs.conn, id)
            author = entry[5]
            usename = flask.session['username']
            admin = flask.session['admin']
            if author != usename and not admin:
                flask.flash('You are not allowed to edit this entry')
                return flask.redirect(flask.url_for('entry', id=id))

            # get hash_id from id
            cursor = self.db_configs.conn.cursor()
            cursor.execute("SELECT id_hash FROM entries WHERE id=?", (id,))
            hash_id = cursor.fetchone()[0]

            parent_entry = flask.request.form['parent_entry']
            if not utils.check_hash_id_existence(self.db_configs.conn, parent_entry) and parent_entry != '':
                    flask.flash('Parent entry does not exist')
                    return flask.redirect(flask.url_for('entry', id=id))

            success_bool = operators.update_entry_in_db(self.db_configs.conn, id, post_form, app.config, hash_id, flask.request.files.getlist('Files'))

            if success_bool:
                message = 'entry is updated successfully'

            else:
                message = 'Something went wrong'

            flask.flash(message)
            return flask.redirect(flask.url_for('index'))

        @app.route("/entry/<int:id>/delete_entry", methods=["POST", "GET"])
        @security.login_required
        @self.logger
        def delete_entry(id):
            entry = utils.get_entry_by_id(self.db_configs.conn, id)
            author = entry[5]
            author = entry[5]
            usename = flask.session['username']
            admin = flask.session['admin']
            if author != usename and not admin:
                flask.flash('You are not allowed to delete this entry')
                return flask.redirect(flask.url_for('entry', id=id))

            success_bool = operators.delete_entry_from_db(self.db_configs.conn, id)

            if success_bool:
                message = 'entry is deleted successfully'

            else:
                message = 'Something went wrong'

            flask.flash(message)
            return flask.redirect(flask.url_for('index'))
        
        @app.route("/protocols", methods=["POST", "GET"])
        @security.login_required
        def protocols():
            # list all files in the protocols folder
            dirName = os.path.join(app.config['DATABASE_FOLDER'], 'protocols')
            List = os.listdir(dirName)

            for count, filename in enumerate(List):
                List[count] = filename

            protocols_file_list = List
            return flask.render_template('protocols.html', Files=protocols_file_list)

        @app.route("/conditions_templates", methods=["POST", "GET"])
        @security.login_required
        def conditions_templates():
            conditions_list = utils.list_user_conditoins_templates(self.db_configs.conn, self.app.config, flask.session)
            return flask.render_template('user_condition_templates.html', conditions_list=conditions_list)

        @app.route("/update_conditions_templates_in_db", methods=["POST", "GET"])
        @security.login_required
        @self.logger
        def update_conditions_templates_in_db():
            post_form = flask.request.form
            success_bool = operators.update_conditions_templates(self.db_configs.conn, post_form, flask.session['username'])

            if success_bool:
                message = 'Conditions template is updated successfully'
            else:
                message = 'Something went wrong'

            flask.flash(message)
            return flask.redirect(flask.url_for('conditions_templates'))

        @app.route("/profile", methods=["POST", "GET"])
        @security.login_required
        def profile():
            username = flask.session['username']
            cursor = self.db_configs.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            # get columns names from the table
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            columns = [column[1] for column in columns]
            # coonvert user to dict with columns as keys
            user = dict(zip(columns, user))
            user_html = flask.render_template('user_profile_template.html', user=user)
            user_html = Markup(user_html)
            return flask.render_template('profile.html', user_html=user_html)

        @app.route("/<path:filename>")
        def static_dir(filename):
            allowed_files = [os.path.join('static', 'js', 'JavaScript.js'), 
                             os.path.join('static', 'css', 'style.css'), 
                             os.path.join('static', 'css', 'bootstrap.min.css'),
                             os.path.join('static', 'assets', 'loading.gif'),]
            if filename in allowed_files:
                return flask.send_from_directory(app.root_path, filename)
            else:
                return flask.redirect(flask.url_for('login'))

        @app.route('/send_entry_file/<int:entry_id>/<path:path>')
        @security.login_required
        def send_entry_file(entry_id, path):
            if '/' not in path:
                cwd = os.getcwd()
                cwd = os.path.join(cwd, app.config['UPLOAD_FOLDER'])
                hash_id = utils.get_hash_id_by_entry_id(self.db_configs.conn, entry_id)
                path = os.path.join(hash_id, path)
                return flask.send_from_directory(cwd, path, as_attachment=True)

        @app.route('/send_protocol_file/<path:path>')
        @security.login_required
        def send_protocol_file(path):
            if '/' not in path:
                cwd = os.getcwd()
                cwd = os.path.join(cwd, app.config['DATABASE_FOLDER'], 'protocols')
                return flask.send_from_directory(cwd, path, as_attachment=True)

        @app.route('/get_conditoin_by_templatename_methodname', methods=["POST", "GET"])
        @security.login_required
        def get_conditoin_by_templatename_methodname():

            username = flask.session['username']
            template_name = flask.request.form.get("template_name")
            method_name = flask.request.form.get("method_name")
            condition_html = utils.get_conditions_by_template_and_method(self.db_configs.conn, app.config, username, template_name, method_name)
            return condition_html

        @app.route('/entry_report_maker/<int:id>', methods=["POST", "GET"])
        @security.login_required
        @self.logger
        def entry_report_maker(id):
            cwd = os.getcwd()
            cwd = os.path.join(cwd, app.config['DATABASE_FOLDER'], 'reports')
            entry_report = utils.entry_report_maker(self.db_configs.conn, id)
            file_path = os.path.join(cwd, f'report_{id}.txt')
            with open(file_path, 'w') as f:
                f.write(entry_report)
            return flask.send_from_directory(cwd,  f'report_{id}.txt',as_attachment=True)

        @app.route('/entries_actions', methods=["POST", "GET"])
        @security.login_required
        @self.logger
        def entries_actions():
            if flask.request.method == 'POST':
                post_form = flask.request.form
                entries_ids = []
                action = post_form['action']  
                for key in post_form:
                    if '&' in key:
                        if key.split('&')[0] == 'Select':
                            entries_ids.append(int(key.split('&')[1]))

                if len(entries_ids) == 0:
                    flask.flash('No entries were selected')
                    return flask.redirect(flask.request.referrer)

                if action == 'bulk_report':
                    cwd = os.getcwd()
                    cwd = os.path.join(cwd, app.config['DATABASE_FOLDER'], 'reports')
                    username = flask.session['username']
                    file_path = os.path.join(cwd, f'bulk_report_{username}.txt')
                    with open(file_path, 'w') as f:
                        for id in entries_ids:
                            entry_report = utils.entry_report_maker(self.db_configs.conn, id)
                            f.write(entry_report)
                            f.write(f"\n\n{'-'*20}\n\n")
                    return flask.send_from_directory(cwd, f'bulk_report_{username}.txt', as_attachment=True)

                elif action == 'set_parent_entry':
                    parent_entry_hash_id = post_form['parent_entry_hash_id']
                    if utils.check_hash_id_existence(self.db_configs.conn, parent_entry_hash_id):
                        for id in entries_ids:
                            utils.set_parent_entry(self.db_configs.conn, id, parent_entry_hash_id)
                        flask.flash('Parent entry was set successfully')
                        return flask.redirect(flask.request.referrer)
                    else:
                        flask.flash('Parent entry Hash ID does not exist')
                        return flask.redirect(flask.request.referrer)
                    
                elif action == "notify_by_email":
                    user_names  = post_form['adress_for_notify_by_email']
                    email_addresses = [utils.get_email_address_by_user_name(self.db_configs.conn, user_name) for user_name in user_names.split(',')]
                    for id in entries_ids:
                        entry_report = utils.entry_report_maker(self.db_configs.conn, id)
                        host_url = self.host_url
                        link2entry = f"{host_url}/entry/{id}"
                        sender_email_address = app.config['CREDS_FILE']['SENDER_EMAIL_ADDRESS']
                        sender_username = flask.session['username']
                        for receiver_email_address in email_addresses:
                            args = {'receiver_email': receiver_email_address, 
                                    'sender_email': sender_email_address, 
                                    'password': app.config['CREDS_FILE']['SENDER_EMAIL_PASSWORD'], 
                                    'subject': f'Entry report notification (by {sender_username})',
                                    'txt': entry_report,
                                    'link2entry': link2entry,
                                    'sender_username': sender_username
                            }
                            mailing.send_report_mail(args)

                    flask.flash('Emails were sent successfully')
                    return flask.redirect(flask.request.referrer)

        @app.route('/chatroom', methods=["GET", "POST"])
        @security.login_required
        def chatroom():
            messages = self.ChatRoom.get_messages()
            users = utils.get_users(self.db_configs.conn)
            users.insert(0, {'username': 'Group Chat'})
            for i, user in enumerate(users):
                if user['username'] == flask.session['username']:
                    users.insert(1, users.pop(i))
                    break
            return flask.render_template('chat_room.html', messages=messages, users=users)

        @app.route('/chatroom_send_message/<string:destination>', methods=["GET", "POST"])
        @security.login_required
        @self.logger
        def chatroom_send_message(destination):
            message = flask.request.form.get('message')
            username = flask.session['username']
            time_now = dt.datetime.now()
            time_now = time_now.strftime("%d/%m/%Y %H:%M:%S")
            message = {'author': username, 'message': message, 'date_time':time_now, 'destination': destination}
            self.ChatRoom.add_message(message)
            return flask.redirect(flask.url_for('chatroom'))

        @app.route('/chatroom_delete_message/<int:id>', methods=["GET", "POST"])
        @security.login_required
        @self.logger
        def chatroom_delete_message(id):
            self.ChatRoom.delete_message(id)
            return flask.redirect(flask.url_for('chatroom'))

        @app.route('/logs', methods=["GET", "POST"])
        @security.admin_required
        def logs():
            cusor = self.db_configs.conn.cursor()
            # get all logs since last 7 days
            cusor.execute("SELECT * FROM logs WHERE date > date('now', '-7 days')")
            logs = cusor.fetchall()
            columns = [column[0] for column in cusor.description]
            logs = [dict(zip(columns, row)) for row in logs]
            return flask.render_template('logs.html', logs=logs)

        @app.route('/backup', methods=["GET", "POST"])
        @security.admin_required
        @self.logger
        def backup():
            if flask.request.method == 'POST':
                status, backup_file_path = utils.backup_db(self.app.config)
                if status:
                    return flask.send_from_directory(os.path.dirname(backup_file_path), os.path.basename(backup_file_path), as_attachment=True)
                else:
                    flask.flash('Database was not backed up successfully')
                    return flask.render_template('backup.html')
            else:
                return flask.render_template('backup.html')

        @app.route('/restore_db', methods=["GET", "POST"])
        @security.admin_required
        @self.logger
        def restore_db():
            if flask.request.method == 'POST':
                Files = flask.request.files.getlist('Files')
                file = Files[0]
                if file.filename.split('.')[-1] != 'zip':
                    flask.flash('Wrong file format / No file was selected')
                    return flask.render_template('backup.html')
                else:
                    backup_file_path = os.path.join(app.config['DATABASE_FOLDER'], 'backup.zip')
                    file.save(backup_file_path)
                    status = utils.restore_db(self.app.config, backup_file_path)
                    if status:
                        flask.flash('Database was restored successfully. Please restart the server')                        
                    else:
                        flask.flash('Database was not restored. Please try again')
                    return flask.render_template('backup.html')
                
        @app.route('/editor/', methods=["GET", "POST"])
        @security.admin_required
        @self.logger
        def editor():
            return flask.url_for('editor')

            
        # t = Thread(target=waitress.serve, args=([self.app]), kwargs={'host':self.ip, 'port':self.port, 'threads':self.num_threads})
        # t.start()     
        waitress.serve(self.app, host=self.ip, port=self.port)
        