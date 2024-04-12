document.getElementById('searchForm').addEventListener('submit', function(event) {
    event.preventDefault();
    var videoUrl = document.getElementById('videoUrl').value;
    fetch('/download/video-res-size?url=' + encodeURIComponent(videoUrl))
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch video resolution');
        }
        return response.json();
    })
    .then(data => {
        var videoResolution = data.resolution;
        var videoSize = data.Size
        fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'videoUrl': videoUrl })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch video info');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('videoTitle').innerText = data.title;
            document.getElementById('thumbnail').src = data.thumbnailUrl;
            document.getElementById('videoSize').innerText = videoSize; // Gán kích thước video vào phần tử HTML
            document.getElementById('videoResolution').innerText = videoResolution; // Hiển thị độ phân giải video
            document.getElementById('result').style.display = 'block';

            document.getElementById('downloadButton').addEventListener('click', function() {
                fetch('/download?url=' + encodeURIComponent(videoUrl))
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to fetch');
                    }
                    return response.json();
                })
                .then(data => {
                    alert(data.message);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
