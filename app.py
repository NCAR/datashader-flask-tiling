# import libraries
from flask import Flask, send_file, render_template, jsonify, request
# from flask_socketio import SocketIO

import io
import math

import datashader as ds
import pandas as pd
import xarray as xr
import colorcet

from datashader import transfer_functions as tf
from datashader.utils import lnglat_to_meters

# import dataset
data = xr.open_dataset("static/data/TS2023_reproject.nc")
time_data = xr.open_dataset("static/data/TS_annual_reproject.nc")

# find min/max data values to set global colorbar
min_val = float(data['TS'].min())
max_val = float(data['TS'].max())

# extract dimensions
lon_array = data['x']
lat_array = data['y']
data_array = data['TS']
time_data_array = time_data['TS']

# following function from ScottSyms tileshade repo under the GNU General Public License v3.0.
# https://github.com/ScottSyms/tileshade/
def tile2mercator(xtile, ytile, zoom):
    # takes the zoom and tile path and passes back the EPSG:3857
    # coordinates of the top left of the tile.
    # From Openstreetmap
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)

    # Convert the results of the degree calulation above and convert
    # to meters for web map presentation
    mercator = lnglat_to_meters(lon_deg, lat_deg)
    return mercator

# following function adapted from ScottSyms tileshade repo under the GNU General Public License v3.0.
# https://github.com/ScottSyms/tileshade/
# changes made: snapping values to ensure continuous tiles; use of quadmesh instead of points; syntax changes to work with Flask.
def generateatile(zoom, x, y):
    # The function takes the zoom and tile path from the web request,
    # and determines the top left and bottom right coordinates of the tile.
    # This information is used to query against the dataframe.
    xleft, yleft = tile2mercator(int(x), int(y), int(zoom))
    xright, yright = tile2mercator(int(x)+1, int(y)+1, int(zoom))

    # ensuring no gaps are left between tiles due to partitioning occurring between coordinates.
    xleft_snapped = lon_array.sel(x=xleft, method="nearest").values
    yleft_snapped = lat_array.sel(y=yleft, method="nearest").values
    xright_snapped = lon_array.sel(x=xright, method="nearest").values
    yright_snapped = lat_array.sel(y=yright, method="nearest").values

    # The dataframe query gets passed to Datashader to construct the graphic.
    xcondition = "x >= {xleft_snapped} and x <= {xright_snapped}".format(xleft_snapped=xleft_snapped, xright_snapped=xright_snapped)
    ycondition = "y <= {yleft_snapped} and y >= {yright_snapped}".format(yleft_snapped=yleft_snapped, yright_snapped=yright_snapped)
    frame = data.query(x=xcondition, y=ycondition)

    # First the graphic is created, then the dataframe is passed to the Datashader aggregator.
    csv = ds.Canvas(plot_width=256, plot_height=256, x_range=(min(xleft-10, xright), max(
        xleft, xright)), y_range=(min(yleft, yright), max(yleft, yright)))
    agg = csv.quadmesh(frame, x='x', y='y', agg=ds.mean('TS'))

    # The image is created from the aggregate object, a color map and aggregation function.
    img = tf.shade(agg, cmap=colorcet.coolwarm, span=[min_val, max_val], how="linear")
    return img.to_pil()

app = Flask(__name__)

# socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/tiles/<int:zoom>/<int:x>/<int:y>.png")
def tile(x, y, zoom):
    results = generateatile(zoom, x, y)
    # image passed off to bytestream
    results_bytes = io.BytesIO()
    results.save(results_bytes, 'PNG')
    results_bytes.seek(0)
    return send_file(results_bytes, mimetype='image/png')

@app.route('/time-series', methods=['POST'])
def get_time_series():
    request_data = request.get_json()
    latitude = request_data['latitude']
    longitude = request_data['longitude']

    df_slice = time_data_array.sel(x=longitude, y=latitude, method="nearest")
    df_slice = df_slice.to_dataframe().reset_index()[['year', 'TS']]

    # convert the DataFrame to JSON
    json_data = df_slice.to_json(orient='records')
    
    # send the JSON response
    return jsonify(data=json_data)

# @socketio.on('mousemove')
# def handle_mousemove(coords):
#     # process the coordinates received from the client
#     value = data_array.sel(x=coords['lng'], y=coords['lat'], method="nearest")
#     socketio.emit('updated_coordinates', float(value.values))  # Emit the queried value back to the client

# if __name__ == '__main__':
#     socketio.run(app)


if __name__ == '__main__':
   app.run(debug=True)