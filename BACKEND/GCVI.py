from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_gci(green_band_bytes, nir_band_bytes):
    # Open the green band image with rasterio to get metadata
    with rasterio.open(green_band_bytes) as src:
        green_meta = src.meta.copy()

    # Load images
    green_image = Image.open(green_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    green_array = np.array(green_image)
    nir_array = np.array(nir_image)

    # Calculate gci
    with np.errstate(divide='ignore', invalid='ignore'):
        gci = ((nir_array.astype(float) / green_array.astype(float))) - 1
    gci = np.nan_to_num(gci)
    gci = np.clip(gci, -1, 1)  # Ensure gci values are between -1 and 1

    # Update the metadata for the output gci GeoTIFF
    green_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': gci.dtype
    })

    # Save gci as a GeoTIFF
    gci_buffer = io.BytesIO()
    with rasterio.open(gci_buffer, 'w', **green_meta) as dst:
        dst.write(gci, 1)

    gci_buffer.seek(0)
    return gci_buffer

@app.route('/calculate_gci', methods=['POST'])
def process_gci():
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    gci_buffer = calculate_gci(green_band_bytes, nir_band_bytes)
    return send_file(gci_buffer, mimetype='image/tiff', download_name='gci.tif')

if __name__ == '__main__':
    app.run(debug=True)