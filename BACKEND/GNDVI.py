from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_gndvi(green_band_bytes, nir_band_bytes):
    # Open the green band image with rasterio to get metadata
    with rasterio.open(green_band_bytes) as src:
        green_meta = src.meta.copy()

    # Load images
    green_image = Image.open(green_band_bytes)
    nir_image = Image.open(nir_band_bytes)

    # Convert images to numpy arrays
    green_array = np.array(green_image)
    nir_array = np.array(nir_image)

    # Calculate gndvi
    with np.errstate(divide='ignore', invalid='ignore'):
        gndvi = (nir_array.astype(float) - green_array.astype(float)) / (nir_array.astype(float) + green_array.astype(float))
    gndvi = np.nan_to_num(gndvi)
    gndvi = np.clip(gndvi, -1, 1)  # Ensure gndvi values are between -1 and 1

    # Update the metadata for the output gndvi GeoTIFF
    green_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': gndvi.dtype
    })

    # Save gndvi as a GeoTIFF
    gndvi_buffer = io.BytesIO()
    with rasterio.open(gndvi_buffer, 'w', **green_meta) as dst:
        dst.write(gndvi, 1)

    gndvi_buffer.seek(0)
    return gndvi_buffer

@app.route('/calculate_gndvi', methods=['POST'])
def process_gndvi():
    green_band_bytes = BytesIO(request.files['greenBand'].read())
    nir_band_bytes = BytesIO(request.files['nirBand'].read())
    gndvi_buffer = calculate_gndvi(green_band_bytes, nir_band_bytes)
    return send_file(gndvi_buffer, mimetype='image/tiff', download_name='gndvi.tif')

if __name__ == '__main__':
    app.run(debug=True)