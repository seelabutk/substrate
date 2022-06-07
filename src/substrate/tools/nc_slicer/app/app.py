from flask import Flask, request, render_template, send_file, jsonify
from grapher import *
from utils import *
import tempfile
from io import BytesIO
import json
app = Flask(__name__)

dataloc = '/data/'

@app.route('/', methods=["GET", "POST"])
def gfg():
    return render_template("index.html")

@app.route('/getVariableNames/', methods=['POST'])
def getVarNames():
    body = request.get_json()
    path = body['ncpath']
    return jsonify(getVariableNames(dataloc + path + '.nc'))

@app.route('/render/', methods=["GET", "POST"])
def render():
    if request.method == 'POST': 
        body = request.get_json()

        ncpath = body['ncpath']
        variable =  body['variable']
        date = body['date']
        sdate = str(date).split('-')
        date = sdate[1]
        date += "/"
        date += sdate[2]
        date += "/"
        date += sdate[0]

        hour = body['hour']
        plt = graph(dataloc + ncpath + ".nc", variable, date, hour, ncpath)

        with tempfile.NamedTemporaryFile("r+b", delete=True) as fd:
            file_name = fd.name + '.png'
            plt.savefig(file_name)
            plt.close("all")

        with open(file_name, 'rb') as image:
            image_data = BytesIO(image.read())

        return send_file(image_data, mimetype='image/png')

@app.route('/data/', methods=["POST"])
def get_data():
    data = request.get_json()
    body = json.loads(data) 
    ncpath = body['ncpath']
    variable =  body['variable']
    date = body['date']
    hour = body['hour']
        
    numpy_arr = get_numpy(dataloc + ncpath + ".nc", variable, date, hour)

    return jsonify(numpy_arr.tolist())

if __name__ == "__main__":
    app.run(host='0.0.0.0')
