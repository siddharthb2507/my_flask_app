from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_recvi(red_band_bytes, nir_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)

    # Calculate recvi
    with np.errstate(divide='ignore', invalid='ignore'):
        recvi = ((nir_array.astype(float) / red_array.astype(float))) - 1
    recvi = np.nan_to_num(recvi)
    recvi = np.clip(recvi, -1, 1)  # Ensure recvi values are between -1 and 1

    # Update the metadata for the output recvi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': recvi.dtype
    })

    # Save recvi as a GeoTIFF
    recvi_buffer = io.BytesIO()
    with rasterio.open(recvi_buffer, 'w', **red_meta) as dst:
        dst.write(recvi, 1)

    recvi_buffer.seek(0)
    return recvi_buffer

@app.route('/calculate_recvi', methods=['POST'])
def process_recvi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    recvi_buffer = calculate_recvi(red_band_bytes, nir_band_bytes)
    return send_file(recvi_buffer, mimetype='image/tiff', download_name='recvi.tif')

if __name__ == '__main__':
    app.run(debug=True)