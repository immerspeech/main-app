// JavaScript to handle tab switching
function switchTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    const tabButtons = document.querySelectorAll('.tab-btn');

    // Remove active class from all tabs and buttons
    tabs.forEach(tab => tab.classList.remove('active'));
    tabButtons.forEach(button => button.classList.remove('active'));

    // Add active class to the selected tab and button
    document.getElementById(tabId).classList.add('active');
    document.getElementById(`${tabId}-tab`).classList.add('active');
    document.getElementById(`${tabId}-player`).classList.add('active');
}

// Default to showing the first tab
document.addEventListener('DOMContentLoaded', () => {
    switchTab('video-upload');
});

const overlay = document.getElementById('overlay');


document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("uploadForm");
    const textEnglish = document.getElementById("textEnglish");
    const textKorean = document.getElementById("textKorean");
    const audioContainer = document.getElementById("audioContainer");
    const statusMessage = document.getElementById("statusMessage");

    const btbUploadBtn = document.getElementById('vu-upload-btn');
    const icon = btbUploadBtn.querySelector('i');
    btbUploadBtn.addEventListener('click', function() {
        if (icon.classList.contains('fa-upload')) {
            document.getElementById('videoInput').click(); // Trigger the file input
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
        overlay.classList.add('active');
        
        event.preventDefault();

        let formData = new FormData(form);
        statusMessage.innerText = "Uploading...";

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            statusMessage.innerText = "Processing... Waiting for results.";
            
            // Start streaming results
            const eventSource = new EventSource("/results");

            eventSource.onmessage = function (event) {
                const cleanedData = event.data.replace(/^data: /, "").trim();
                const data = JSON.parse(cleanedData);

                if (data.type === "text_en") {
                    textEnglish.innerText = "English: " + data.content;
                } else if (data.type === "text_kr") {
                    textKorean.innerText = "Korean: " + data.content;
                } else if (data.type === "audio") {
                    console.log("ASDDAS")
                    let audioElement = document.createElement("audio");
                    audioElement.controls = true;
                    audioElement.src = data.url;
                    console.log("ASDDAdasdasasdS")
                    
                    audioContainer.appendChild(audioElement);

                    console.log("ASDDASdasdasasdadsadsasd")
                    console.log("Received data:", data);
                    if (data.type === "audio") {
                        console.log("Audio URL:", data.url);
                    }
                    console.log(data.url)
                }
            };

            overlay.classList.remove('active');

            eventSource.onerror = function () {
                statusMessage.innerText = "Processing complete.";
                eventSource.close();
                overlay.classList.remove('active');
            };
        } else {
            statusMessage.innerText = "Error uploading video.";
        }
    });
});