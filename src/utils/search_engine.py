import flask
from flask import jsonify
import utils

def author_search_in_db(conn, keyword):
    if keyword != '' and keyword != ' ':
        try:
            cursor = conn.cursor()
            cursor.execute("select *  FROM authors WHERE author LIKE ?", (f"%{keyword}%",))
            result = cursor.fetchall()
        except:
            result = None
    else:
        result = None
    return jsonify(result)

def tags_search_in_db(conn, keyword):
    if keyword != '' and keyword != ' ':
        keyword = keyword.split(',')
        keyword = keyword[-1]
        try:
            cursor = conn.cursor()
            cursor.execute("select *  FROM tags WHERE tag LIKE ?", (f"%{keyword}%",))
            result = cursor.fetchall()
        except:
            result = None
    else:
        result = None
    return jsonify(result)

def text_search_in_db(conn, keyword):
    print(keyword)
    if keyword != '' and keyword != ' ':
        try:
            cursor = conn.cursor()
            cursor.execute("select *  FROM entries WHERE extra_txt LIKE ?", (f"%{keyword}%",))
            result = cursor.fetchall()
        except:
            result = None
    else:
        result = None
    for i,r in enumerate(result):
        r = list(r)
        index = r[2].find(keyword)
        r[2] = r[2][index-20:index+20]
        r = [r[2], r[-1]]
        result[i] = tuple(r)
    return jsonify(result)

def title_search_in_db(conn, keyword):
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT entry_name FROM entries WHERE entry_name LIKE ? LIMIT 10", (f'%{keyword}%',))
    results = cursor.fetchall()
    return flask.jsonify(results)

def keyword_search_in_db(conn, keyword):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT entry_name FROM entries 
        WHERE entry_name LIKE ? OR tags LIKE ? OR conditions LIKE ? OR extra_txt LIKE ? 
        LIMIT 10
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    results = cursor.fetchall()
    return flask.jsonify(results)

def filter_entries(conn, post_request_form):
    Authors = post_request_form['Author']
    Hash_ID = post_request_form['Hash_ID']
    Text = post_request_form.get('Text', '')
    Tags = post_request_form.get('Tags', '')
    Title = post_request_form.get('Title', '')
    Keyword = post_request_form.get('Keyword', '')
    
    if 'date_bool' not in post_request_form:
        date_bool = False
    else:
        date_bool = True
    if not date_bool:
        date_start = '0001-01-01'
        date_end = '9999-12-31'
    else:
        date_start = post_request_form['date_start']
        date_end = post_request_form['date_end']
    
    # We're no longer processing conditions as per requirements
    conditions = []
    
    rows = []
    if Hash_ID != '':
        sql_command = 'SELECT * FROM entries WHERE id_hash like ? AND ' 
        rows.append(f'%{Hash_ID}%')
    else:
        sql_command = 'SELECT * FROM entries WHERE '
        if Authors != '':
            sql_command += 'author == ? AND '
            rows.append(Authors)
        
        # Handle the new Keyword field that searches across multiple columns
        if Keyword != '':
            sql_command += '('
            sql_command += 'entry_name like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'tags like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'conditions like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'extra_txt like ?'
            rows.append(f'%{Keyword}%')
            sql_command += ') AND '
        
        # Handle individual field searches from advanced search
        if Title != '':
            sql_command += 'entry_name like ? AND '
            rows.append(f'%{Title}%')
        if Text != '':
            sql_command += 'extra_txt like ? AND '
            rows.append(f'%{Text}%')
        if date_start != '':
            sql_command += 'date >= ? AND '
            rows.append(date_start)
        if date_end != '':
            sql_command += 'date <= ? AND '
            rows.append(date_end)
        if Tags != '':
            Tags = Tags.split(',')
            for tag in Tags:
                if tag != '':
                    sql_command += 'tags like ? AND '
                    rows.append(f'%{tag}%')
    
    sql_command = sql_command + '1'
    rows = tuple(rows)
    cursor = conn.cursor()
    cursor.execute(sql_command, rows)
    entries_list = cursor.fetchall()
    entries_list = utils.entry_list_maker(entries_list)
    return entries_list

