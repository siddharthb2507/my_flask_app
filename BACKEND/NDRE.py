from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_ndre(rededge_band_bytes, nir_band_bytes):
    # Open the rededge band image with rasterio to get metadata
    with rasterio.open(rededge_band_bytes) as src:
        rededge_meta = src.meta.copy()

    # Load images
    rededge_image = Image.open(rededge_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    rededge_array = np.array(rededge_image)
    nir_array = np.array(nir_image)

    # Calculate ndre
    with np.errstate(divide='ignore', invalid='ignore'):
        ndre = (nir_array.astype(float) - rededge_array.astype(float)) / (nir_array.astype(float) + rededge_array.astype(float))
    ndre = np.nan_to_num(ndre)
    ndre = np.clip(ndre, -1, 1)  # Ensure ndre values are between -1 and 1

    # Update the metadata for the output ndre GeoTIFF
    rededge_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': ndre.dtype
    })

    # Save ndre as a GeoTIFF
    ndre_buffer = io.BytesIO()
    with rasterio.open(ndre_buffer, 'w', **rededge_meta) as dst:
        dst.write(ndre, 1)

    ndre_buffer.seek(0)
    return ndre_buffer

@app.route('/calculate_ndre', methods=['POST'])
def process_ndre():
    rededge_band_bytes = BytesIO(request.files['rededgeBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    ndre_buffer = calculate_ndre(rededge_band_bytes, nir_band_bytes)
    return send_file(ndre_buffer, mimetype='image/tiff', download_name='ndre.tif')

if __name__ == '__main__':
    app.run(debug=True)