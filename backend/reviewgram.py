from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv, find_dotenv
import logging
import json
import os
import pymysql
import base64
import traceback

load_dotenv(find_dotenv())

bot_webhook_token = os.getenv("BOT_WEBHOOK_TOKEN")
bot_api_token  = os.getenv("BOT_API_TOKEN")

app = Flask(__name__)

def safe_get_key(dict, keys):
    tmp = dict
    for key in keys:
        if key in tmp:
            tmp = tmp[key]
        else:
            return None
    return tmp

@app.route('/')
def index():
    return 'Hello world'


@app.route('/reviewgram/')
def reviewgram():
    return 'Hello world'


@app.route('/reviewgram/bot/', methods=['POST', 'GET'])
def bot_api():
    if request.args.get('token') != bot_webhook_token:
        abort(404)
    data = request.json
    if data is None:
        abort(404)
    try:
        userId = safe_get_key(data, ["message", "from", "id"])
        message = safe_get_key(data, ["message", "text"])
        if ((userId is not None) and (message is not None)):
            decoded = base64.b64decode(message)
            con = pymysql.connect(os.getenv("MYSQL_HOST"), os.getenv("MYSQL_USER"), os.getenv("MYSQL_PASSWORD"), os.getenv("MYSQL_DB"))
            with con:
                cur = con.cursor()
                cur.execute("SELECT COUNT(*) AS CNT FROM `token_to_user_id` WHERE `TOKEN` = %s", [decoded])
                countRows = cur.fetchone()
                cur.close()
                if (countRows[0] > 0):
                    cur = con.cursor()
                    cur.execute("UPDATE `token_to_user_id` SET USER_ID = %s, TSTAMP = UNIX_TIMESTAMP(NOW()) WHERE TOKEN = %s", [userId, decoded])
                    con.commit()
                    cur.close()
                else:
                    cur = con.cursor()
                    cur.execute("INSERT INTO `token_to_user_id`(USER_ID, TOKEN, TSTAMP) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()))", [userId, decoded])
                    con.commit()
                    cur.close()
        else:
            text_file = open("/root/reviewgram/log.txt", "a")
            text_file.write("no data")
            text_file.write("\n")
            text_file.close()
            abort(404)
    except Exception as e:
        text_file = open("/root/reviewgram/log.txt", "a")
        text_file.write("Exception " + traceback.format_exc())
        text_file.write("\n")
        text_file.close()
        abort(404)
    return 'OK'


@app.route('/reviewgram/bot_username/')
def bot_username():
    return os.getenv("BOT_USERNAME")


gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
