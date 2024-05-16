from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_ndsi(swir1_band_bytes, nir_band_bytes):
    # Open the swir1 band image with rasterio to get metadata
    with rasterio.open(swir1_band_bytes) as src:
        swir1_meta = src.meta.copy()

    # Load images
    swir1_image = Image.open(swir1_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    swir1_array = np.array(swir1_image)
    nir_array = np.array(nir_image)

    # Calculate ndsi
    with np.errstate(divide='ignore', invalid='ignore'):
        ndsi = (swir1_array.astype(float) - nir_array.astype(float)) / (swir1_array.astype(float) + nir_array.astype(float))
    ndsi = np.nan_to_num(ndsi)
    ndsi = np.clip(ndsi, -1, 1)  # Ensure ndsi values are between -1 and 1

    # Update the metadata for the output ndsi GeoTIFF
    swir1_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': ndsi.dtype
    })

    # Save ndsi as a GeoTIFF
    ndsi_buffer = io.BytesIO()
    with rasterio.open(ndsi_buffer, 'w', **swir1_meta) as dst:
        dst.write(ndsi, 1)

    ndsi_buffer.seek(0)
    return ndsi_buffer

@app.route('/calculate_ndsi', methods=['POST'])
def process_ndsi():
    swir1_band_bytes = BytesIO(request.files['swir1Band'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    ndsi_buffer = calculate_ndsi(swir1_band_bytes, nir_band_bytes)
    return send_file(ndsi_buffer, mimetype='image/tiff', download_name='ndsi.tif')

if __name__ == '__main__':
    app.run(debug=True)