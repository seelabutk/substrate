import tempfile
import json

from datetime import timedelta
from io import BytesIO
from functools import update_wrapper

from flask import Flask, request, render_template, send_file, jsonify, current_app, make_response
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/', methods=["GET", "POST"])
@cross_origin()
def main():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0')