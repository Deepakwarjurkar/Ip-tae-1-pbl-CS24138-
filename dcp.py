import cv2
import numpy as np


def get_dark_channel(image, window_size=15):
    """
    Calculate the Dark Channel Prior.

    image:
        RGB image with values in the range 0 to 1.
    """

    # Minimum value among R, G and B
    min_channel = np.min(image, axis=2)

    # Local minimum filter
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (window_size, window_size)
    )

    dark_channel = cv2.erode(
        min_channel,
        kernel
    )

    return dark_channel


def estimate_atmospheric_light(image, dark_channel):
    """
    Estimate atmospheric light A.
    """

    height, width = dark_channel.shape

    total_pixels = height * width

    # Top 0.1% brightest pixels in dark channel
    num_pixels = max(
        1,
        int(total_pixels * 0.001)
    )

    dark_flat = dark_channel.reshape(-1)

    # Get indices of brightest dark-channel pixels
    indices = np.argpartition(
        dark_flat,
        -num_pixels
    )[-num_pixels:]

    image_flat = image.reshape(-1, 3)

    candidate_pixels = image_flat[indices]

    # Choose the brightest candidate
    brightness = np.sum(
        candidate_pixels,
        axis=1
    )

    atmospheric_light = candidate_pixels[
        np.argmax(brightness)
    ]

    return atmospheric_light


def estimate_transmission(
    image,
    atmospheric_light,
    omega=0.95,
    window_size=15
):
    """
    Estimate the initial transmission map
    using the Dark Channel Prior.
    """

    # Normalize image by atmospheric light
    normalized_image = image / (
        atmospheric_light + 1e-6
    )

    # Calculate normalized dark channel
    dark_normalized = get_dark_channel(
        normalized_image,
        window_size
    )

    # Initial transmission
    transmission = (
        1.0 -
        omega * dark_normalized
    )

    return transmission


def guided_filter(
    guide,
    filtering_input,
    radius=40,
    eps=0.001
):
    """
    Guided filter used to refine the transmission map.

    guide:
        Grayscale guide image in range 0 to 1.

    filtering_input:
        Initial transmission map.
    """

    kernel_size = (
        2 * radius + 1,
        2 * radius + 1
    )

    mean_guide = cv2.boxFilter(
        guide,
        cv2.CV_64F,
        kernel_size,
        normalize=True
    )

    mean_input = cv2.boxFilter(
        filtering_input,
        cv2.CV_64F,
        kernel_size,
        normalize=True
    )

    mean_guide_squared = cv2.boxFilter(
        guide * guide,
        cv2.CV_64F,
        kernel_size,
        normalize=True
    )

    mean_guide_input = cv2.boxFilter(
        guide * filtering_input,
        cv2.CV_64F,
        kernel_size,
        normalize=True
    )

    # Variance of guide
    variance_guide = (
        mean_guide_squared -
        mean_guide * mean_guide
    )

    # Covariance
    covariance = (
        mean_guide_input -
        mean_guide * mean_input
    )

    # Linear coefficients
    a = covariance / (
        variance_guide + eps
    )

    b = (
        mean_input -
        a * mean_guide
    )

    # Average coefficients
    mean_a = cv2.boxFilter(
        a,
        cv2.CV_64F,
        kernel_size,
        normalize=True
    )

    mean_b = cv2.boxFilter(
        b,
        cv2.CV_64F,
        kernel_size,
        normalize=True
    )

    # Refined transmission
    refined = (
        mean_a * guide +
        mean_b
    )

    return refined


def refine_transmission(
    image,
    transmission
):
    """
    Refine transmission using guided filtering.
    """

    # Convert RGB image to grayscale guide
    guide = cv2.cvtColor(
        image.astype(np.float32),
        cv2.COLOR_RGB2GRAY
    )

    refined = guided_filter(
        guide,
        transmission.astype(np.float64),
        radius=40,
        eps=0.001
    )

    # Keep transmission between 0 and 1
    refined = np.clip(
        refined,
        0,
        1
    )

    return refined.astype(np.float32)


def recover_scene(
    image,
    atmospheric_light,
    transmission,
    t0=0.1
):
    """
    Recover the haze-free scene.
    """

    # Avoid division by very small transmission
    transmission = np.maximum(
        transmission,
        t0
    )

    transmission_3 = transmission[:, :, np.newaxis]

    recovered = (
        (image - atmospheric_light)
        / transmission_3
    ) + atmospheric_light

    # Keep valid image range
    recovered = np.clip(
        recovered,
        0,
        1
    )

    return recovered


def dehaze(image):
    """
    Complete Dark Channel Prior dehazing pipeline.

    Returns:
        dark_channel
        atmospheric_light
        refined_transmission
        dehazed_image
    """

    # --------------------------------
    # STEP 1: Dark Channel
    # --------------------------------

    dark_channel = get_dark_channel(
        image,
        window_size=15
    )

    # --------------------------------
    # STEP 2: Atmospheric Light
    # --------------------------------

    atmospheric_light = (
        estimate_atmospheric_light(
            image,
            dark_channel
        )
    )

    # --------------------------------
    # STEP 3: Initial Transmission
    # --------------------------------

    transmission = estimate_transmission(
        image,
        atmospheric_light,
        omega=0.95,
        window_size=15
    )

    # --------------------------------
    # STEP 4: Transmission Refinement
    # --------------------------------

    refined_transmission = (
        refine_transmission(
            image,
            transmission
        )
    )

    # --------------------------------
    # STEP 5: Scene Recovery
    # --------------------------------

    dehazed = recover_scene(
        image,
        atmospheric_light,
        refined_transmission,
        t0=0.1
    )

    return (
        dark_channel,
        atmospheric_light,
        refined_transmission,
        dehazed
    )