from flask import Flask, request, jsonify, abort
import logging
import json

bot_webhook_token = "{BWT}"
bot_api_token = "{BA}"

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world'

@app.route('/reviewgram/')
def reviewgram():
    return 'Hello world'

@app.route('/reviewgram/bot/', methods=['POST', 'GET'])
def bot_api():
    if (request.args.get('token') != bot_webhook_token):
       abort(404)
    data = request.json
    if (data is None):
       abort(404)
    str = jsonify(data)
    text_file = open("/root/reviewgram/log.txt", "a")
    text_file.write(json.dumps(data))
    text_file.write("\n")
    text_file.close()
    return 'Hello world'

gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
