import os

from flask import render_template
from flask_api import FlaskAPI
from flask_cors import CORS
from flask_pymongo import PyMongo

app = FlaskAPI(__name__, template_folder='../templates', static_folder='../static')

app.config['MONGO_URI'] = 'mongodb://steemit:steemit@mongo1.steemdata.com:27017/SteemData'

mongo = PyMongo(app)
CORS(app)  # enable cors defaults (*)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/health')
def health():
    return []


if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'),
            debug=not os.getenv('PRODUCTION', False))
