from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_ndti(red_band_bytes, green_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    green_image = Image.open(green_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    green_array = np.array(green_image)

    # Calculate ndti
    with np.errstate(divide='ignore', invalid='ignore'):
        ndti = (red_array.astype(float) - green_array.astype(float)) / (red_array.astype(float) + green_array.astype(float))
    ndti = np.nan_to_num(ndti)
    ndti = np.clip(ndti, -1, 1)  # Ensure ndti values are between -1 and 1

    # Update the metadata for the output ndti GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': ndti.dtype
    })

    # Save ndti as a GeoTIFF
    ndti_buffer = io.BytesIO()
    with rasterio.open(ndti_buffer, 'w', **red_meta) as dst:
        dst.write(ndti, 1)

    ndti_buffer.seek(0)
    return ndti_buffer

@app.route('/calculate_ndti', methods=['POST'])
def process_ndti():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    ndti_buffer = calculate_ndti(red_band_bytes, green_band_bytes)
    return send_file(ndti_buffer, mimetype='image/tiff', download_name='ndti.tif')

if __name__ == '__main__':
    app.run(debug=True)