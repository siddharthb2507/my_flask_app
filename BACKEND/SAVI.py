from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_savi(red_band_bytes, nir_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)

    # Calculate savi
    with np.errstate(divide='ignore', invalid='ignore'):
        savi = ((nir_array.astype(float) - red_array.astype(float)) / (nir_array.astype(float) + red_array.astype(float)+0.5))*(1+0.5)
    savi = np.nan_to_num(savi)
    savi = np.clip(savi, -1, 1)  # Ensure savi values are between -1 and 1

    # Update the metadata for the output savi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': savi.dtype
    })

    # Save savi as a GeoTIFF
    savi_buffer = io.BytesIO()
    with rasterio.open(savi_buffer, 'w', **red_meta) as dst:
        dst.write(savi, 1)

    savi_buffer.seek(0)
    return savi_buffer

@app.route('/calculate_savi', methods=['POST'])
def process_savi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    savi_buffer = calculate_savi(red_band_bytes, nir_band_bytes)
    return send_file(savi_buffer, mimetype='image/tiff', download_name='savi.tif')

if __name__ == '__main__':
    app.run(debug=True)