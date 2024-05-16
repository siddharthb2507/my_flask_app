from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_vari(red_band_bytes, green_band_bytes, blue_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    green_image = Image.open(green_band_bytes)
    blue_image = Image.open(blue_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    green_array = np.array(green_image)
    blue_array = np.array(blue_image)

    # Calculate vari
    with np.errstate(divide='ignore', invalid='ignore'):
        vari = (green_array.astype(float) - red_array.astype(float)) / (green_array.astype(float) + red_array.astype(float) - blue_array.astype(float))
    vari = np.nan_to_num(vari)
    vari = np.clip(vari, -1, 1)  # Ensure vari values are between -1 and 1

    # Update the metadata for the output vari GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': vari.dtype
    })

    # Save vari as a GeoTIFF
    vari_buffer = io.BytesIO()
    with rasterio.open(vari_buffer, 'w', **red_meta) as dst:
        dst.write(vari, 1)

    vari_buffer.seek(0)
    return vari_buffer

@app.route('/calculate_vari', methods=['POST'])
def process_vari():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    blue_band_bytes = BytesIO(request.files['blueBand'].read())
    vari_buffer = calculate_vari(red_band_bytes, green_band_bytes, blue_band_bytes)
    return send_file(vari_buffer, mimetype='image/tiff', download_name='vari.tif')

if __name__ == '__main__':
    app.run(debug=True)