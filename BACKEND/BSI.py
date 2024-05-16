from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_bsi(red_band_bytes, nir_band_bytes, blue_band_bytes, swir2_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)
    blue_image = Image.open(blue_band_bytes)
    swir2_image = Image.open(swir2_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)
    blue_array = np.array(blue_image)
    swir2_array = np.array(swir2_image)

    # Calculate bsi
    with np.errstate(divide='ignore', invalid='ignore'):
        bsi = ((swir2_array.astype(float)+red_array.astype(float))-(nir_array.astype(float)+blue_array.astype(float)))/((swir2_array.astype(float)+red_array.astype(float))+(nir_array.astype(float)+blue_array.astype(float)))
    bsi = np.nan_to_num(bsi)
    bsi = np.clip(bsi, -1, 1)  # Ensure bsi values are between -1 and 1

    # Update the metadata for the output bsi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': bsi.dtype
    })

    # Save bsi as a GeoTIFF
    bsi_buffer = io.BytesIO()
    with rasterio.open(bsi_buffer, 'w', **red_meta) as dst:
        dst.write(bsi, 1)

    bsi_buffer.seek(0)
    return bsi_buffer

@app.route('/calculate_bsi', methods=['POST'])
def process_bsi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    blue_band_bytes = BytesIO(request.files['blueBand'].read())
    swir2_band_bytes = BytesIO(request.files['swir2Band'].read())
    bsi_buffer = calculate_bsi(red_band_bytes, nir_band_bytes, blue_band_bytes, swir2_band_bytes)
    return send_file(bsi_buffer, mimetype='image/tiff', download_name='bsi.tif')

if __name__ == '__main__':
    app.run(debug=True)