def realtime_filter_entries(conn, search_params, offset=0, limit=10):
    """
    Filter entries based on search parameters for real-time search.
    Returns a limited number of entries for pagination.
    """
    Authors = search_params.get('Author', '')
    Hash_ID = search_params.get('Hash_ID', '')
    Text = search_params.get('Text', '')
    Tags = search_params.get('Tags', '')
    Title = search_params.get('Title', '')
    Keyword = search_params.get('Keyword', '')
    
    # Handle date range
    if 'date_bool' not in search_params or search_params.get('date_bool') != 'on':
        date_start = '0001-01-01'
        date_end = '9999-12-31'
    else:
        date_start = search_params.get('date_start', '0001-01-01')
        date_end = search_params.get('date_end', '9999-12-31')
    
    rows = []
    if Hash_ID != '':
        sql_command = 'SELECT * FROM entries WHERE id_hash like ? AND ' 
        rows.append(f'%{Hash_ID}%')
    else:
        sql_command = 'SELECT * FROM entries WHERE '
        if Authors != '':
            sql_command += 'author like ? AND '
            rows.append(f'%{Authors}%')
        
        # Handle the Keyword field that searches across multiple columns
        if Keyword != '':
            sql_command += '('
            sql_command += 'entry_name like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'tags like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'conditions like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'extra_txt like ?'
            rows.append(f'%{Keyword}%')
            sql_command += ') AND '
        
        # Handle individual field searches from advanced search
        if Title != '':
            sql_command += 'entry_name like ? AND '
            rows.append(f'%{Title}%')
        if Text != '':
            sql_command += 'extra_txt like ? AND '
            rows.append(f'%{Text}%')
        if date_start != '':
            sql_command += 'date >= ? AND '
            rows.append(date_start)
        if date_end != '':
            sql_command += 'date <= ? AND '
            rows.append(date_end)
        if Tags != '':
            Tags = Tags.split(',')
            for tag in Tags:
                if tag != '':
                    sql_command += 'tags like ? AND '
                    rows.append(f'%{tag}%')
    
    sql_command = sql_command + '1 ORDER BY date DESC LIMIT ? OFFSET ?'
    rows.append(limit)
    rows.append(offset)
    
    rows = tuple(rows)
    cursor = conn.cursor()
    cursor.execute(sql_command, rows)
    entries_list = cursor.fetchall()
    entries_list = utils.entry_list_maker(entries_list)
    return entries_list

def count_matching_entries(conn, search_params):
    """
    Count the total number of entries matching the search parameters.
    Used for pagination in real-time search.
    """
    Authors = search_params.get('Author', '')
    Hash_ID = search_params.get('Hash_ID', '')
    Text = search_params.get('Text', '')
    Tags = search_params.get('Tags', '')
    Title = search_params.get('Title', '')
    Keyword = search_params.get('Keyword', '')
    
    # Handle date range
    if 'date_bool' not in search_params or search_params.get('date_bool') != 'on':
        date_start = '0001-01-01'
        date_end = '9999-12-31'
    else:
        date_start = search_params.get('date_start', '0001-01-01')
        date_end = search_params.get('date_end', '9999-12-31')
    
    rows = []
    if Hash_ID != '':
        sql_command = 'SELECT COUNT(*) FROM entries WHERE id_hash like ? AND ' 
        rows.append(f'%{Hash_ID}%')
    else:
        sql_command = 'SELECT COUNT(*) FROM entries WHERE '
        if Authors != '':
            sql_command += 'author like ? AND '
            rows.append(f'%{Authors}%')
        
        # Handle the Keyword field that searches across multiple columns
        if Keyword != '':
            sql_command += '('
            sql_command += 'entry_name like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'tags like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'conditions like ? OR '
            rows.append(f'%{Keyword}%')
            sql_command += 'extra_txt like ?'
            rows.append(f'%{Keyword}%')
            sql_command += ') AND '
        
        # Handle individual field searches from advanced search
        if Title != '':
            sql_command += 'entry_name like ? AND '
            rows.append(f'%{Title}%')
        if Text != '':
            sql_command += 'extra_txt like ? AND '
            rows.append(f'%{Text}%')
        if date_start != '':
            sql_command += 'date >= ? AND '
            rows.append(date_start)
        if date_end != '':
            sql_command += 'date <= ? AND '
            rows.append(date_end)
        if Tags != '':
            Tags = Tags.split(',')
            for tag in Tags:
                if tag != '':
                    sql_command += 'tags like ? AND '
                    rows.append(f'%{tag}%')
    
    sql_command = sql_command + '1'
    rows = tuple(rows)
    cursor = conn.cursor()
    cursor.execute(sql_command, rows)
    count = cursor.fetchone()[0]
    return count

def entries_time_line(conn):
    cursor = conn.cursor()
    if flask.session['admin']:
        cursor.execute("SELECT * FROM entries ORDER BY date DESC LIMIT 12")         
    else:
        cursor.execute("SELECT * FROM entries WHERE author == ? ORDER BY date DESC LIMIT 12", (flask.session['username'],))                              
    entries_list = cursor.fetchall()
    entries_list=  utils.entry_list_maker(entries_list)
    return entries_list
    