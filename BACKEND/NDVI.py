from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_ndvi(red_band_bytes, nir_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)

    # Calculate ndvi
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir_array.astype(float) - red_array.astype(float)) / (nir_array.astype(float) + red_array.astype(float))
    ndvi = np.nan_to_num(ndvi)
    ndvi = np.clip(ndvi, -1, 1)  # Ensure ndvi values are between -1 and 1

    # Update the metadata for the output NDVI GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': ndvi.dtype
    })

    # Save ndvi as a GeoTIFF
    ndvi_buffer = io.BytesIO()
    with rasterio.open(ndvi_buffer, 'w', **red_meta) as dst:
        dst.write(ndvi, 1)

    ndvi_buffer.seek(0)
    return ndvi_buffer

@app.route('/calculate_ndvi', methods=['POST'])
def process_ndvi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    ndvi_buffer = calculate_ndvi(red_band_bytes, nir_band_bytes)
    return send_file(ndvi_buffer, mimetype='image/tiff', download_name='ndvi.tif')

if __name__ == '__main__':
    app.run(debug=True)