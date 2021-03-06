import pymysql
import os


MONKEYPATCH_PYMYSQL_CONNECTION = True


def monkeypatch_pymysql_connection():
    Connection = pymysql.connections.Connection

    def enter_patch(self):
        return self

    def exit_patch(self, exc, value, traceback):
        try:
            self.rollback()  # Implicit rollback when connection closed per PEP-249
        finally:
            self.close()

    Connection.__enter__ = enter_patch
    Connection.__exit__ = exit_patch


if MONKEYPATCH_PYMYSQL_CONNECTION:
    monkeypatch_pymysql_connection()
    MONKEYPATCH_PYMYSQL_CONNECTION = False 

# Соединение с БД
def connect_to_db():
    return pymysql.connect(os.getenv("MYSQL_HOST"), os.getenv("MYSQL_USER"), os.getenv("MYSQL_PASSWORD"), os.getenv("MYSQL_DB"))

# Получение первой строки по запросу из БД
def select_and_fetch_all(con, query, params):
    cur = con.cursor()
    cur.execute(query, params)
    result = cur.fetchall()
    cur.close()
    return result

# Получение первой строки по запросу из БД
def select_and_fetch_one(con, query, params):
    cur = con.cursor()
    cur.execute(query, params)
    result = cur.fetchone()
    cur.close()
    return result

# Получение первой колонки и строки по запросу из БД
def select_and_fetch_first_column(con, query, params):
    row  = select_and_fetch_one(con, query, params)
    if (row is None):
        return None
    else:
        return row[0]

# Выполнение запроса к БД
def execute_update(con, query, params):
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    cur.close()
    
 # Выполнение запроса к БД
def execute_insert(con, query, params):
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    rowid = cur.lastrowid
    cur.close()
    return rowid