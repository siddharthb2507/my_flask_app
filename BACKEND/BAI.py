from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_bai(red_band_bytes, nir_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)

    # Calculate bai
    with np.errstate(divide='ignore', invalid='ignore'):
        bai = 1/((0.1 - red_array.astype(float))**2 + (0.06 - nir_array.astype(float))**2)  
    bai = np.nan_to_num(bai)
    bai = np.clip(bai, -1, 1)  # Ensure bai values are between -1 and 1

    # Update the metadata for the output bai GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': bai.dtype
    })

    # Save bai as a GeoTIFF
    bai_buffer = io.BytesIO()
    with rasterio.open(bai_buffer, 'w', **red_meta) as dst:
        dst.write(bai, 1)

    bai_buffer.seek(0)
    return bai_buffer

@app.route('/calculate_bai', methods=['POST'])
def process_bai():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    bai_buffer = calculate_bai(red_band_bytes, nir_band_bytes)
    return send_file(bai_buffer, mimetype='image/tiff', download_name='bai.tif')

if __name__ == '__main__':
    app.run(debug=True)