async function calculateNDVI() {
    const redFile = document.getElementById("redFile").files[0];
    const nirFile = document.getElementById("nirFile").files[0];
  
    if (!redFile || !nirFile) {
      alert("Please select both red and NIR band files.");
      return;
    }
  
    const formData = new FormData();
    formData.append("red_file", redFile);
    formData.append("nir_file", nirFile);
  
    try {
      const response = await fetch("http://localhost:8000/calculate-ndvi", {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
  
      if (data.message === "NDVI calculation successful!") {
        if (data.ndvi_data) {
          // Download NDVI data if available (optional)
          const blob = new Blob([data.ndvi_data], { type: "application/octet-stream" });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = "ndvi_output.tif";
          link.click();
          window.URL.revokeObjectURL(url);
        } else {
          alert("NDVI calculation successful! No data available for download.");
        }
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error(error);
      alert("An error occurred during NDVI calculation.");
    }
  }
  