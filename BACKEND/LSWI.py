from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_lswi(swir1_band_bytes, nir_band_bytes):
    # Open the swir1 band image with rasterio to get metadata
    with rasterio.open(swir1_band_bytes) as src:
        swir1_meta = src.meta.copy()

    # Load images
    swir1_image = Image.open(swir1_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    swir1_array = np.array(swir1_image)
    nir_array = np.array(nir_image)

    # Calculate lswi
    with np.errstate(divide='ignore', invalid='ignore'):
        lswi = (nir_array.astype(float) - swir1_array.astype(float)) / (nir_array.astype(float) + swir1_array.astype(float))
    lswi = np.nan_to_num(lswi)
    lswi = np.clip(lswi, -1, 1)  # Ensure lswi values are between -1 and 1

    # Update the metadata for the output lswi GeoTIFF
    swir1_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': lswi.dtype
    })

    # Save lswi as a GeoTIFF
    lswi_buffer = io.BytesIO()
    with rasterio.open(lswi_buffer, 'w', **swir1_meta) as dst:
        dst.write(lswi, 1)

    lswi_buffer.seek(0)
    return lswi_buffer

@app.route('/calculate_lswi', methods=['POST'])
def process_lswi():
    swir1_band_bytes = BytesIO(request.files['swir1Band'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    lswi_buffer = calculate_lswi(swir1_band_bytes, nir_band_bytes)
    return send_file(lswi_buffer, mimetype='image/tiff', download_name='lswi.tif')

if __name__ == '__main__':
    app.run(debug=True)