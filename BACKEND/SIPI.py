from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_sipi(red_band_bytes, nir_band_bytes, blue_band_bytes):
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

    # Calculate sipi
    with np.errstate(divide='ignore', invalid='ignore'):
        sipi = (nir_array.astype(float) - red_array.astype(float)) / (nir_array.astype(float) + red_array.astype(float) - blue_array.astype(float))
    sipi = np.nan_to_num(sipi)
    sipi = np.clip(sipi, -1, 1)  # Ensure sipi values are between -1 and 1

    # Update the metadata for the output sipi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': sipi.dtype
    })

    # Save sipi as a GeoTIFF
    sipi_buffer = io.BytesIO()
    with rasterio.open(sipi_buffer, 'w', **red_meta) as dst:
        dst.write(sipi, 1)

    sipi_buffer.seek(0)
    return sipi_buffer

@app.route('/calculate_sipi', methods=['POST'])
def process_sipi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    blue_band_bytes = BytesIO(request.files['blueBand'].read())
    sipi_buffer = calculate_sipi(red_band_bytes, nir_band_bytes, blue_band_bytes)
    return send_file(sipi_buffer, mimetype='image/tiff', download_name='sipi.tif')

if __name__ == '__main__':
    app.run(debug=True)