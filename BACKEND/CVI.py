from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_cvi(red_band_bytes, nir_band_bytes, green_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)
    green_image = Image.open(green_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)
    green_array = np.array(green_image)

    # Calculate cvi
    with np.errstate(divide='ignore', invalid='ignore'):
        cvi = ((nir_array.astype(float)) / (green_array.astype(float))) * ((red_array.astype(float)) / (green_array.astype(float)))
    cvi = np.nan_to_num(cvi)
    cvi = np.clip(cvi, -1, 1)  # Ensure cvi values are between -1 and 1

    # Update the metadata for the output cvi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': cvi.dtype
    })

    # Save cvi as a GeoTIFF
    cvi_buffer = io.BytesIO()
    with rasterio.open(cvi_buffer, 'w', **red_meta) as dst:
        dst.write(cvi, 1)

    cvi_buffer.seek(0)
    return cvi_buffer

@app.route('/calculate_cvi', methods=['POST'])
def process_cvi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    cvi_buffer = calculate_cvi(red_band_bytes, nir_band_bytes, green_band_bytes)
    return send_file(cvi_buffer, mimetype='image/tiff', download_name='cvi.tif')

if __name__ == '__main__':
    app.run(debug=True)