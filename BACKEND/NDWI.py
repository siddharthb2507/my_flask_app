from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_ndwi(green_band_bytes, nir_band_bytes):
    # Open the green band image with rasterio to get metadata
    with rasterio.open(green_band_bytes) as src:
        green_meta = src.meta.copy()

    # Load images
    green_image = Image.open(green_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    green_array = np.array(green_image)
    nir_array = np.array(nir_image)

    # Calculate ndwi
    with np.errstate(divide='ignore', invalid='ignore'):
        ndwi = (green_array.astype(float) - nir_array.astype(float)) / (green_array.astype(float) + nir_array.astype(float))
    ndwi = np.nan_to_num(ndwi)
    ndwi = np.clip(ndwi, -1, 1)  # Ensure ndwi values are between -1 and 1

    # Update the metadata for the output ndwi GeoTIFF
    green_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': ndwi.dtype
    })

    # Save ndwi as a GeoTIFF
    ndwi_buffer = io.BytesIO()
    with rasterio.open(ndwi_buffer, 'w', **green_meta) as dst:
        dst.write(ndwi, 1)

    ndwi_buffer.seek(0)
    return ndwi_buffer

@app.route('/calculate_ndwi', methods=['POST'])
def process_ndwi():
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    ndwi_buffer = calculate_ndwi(green_band_bytes, nir_band_bytes)
    return send_file(ndwi_buffer, mimetype='image/tiff', download_name='ndwi.tif')

if __name__ == '__main__':
    app.run(debug=True)