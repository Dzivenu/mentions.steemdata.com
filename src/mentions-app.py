import os

from flask import Flask, render_template
from flask_misaka import Misaka
from flask_pymongo import PyMongo

from methods import perform_query

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.config['MONGO_URI'] = 'mongodb://steemit:steemit@mongo1.steemdata.com:27017/SteemData'

mongo = PyMongo(app)

# enable markdown rendering
md_features = ['autolink', 'fenced_code', 'underline', 'highlight', 'quote',
               'math', 'superscript', 'tables', 'wrap']
md_features = {x: True for x in md_features}
Misaka(app, **md_features)

@app.route('/')
def hello_world():
    results = perform_query(mongo, search='furion python', sort_by='payout')
    return render_template('index.html', results=results)


@app.route('/health')
def health():
    return []


@app.template_filter('humanDate')
def humanize_date(s):
    # test = maya.parse(s)
    return s


if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'),
            debug=not os.getenv('PRODUCTION', False))
