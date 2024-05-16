from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_dbsi(red_band_bytes, nir_band_bytes, green_band_bytes, swir2_band_bytes):
    # Open the red band image with rasterio to get metadata
    with rasterio.open(red_band_bytes) as src:
        red_meta = src.meta.copy()

    # Load images
    red_image = Image.open(red_band_bytes)
    nir_image = Image.open(nir_band_bytes)
    green_image = Image.open(green_band_bytes)
    swir2_image = Image.open(swir2_band_bytes)

    # Convert images to numpy arrays
    red_array = np.array(red_image)
    nir_array = np.array(nir_image)
    green_array = np.array(green_image)
    swir2_array = np.array(swir2_image)

    # 
    swir2 = swir2_array.astype(float)
    red = red_array.astype(float)
    green = green_array.astype(float)
    nir = nir_array.astype(float)
    # 

    # Calculate dbsi
    with np.errstate(divide='ignore', invalid='ignore'):
        dbsi = (((swir2-green)/(swir2+green))-((nir-red)/(nir+red)))
    dbsi = np.nan_to_num(dbsi)
    dbsi = np.clip(dbsi, -1, 1)  # Ensure dbsi values are between -1 and 1

    # Update the metadata for the output dbsi GeoTIFF
    red_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': dbsi.dtype
    })

    # Save dbsi as a GeoTIFF
    dbsi_buffer = io.BytesIO()
    with rasterio.open(dbsi_buffer, 'w', **red_meta) as dst:
        dst.write(dbsi, 1)

    dbsi_buffer.seek(0)
    return dbsi_buffer

@app.route('/calculate_dbsi', methods=['POST'])
def process_dbsi():
    red_band_bytes = BytesIO(request.files['redBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    swir2_band_bytes = BytesIO(request.files['swir2Band'].read())
    dbsi_buffer = calculate_dbsi(red_band_bytes, nir_band_bytes, green_band_bytes, swir2_band_bytes)
    return send_file(dbsi_buffer, mimetype='image/tiff', download_name='dbsi.tif')

if __name__ == '__main__':
    app.run(debug=True)