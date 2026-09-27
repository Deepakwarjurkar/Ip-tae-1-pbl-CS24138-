from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import time

from dcp import dehaze


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULT_FOLDER"] = RESULT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


def calculate_contrast(image):
    """
    Calculate image contrast using the standard deviation
    of grayscale intensity.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return float(np.std(gray))


def calculate_entropy(image):
    """
    Calculate grayscale image entropy.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    histogram = cv2.calcHist(
        [gray],
        [0],
        None,
        [256],
        [0, 256]
    ).flatten()

    probabilities = histogram / np.sum(histogram)

    probabilities = probabilities[
        probabilities > 0
    ]

    entropy = -np.sum(
        probabilities * np.log2(probabilities)
    )

    return float(entropy)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    if "image" not in request.files:
        return render_template(
            "index.html",
            error="Please select an image."
        )

    file = request.files["image"]

    if file.filename == "":
        return render_template(
            "index.html",
            error="Please select an image."
        )

    # Secure the uploaded filename
    filename = secure_filename(file.filename)

    if not filename:
        return render_template(
            "index.html",
            error="Invalid filename."
        )

    upload_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(upload_path)

    # Read image
    image = cv2.imread(upload_path)

    if image is None:
        return render_template(
            "index.html",
            error="The selected image could not be read."
        )

    # Convert BGR -> RGB
    image_rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image_float = (
        image_rgb.astype(np.float32) / 255.0
    )

    # --------------------------------
    # ORIGINAL IMAGE METRICS
    # --------------------------------

    contrast_before = calculate_contrast(
        image_rgb
    )

    entropy_before = calculate_entropy(
        image_rgb
    )

    # --------------------------------
    # RUN DCP
    # --------------------------------

    start_time = time.perf_counter()

    (
        dark_channel,
        atmospheric_light,
        transmission,
        dehazed
    ) = dehaze(image_float)

    processing_time = (
        time.perf_counter() - start_time
    )

    # --------------------------------
    # SAVE DARK CHANNEL
    # --------------------------------

    dark_filename = "dark_" + filename

    dark_path = os.path.join(
        RESULT_FOLDER,
        dark_filename
    )

    dark_uint8 = (
        np.clip(dark_channel, 0, 1) * 255
    ).astype(np.uint8)

    cv2.imwrite(
        dark_path,
        dark_uint8
    )

    # --------------------------------
    # SAVE TRANSMISSION MAP
    # --------------------------------

    transmission_filename = (
        "transmission_" + filename
    )

    transmission_path = os.path.join(
        RESULT_FOLDER,
        transmission_filename
    )

    transmission_uint8 = (
        np.clip(transmission, 0, 1) * 255
    ).astype(np.uint8)

    cv2.imwrite(
        transmission_path,
        transmission_uint8
    )

    # --------------------------------
    # SAVE DEHAZED IMAGE
    # --------------------------------

    dehazed_filename = (
        "dehazed_" + filename
    )

    dehazed_path = os.path.join(
        RESULT_FOLDER,
        dehazed_filename
    )

    dehazed_uint8 = (
        np.clip(dehazed, 0, 1) * 255
    ).astype(np.uint8)

    dehazed_bgr = cv2.cvtColor(
        dehazed_uint8,
        cv2.COLOR_RGB2BGR
    )

    cv2.imwrite(
        dehazed_path,
        dehazed_bgr
    )

    # --------------------------------
    # DEHAZED IMAGE METRICS
    # --------------------------------

    contrast_after = calculate_contrast(
        dehazed_uint8
    )

    entropy_after = calculate_entropy(
        dehazed_uint8
    )

    # --------------------------------
    # RETURN WEBSITE RESULTS
    # --------------------------------

    return render_template(
        "index.html",

        original_image="/uploads/" + filename,

        dark_channel="/results/" + dark_filename,

        transmission="/results/" +
        transmission_filename,

        dehazed_image="/results/" +
        dehazed_filename,

        atmospheric_light=np.round(
            atmospheric_light,
            3
        ).tolist(),

        contrast_before=round(
            contrast_before,
            2
        ),

        contrast_after=round(
            contrast_after,
            2
        ),

        entropy_before=round(
            entropy_before,
            2
        ),

        entropy_after=round(
            entropy_after,
            2
        ),

        processing_time=round(
            processing_time,
            2
        )
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


@app.route("/results/<filename>")
def result_file(filename):

    return send_from_directory(
        app.config["RESULT_FOLDER"],
        filename
    )


@app.route("/download/<filename>")
def download_file(filename):

    return send_from_directory(
        app.config["RESULT_FOLDER"],
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)