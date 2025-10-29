from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# Load environment variables (set these in Azure App Settings, not in .env)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("IMAGES_CONTAINER", "lanternfly-images")

# Create the BlobServiceClient and container client
bsc = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
cc = bsc.get_container_client(CONTAINER_NAME)

# Make sure the container exists
try:
    cc.create_container()
except Exception:
    pass  # Container likely already exists

# --- Upload API ---
@app.post("/api/v1/upload")
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Upload the file to Azure Blob Storage
    blob_client = cc.get_blob_client(file.filename)
    blob_client.upload_blob(file, overwrite=True)

    # Return the URL to access the image
    blob_url = f"{cc.url}/{file.filename}"
    return jsonify({"ok": True, "url": blob_url})


# --- Gallery API ---
@app.get("/api/v1/gallery")
def gallery():
    blobs = [f"{cc.url}/{b.name}" for b in cc.list_blobs()]
    return jsonify(blobs)


# --- Health check API ---
@app.get("/api/v1/health")
def health():
    return jsonify({"status": "healthy"})


# --- Root Route ---
@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
