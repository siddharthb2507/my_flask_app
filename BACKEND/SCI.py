from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

def calculate_ndvi(swir1_band_bytes, swir2_band_bytes):
    # Open the swir1 band image with rasterio to get metadata
    with rasterio.open(swir1_band_bytes) as src:
        swir1_meta = src.meta.copy()

    # Load images
    swir1_image = Image.open(swir1_band_bytes)
    swir2_image = Image.open(swir2_band_bytes)

    # Convert images to numpy arrays
    swir1_array = np.array(swir1_image)
    swir2_array = np.array(swir2_image)

    # Calculate sci
    with np.errstate(divide='ignore', invalid='ignore'):
        sci = (swir1_array.astype(float) - swir2_array.astype(float)) / (swir1_array.astype(float) + swir2_array.astype(float))
    sci = np.nan_to_num(sci)
    sci = np.clip(sci, -1, 1)  # Ensure sci values are between -1 and 1

    # Update the metadata for the output NDVI GeoTIFF
    swir1_meta.update({
        'driver': 'GTiff',
        'count': 1,
        'dtype': sci.dtype
    })

    # Save sci as a GeoTIFF
    ndvi_buffer = io.BytesIO()
    with rasterio.open(ndvi_buffer, 'w', **swir1_meta) as dst:
        dst.write(sci, 1)

    ndvi_buffer.seek(0)
    return ndvi_buffer

@app.route('/calculate_ndvi', methods=['POST'])
def process_ndvi():
    swir1_band_bytes = BytesIO(request.files['swir1Band'].read())
    swir2_band_bytes = BytesIO(request.files['swir2Band'].read())
    ndvi_buffer = calculate_ndvi(swir1_band_bytes, swir2_band_bytes)
    return send_file(ndvi_buffer, mimetype='image/tiff', download_name='sci.tif')

if __name__ == '__main__':
    app.run(debug=True)