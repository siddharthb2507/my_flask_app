from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_hbsi(green_band_bytes, nir_band_bytes, blue_band_bytes, swir2_band_bytes):
    # Open the green band image with rasterio to get metadata
    with rasterio.open(green_band_bytes) as src:
        green_meta = src.meta.copy()

    # Load images
    green_image = Image.open(green_band_bytes)
    nir_image = Image.open(nir_band_bytes)
    blue_image = Image.open(blue_band_bytes)
    swir2_image = Image.open(swir2_band_bytes)

    # Convert images to numpy arrays
    green_array = np.array(green_image)
    nir_array = np.array(nir_image)
    blue_array = np.array(blue_image)
    swir2_array = np.array(swir2_image)

    # 
    swir2 = swir2_array.astype(float)
    green = green_array.astype(float)
    blue = blue_array.astype(float)
    nir = nir_array.astype(float)
    # 

    # Calculate hbsi
    with np.errstate(divide='ignore', invalid='ignore'):
        hbsi = (((swir2-blue)/(swir2+blue))-((nir-green)/(nir+green)))
    hbsi = np.nan_to_num(hbsi)
    hbsi = np.clip(hbsi, -1, 1)  # Ensure hbsi values are between -1 and 1

    # Update the metadata for the output hbsi GeoTIFF
    green_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': hbsi.dtype
    })

    # Save hbsi as a GeoTIFF
    hbsi_buffer = io.BytesIO()
    with rasterio.open(hbsi_buffer, 'w', **green_meta) as dst:
        dst.write(hbsi, 1)

    hbsi_buffer.seek(0)
    return hbsi_buffer

@app.route('/calculate_hbsi', methods=['POST'])
def process_hbsi():
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    blue_band_bytes = BytesIO(request.files['blueBand'].read())
    swir2_band_bytes = BytesIO(request.files['swir2Band'].read())
    hbsi_buffer = calculate_hbsi(green_band_bytes, nir_band_bytes, blue_band_bytes, swir2_band_bytes)
    return send_file(hbsi_buffer, mimetype='image/tiff', download_name='hbsi.tif')

if __name__ == '__main__':
    app.run(debug=True)