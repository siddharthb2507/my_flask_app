from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_mndwi(swir2_band_bytes, nir_band_bytes):
    # Open the swir2 band image with rasterio to get metadata
    with rasterio.open(swir2_band_bytes) as src:
        swir2_meta = src.meta.copy()

    # Load images
    swir2_image = Image.open(swir2_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    swir2_array = np.array(swir2_image)
    nir_array = np.array(nir_image)

    # Calculate mndwi
    with np.errstate(divide='ignore', invalid='ignore'):
        mndwi = (swir2_array.astype(float) - nir_array.astype(float)) / (swir2_array.astype(float) + nir_array.astype(float))
    mndwi = np.nan_to_num(mndwi)
    mndwi = np.clip(mndwi, -1, 1)  # Ensure mndwi values are between -1 and 1

    # Update the metadata for the output mndwi GeoTIFF
    swir2_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': mndwi.dtype
    })

    # Save mndwi as a GeoTIFF
    mndwi_buffer = io.BytesIO()
    with rasterio.open(mndwi_buffer, 'w', **swir2_meta) as dst:
        dst.write(mndwi, 1)

    mndwi_buffer.seek(0)
    return mndwi_buffer

@app.route('/calculate_mndwi', methods=['POST'])
def process_mndwi():
    swir2_band_bytes = BytesIO(request.files['swir2Band'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    mndwi_buffer = calculate_mndwi(swir2_band_bytes, nir_band_bytes)
    return send_file(mndwi_buffer, mimetype='image/tiff', download_name='mndwi.tif')

if __name__ == '__main__':
    app.run(debug=True)