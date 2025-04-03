// JavaScript to handle tab switching
function switchTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabs.forEach(tab => tab.classList.remove('active'));
    tabButtons.forEach(button => button.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    document.getElementById(`${tabId}-tab`).classList.add('active');
}

// Default to showing the first tab
document.addEventListener('DOMContentLoaded', () => {
    switchTab('video-upload');
});

const overlay = document.getElementById('overlay');

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("uploadForm");
    const statusMessage = document.getElementById("statusMessage");
    const btbUploadBtn = document.getElementById('vu-upload-btn');
    const icon = btbUploadBtn.querySelector('i');
    const audioPlayer = document.getElementById('audioPlayer');
    const audioSource = document.getElementById('audioSource');

    btbUploadBtn.addEventListener('click', function() {
        if (icon.classList.contains('fa-upload')) {
            document.getElementById('videoInput').click();
        }
        if (icon.classList.contains('fa-refresh')) {
            location.reload();
        }
    });

    document.getElementById('videoInput').addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            console.log("File selected:", file.name);
            form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
        }
        if (icon.classList.contains('fa-upload')) {
            icon.classList.replace('fa-upload', 'fa-refresh');
            btbUploadBtn.style.backgroundColor = '#4caf50';
        }
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent default form submission

        overlay.classList.add('active');
        statusMessage.innerText = "Uploading...";

        let formData = new FormData(form);
        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                statusMessage.innerText = "Processing complete!";
                overlay.classList.remove('active');

                // Update audio player with the processed URL
                audioSource.src = result.processed_url;
                audioPlayer.load(); // Reload the audio element
                audioPlayer.style.display = 'block'; // Show the player
                audioPlayer.play().catch(err => {
                    console.log("Auto-play failed:", err);
                    statusMessage.innerText = "Click play to start audio";
                });
            } else {
                statusMessage.innerText = `Error: ${result.error}`;
                overlay.classList.remove('active');
            }
        } catch (error) {
            console.error("Upload error:", error);
            statusMessage.innerText = "Upload failed: " + error.message;
            overlay.classList.remove('active');
        }
    });
});