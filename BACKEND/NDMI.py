from flask import Flask, request, send_file
from PIL import Image
import numpy as np
import io
import rasterio
from rasterio.transform import from_bounds
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def calculate_ndmi(nir_band, swir1_band):
    # Load images
    nir_image = Image.open(nir_band)
    swir1_image = Image.open(swir1_band)

    # Convert images to numpy arrays
    nir_array = np.array(nir_image)
    swir1_array = np.array(swir1_image)

    # Calculate ndmi
    with np.errstate(divide='ignore', invalid='ignore'):
        ndmi = (nir_array.astype(float) - swir1_array.astype(float)) / (nir_array.astype(float) + swir1_array.astype(float))
    ndmi = np.nan_to_num(ndmi)
    ndmi = np.clip(ndmi, -1, 1)  # Ensure ndmi values are between -1 and 1

    # Get metadata from the nir band image
    bounds = nir_image.getbbox()
    transform = from_bounds(*bounds, nir_array.shape[1], nir_array.shape[0])
    ndmi_profile = {
        'driver': 'GTiff',
        'height': nir_array.shape[0],
        'width': nir_array.shape[1],
        'count': 1,
        'dtype': ndmi.dtype,
        'transform': transform,
        'nodata': 0,
        'crs': 'EPSG:32643'  # Set the CRS explicitly to EPSG:32643
    }

    # Save ndmi as a GeoTIFF
    ndmi_buffer = io.BytesIO()
    with rasterio.open(ndmi_buffer, 'w', **ndmi_profile) as dst:
        dst.write(ndmi, 1)

    ndmi_buffer.seek(0)
    return ndmi_buffer

@app.route('/calculate_ndmi', methods=['POST'])
def process_ndmi():
    nir_band = request.files['nirBand']
    swir1_band = request.files['swir1Band']
    ndmi_buffer = calculate_ndmi(nir_band, swir1_band)

    return send_file(ndmi_buffer, mimetype='image/tiff', download_name='ndmi.tif')

if __name__ == '__main__':
    app.run(debug=True)
