const serverUrl = "http://127.0.0.1:2000";

function loadGallery() {
    fetch(`${serverUrl}/gallery`)
        .then(response => response.json())
        .then(images => {
            const gallery = document.getElementById("gallery");
            gallery.innerHTML = "";
            images.forEach(src => {
                const img = document.createElement("img");
                img.src = `${serverUrl}${src}`;
                img.alt = "Image";
                gallery.appendChild(img);
            });
        })
        .catch(error => console.error("Error loading gallery:", error));
}

document.addEventListener("DOMContentLoaded", () => {
    const uploadInput = document.getElementById("uploadInput");

    if (uploadInput) {
        uploadInput.addEventListener("change", () => {
            if (uploadInput.files.length > 0) {
                const file = uploadInput.files[0];
                const formData = new FormData();
                formData.append("file", file);

                fetch(`${serverUrl}/upload`, {
                    method: "POST",
                    body: formData,
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.url) {
                            loadGallery();
                        } else {
                            alert("Ошибка: " + (data.error || "Неизвестная ошибка"));
                        }
                    })
                    .catch(error => console.error("Error uploading image:", error));
            }
        });

        loadGallery();
    }
});