import sys
import pathlib
import os
parent_parent_path = str(pathlib.Path(__file__).parent.parent.absolute())
sys.path.append(os.path.join(parent_parent_path, 'utils'))

import utils
from dictianory import slef_made_codes
import sqlite3
from sqlite3 import Error
import itertools

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        print('Connected to database using SQLite', sqlite3.version)
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        utils.error_log(e)

### entries
def insert_entry_to_db(conn, Author, date, Tags, File_Path, Notes, conditions, entry_name, parent_entry):
    try:
        conditions_parsed = utils.parse_conditions(conditions)
        Tags_parsed = utils.parse_tags(Tags)
        insert_tag(conn, Tags_parsed)
        insert_conditions(conn, conditions_parsed)
        insert_author(conn, Author)
        cursor = conn.cursor()
        hash_id = utils.generate_hash(conn)
        rows = [(hash_id, Tags, Notes, File_Path, date, Author, conditions, entry_name, parent_entry, None)]
        cursor.executemany('insert into entries values (?,?,?,?,?,?,?,?,?,?)', rows)
        conn.commit()
        success_bool = 1
    except Error as e:
        utils.error_log(e)
        success_bool = 0
        hash_id = None
    return success_bool, hash_id

def update_entry_in_db(conn, id, post_form, app_config, hash_id, Files):
    try:
        date = post_form['date']
        Tags = post_form['Tags']
        File_Path = post_form['File_Path']
        Notes = post_form['Notes']
        entry_name = post_form['entry_name']
        parent_entry = post_form['parent_entry']

        Tags_parsed = utils.parse_tags(Tags)
        insert_tag(conn, Tags_parsed)

        if len(Files) > 0:
            utils.upload_files(app_config, hash_id, Files)

        Files2remove = []
        for form_input in post_form:
            try:
                if slef_made_codes[form_input.split('&')[0]] == 'remove':
                    Files2remove.append(form_input.split('&')[1])
            except:
                pass

        if len(Files2remove) > 0:
            utils.remove_files(app_config, hash_id, Files2remove)

        conditions = []
        for form_input in post_form:
            if 'condition' == form_input.split('&')[0]:
                conditions.append('&'.join(form_input.split('&')[1:]))
            elif 'PARAM' == form_input.split('&')[0]:
                list_tmp = form_input.split('&')[2:]
                list_tmp.append(post_form[f"PARAMVALUE&{'&'.join(form_input.split('&')[1:])}"].split('&')[-1])
                list_tmp = '&'.join(list_tmp)
                conditions.append(list_tmp)
                
        conditions = ','.join(conditions)
        cursor = conn.cursor()
        rows = [(Tags, Notes, File_Path, date, conditions, entry_name, parent_entry, id)]
        cursor.executemany('update entries set tags=?, extra_txt=?, file_path=?, date=?, conditions=?, entry_name=?, entry_parent=? where id=?', rows)
        conn.commit()
        success_bool = 1

    except Error as e:
        utils.error_log(e)
        success_bool = 0
    return success_bool

def delete_entry_from_db(conn, id):
    try:
        hash_id = utils.get_hash_id_by_entry_id(conn, id)
        cursor = conn.cursor()
        cursor.execute('delete from entries where id=?', (id,))
        conn.commit()
        remove_deleted_entry_as_parent(conn, hash_id)
        delete_author(conn, id)
        success_bool = 1
    except Error as e:
        utils.error_log(e)
        success_bool = 0
    return success_bool


def remove_deleted_entry_as_parent(conn, hash_id):
    try:
        cursor = conn.cursor()
        cursor.execute("update entries set entry_parent='' where entry_parent=?", (hash_id,))
        conn.commit()
        success_bool = 1
    except Error as e:
        utils.error_log(e)
        success_bool = 0
    return success_bool
### entries


### Tags
def insert_tag(conn, Tags_parsed):
    try:
        for tag in Tags_parsed:
            if not utils.check_existence_tag(conn, tag):
                cursor = conn.cursor()
                rows = [(tag, None)]
                cursor.executemany('insert into tags values (?, ?)', rows)
                conn.commit()
        success_bool = 1
    except Error as e:
        utils.error_log(e)
        success_bool = 0
    return success_bool
### Tags


### Authors
def insert_author(conn, Author):
    try:
        if not utils.check_existence_author(conn, Author):
            cursor = conn.cursor()
            rows = [(Author, None)]
            cursor.executemany('insert into authors values (?, ?)', rows)
            conn.commit()
        success_bool = 1
    except Error as e:
        utils.error_log(e)
        success_bool = 0
    return success_bool

def delete_author(conn, id):
    if not utils.check_existence_author(conn, id):
        cursor = conn.cursor()
        cursor.execute('delete from authors where id=?', (id,))
        conn.commit()
### Authors


### Conditions
def insert_conditions(conn, conditions):
    try:
        for condition in conditions:
            if not utils.check_existence_condition(conn, condition):
                cursor = conn.cursor()
                rows = [(condition, None)]
                cursor.executemany('insert into conditions values (?, ?)', rows)
                conn.commit()
        success_bool = 1
    except Error as e:
        utils.error_log(e)
        success_bool = 0
    return success_bool

def update_conditions_templates(conn, post_form, username):
    post_form = post_form.to_dict()
    new_template_name = post_form['new_template_name']
    conditions = []
    for key, _ in post_form.items():
        if 'condition' == key.split('&')[0]:
            conditions.append(key.split('&')[1:])
        elif 'PARAM' == key.split('&')[0]:
            list_tmp = key.split('&')[2:]
            list_tmp.append(post_form[f"PARAMVALUE&{'&'.join(key.split('&')[1:])}"].split('&')[-1])
            conditions.append(list_tmp)
    conditions_dict = {}
    for key, group in itertools.groupby(conditions, lambda x: x[0]):
        conditions_dict[key] = list(group)
    for template_name in conditions_dict.keys():
        condition_this_template_list = conditions_dict[template_name]
        for indx, condition_this_template in enumerate(condition_this_template_list):
            condition_this_template_list[indx] = '&'.join(condition_this_template[1:])
        condition_this_template_list = ','.join(condition_this_template_list)
        cursor = conn.cursor()
        if template_name == 'default':
            cursor.execute('insert into conditions_templates values (?, ?, ?, ?)', (username, new_template_name, condition_this_template_list, None))
        elif template_name != '':
            cursor.execute('update conditions_templates set conditions=? where author=? and template_name=?', (condition_this_template_list, username, template_name))
        conn.commit()
    
    for key, _ in post_form.items():
        if 'delete' == key.split('&')[0]:
            # remove template
            template_name = key.split('&')[1]
            cursor = conn.cursor()
            cursor.execute('delete from conditions_templates where author=? and template_name=?', (username, template_name))
            conn.commit()
            
    return True
### Conditions