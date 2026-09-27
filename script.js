/* ==========================================
   IMAGE UPLOAD & PREVIEW
========================================== */

const imageInput =
    document.getElementById("imageInput");

const dropZone =
    document.getElementById("dropZone");

const previewContainer =
    document.getElementById("previewContainer");

const previewImage =
    document.getElementById("previewImage");

const fileName =
    document.getElementById("fileName");

const removeImage =
    document.getElementById("removeImage");

const uploadForm =
    document.getElementById("uploadForm");

const dehazeButton =
    document.getElementById("dehazeButton");


/* ==========================================
   SHOW SELECTED IMAGE
========================================== */

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            if (this.files.length > 0) {

                showPreview(this.files[0]);

            }

        }
    );

}


function showPreview(file) {

    if (!previewContainer) {
        return;
    }

    fileName.textContent =
        file.name;

    const reader =
        new FileReader();

    reader.onload =
        function (event) {

            previewImage.src =
                event.target.result;

            previewContainer.classList.add(
                "visible"
            );

        };

    reader.readAsDataURL(file);

}


/* ==========================================
   REMOVE SELECTED IMAGE
========================================== */

if (removeImage) {

    removeImage.addEventListener(
        "click",
        function (event) {

            event.preventDefault();

            imageInput.value = "";

            previewImage.src = "";

            fileName.textContent = "";

            previewContainer.classList.remove(
                "visible"
            );

        }
    );

}


/* ==========================================
   DRAG AND DROP
========================================== */

if (dropZone) {

    [
        "dragenter",
        "dragover"
    ].forEach(
        function (eventName) {

            dropZone.addEventListener(
                eventName,
                function (event) {

                    event.preventDefault();

                    dropZone.classList.add(
                        "dragging"
                    );

                }
            );

        }
    );


    [
        "dragleave",
        "drop"
    ].forEach(
        function (eventName) {

            dropZone.addEventListener(
                eventName,
                function (event) {

                    event.preventDefault();

                    dropZone.classList.remove(
                        "dragging"
                    );

                }
            );

        }
    );


    dropZone.addEventListener(
        "drop",
        function (event) {

            const files =
                event.dataTransfer.files;

            if (files.length > 0) {

                /*
                    Assign the dropped file
                    to the file input.
                */

                imageInput.files =
                    files;

                showPreview(files[0]);

            }

        }
    );

}


/* ==========================================
   PROCESSING BUTTON
========================================== */

if (uploadForm) {

    uploadForm.addEventListener(
        "submit",
        function () {

            if (dehazeButton) {

                dehazeButton.disabled =
                    true;

                dehazeButton.innerHTML = `
                    <span>
                        Processing image...
                    </span>

                    <span>
                        ◌
                    </span>
                `;

            }

        }
    );

}


/* ==========================================
   BEFORE / AFTER SLIDER
========================================== */

const comparisonSlider =
    document.getElementById(
        "comparisonSlider"
    );

const beforeImageContainer =
    document.getElementById(
        "beforeImageContainer"
    );

const sliderLine =
    document.getElementById(
        "sliderLine"
    );

const sliderHandle =
    document.getElementById(
        "sliderHandle"
    );


if (comparisonSlider) {

    let isDragging = false;


    /* --------------------------------------
       MOVE SLIDER
    -------------------------------------- */

    function moveSlider(clientX) {

        const rect =
            comparisonSlider.getBoundingClientRect();


        let position =
            (
                (clientX - rect.left)
                /
                rect.width
            ) * 100;


        /*
            Keep the slider between
            0% and 100%.
        */

        position =
            Math.max(
                0,
                Math.min(
                    100,
                    position
                )
            );


        /*
            Change the clipping width
            of the original image.
        */

        if (beforeImageContainer) {

            beforeImageContainer.style.width =
                position + "%";

        }


        /*
            Move the vertical line.
        */

        if (sliderLine) {

            sliderLine.style.left =
                position + "%";

        }


        /*
            Move the circular handle.
        */

        if (sliderHandle) {

            sliderHandle.style.left =
                position + "%";

        }

    }


    /* --------------------------------------
       MOUSE
    -------------------------------------- */

    comparisonSlider.addEventListener(
        "mousedown",
        function (event) {

            isDragging = true;

            moveSlider(event.clientX);

        }
    );


    document.addEventListener(
        "mousemove",
        function (event) {

            if (isDragging) {

                moveSlider(event.clientX);

            }

        }
    );


    document.addEventListener(
        "mouseup",
        function () {

            isDragging = false;

        }
    );


    /* --------------------------------------
       TOUCH
    -------------------------------------- */

    comparisonSlider.addEventListener(
        "touchstart",
        function (event) {

            isDragging = true;

            if (event.touches.length > 0) {

                moveSlider(
                    event.touches[0].clientX
                );

            }

        },
        { passive: true }
    );


    comparisonSlider.addEventListener(
        "touchmove",
        function (event) {

            if (isDragging &&
                event.touches.length > 0) {

                moveSlider(
                    event.touches[0].clientX
                );

            }

        },
        { passive: true }
    );


    comparisonSlider.addEventListener(
        "touchend",
        function () {

            isDragging = false;

        }
    );


    /* --------------------------------------
       INITIAL POSITION
    -------------------------------------- */

    moveSlider(
        comparisonSlider.getBoundingClientRect()
            .left +
        comparisonSlider.getBoundingClientRect()
            .width * 0.5
    );

}