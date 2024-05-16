from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_osavi(red_band_bytes, nir_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)

    # Calculate osavi
    with np.errstate(divide='ignore', invalid='ignore'):
        osavi = (nir_array.astype(float) - red_array.astype(float)) / (nir_array.astype(float) + red_array.astype(float) + 0.16)
    osavi = np.nan_to_num(osavi)
    osavi = np.clip(osavi, -1, 1)  # Ensure osavi values are between -1 and 1

    # Update the metadata for the output osavi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': osavi.dtype
    })

    # Save osavi as a GeoTIFF
    osavi_buffer = io.BytesIO()
    with rasterio.open(osavi_buffer, 'w', **red_meta) as dst:
        dst.write(osavi, 1)

    osavi_buffer.seek(0)
    return osavi_buffer

@app.route('/calculate_osavi', methods=['POST'])
def process_osavi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    osavi_buffer = calculate_osavi(red_band_bytes, nir_band_bytes)
    return send_file(osavi_buffer, mimetype='image/tiff', download_name='osavi.tif')

if __name__ == '__main__':
    app.run(debug=True)