from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_evi(red_band_bytes, nir_band_bytes, blue_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)
    blue_image = Image.open(blue_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)
    blue_array = np.array(blue_image)

    # Calculate evi
    with np.errstate(divide='ignore', invalid='ignore'):
        evi =2.5*(nir_array.astype(float) - red_array.astype(float)) / (nir_array.astype(float) + 6*red_array.astype(float) - 7.5*blue_array.astype(float) + 1)
    evi = np.nan_to_num(evi)
    evi = np.clip(evi, -1, 1)  # Ensure evi values are between -1 and 1

    # Update the metadata for the output evi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': evi.dtype
    })

    # Save evi as a GeoTIFF
    evi_buffer = io.BytesIO()
    with rasterio.open(evi_buffer, 'w', **red_meta) as dst:
        dst.write(evi, 1)

    evi_buffer.seek(0)
    return evi_buffer

@app.route('/calculate_evi', methods=['POST'])
def process_evi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    blue_band_bytes = BytesIO(request.files['blueBand'].read())
    evi_buffer = calculate_evi(red_band_bytes, nir_band_bytes, blue_band_bytes)
    return send_file(evi_buffer, mimetype='image/tiff', download_name='evi.tif')

if __name__ == '__main__':
    app.run(debug=True)