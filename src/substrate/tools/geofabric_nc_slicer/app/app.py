import tempfile
import json

from datetime import timedelta
from grapher import *
from utils import *
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
    app.run(host='0.0.0.0', port=8888, debug=True)

# app.config['CORS_HEADERS'] = 'Content-Type'

# dataloc = '/data/'
# def crossdomain(origin=None, methods=None, headers=None,
#                 max_age=21600, attach_to_all=True,
#                 automatic_options=True):
#     if methods is not None:
#         methods = ', '.join(sorted(x.upper() for x in methods))
#     if headers is not None and not isinstance(headers, str):
#         headers = ', '.join(x.upper() for x in headers)
#     if not isinstance(origin, str):
#         origin = ', '.join(origin)
#     if isinstance(max_age, timedelta):
#         max_age = max_age.total_seconds()

#     def get_methods():
#         if methods is not None:
#             return methods

#         options_resp = current_app.make_default_options_response()
#         return options_resp.headers['allow']

#     def decorator(f):
#         def wrapped_function(*args, **kwargs):
#             if automatic_options and request.method == 'OPTIONS':
#                 resp = current_app.make_default_options_response()
#             else:
#                 resp = make_response(f(*args, **kwargs))
#             if not attach_to_all and request.method != 'OPTIONS':
#                 return resp

#             h = resp.headers

#             h['Access-Control-Allow-Origin'] = origin
#             h['Access-Control-Allow-Methods'] = get_methods()
#             h['Access-Control-Max-Age'] = str(max_age)
#             if headers is not None:
#                 h['Access-Control-Allow-Headers'] = headers
#             return resp

#         f.provide_automatic_options = False
#         return update_wrapper(wrapped_function, f)
#     return decorator



# @app.route('/var/*', methods=["GET", "POST"])
# @cross_origin()
# # @crossdomain(origin="*")
# def test():
#     return render_template("index.html")
# @app.route('/getVariableNames/', methods=['POST'])
# def getVarNames():
#     body = request.get_json()
#     path = body['ncpath']
#     return jsonify(getVariableNames(dataloc + path + '.nc'))

# @app.route('/render/', methods=["GET", "POST"])
# def render():
#     if request.method == 'POST': 
#         body = request.get_json()

#         ncpath = body['ncpath']
#         variable =  body['variable']
#         date = body['date']
#         sdate = str(date).split('-')
#         date = sdate[1]
#         date += "/"
#         date += sdate[2]
#         date += "/"
#         date += sdate[0]

#         hour = body['hour']
#         plt = graph(dataloc + ncpath + ".nc", variable, date, hour, ncpath)

#         with tempfile.NamedTemporaryFile("r+b", delete=True) as fd:
#             file_name = fd.name + '.png'
#             plt.savefig(file_name)
#             plt.close("all")

#         with open(file_name, 'rb') as image:
#             image_data = BytesIO(image.read())

#         return send_file(image_data, mimetype='image/png')

# @app.route('/data/', methods=["POST"])
# def get_data():
#     data = request.get_json()
#     body = json.loads(data) 
#     ncpath = body['ncpath']
#     variable =  body['variable']
#     date = body['date']
#     hour = body['hour']
        
#     numpy_arr = get_numpy(dataloc + ncpath + ".nc", variable, date, hour)

#     return jsonify(numpy_arr.tolist())