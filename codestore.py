from flask import Flask, render_template, request, jsonify, send_file
from pytube import YouTube
from googleapiclient.discovery import build

import traceback
import json
from functools import lru_cache
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Đọc API key từ tệp cấu hình
with open('config.json') as f:
    config = json.load(f)
    api_key = config['api_key']

# Tạo một service object để gửi các yêu cầu đến YouTube Data API
youtube = build('youtube', 'v3', developerKey=api_key)

# Hàm

# rút gọn url và chỉ lấy phần cần thiết
def extract_video_url(video_url):
    # Parse URL
    parsed_url = urlparse(video_url)
    # Extract query parameters
    query_params = parse_qs(parsed_url.query)
    # Lấy giá trị của tham số 'v' nếu có
    video_id = query_params.get('v', [''])[0]
    if video_id:
        # Rebuild URL chỉ từ phần protocol đến phần ID
        extracted_url = f"{parsed_url.scheme}://{parsed_url.netloc}/watch?v={video_id}"
        return extracted_url
    else:
        return None

# lấy phần id trong url
def get_video_id(video_url):
    extracted_url = extract_video_url(video_url)
    if extracted_url:
        # Parse lại URL chỉ từ phần protocol đến phần ID
        parsed_url = urlparse(extracted_url)
        # Trích xuất video ID từ query parameters
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v', [''])[0]
        return video_id
    else:
        return None

def get_video_info_from_youtube(video_id):
    # Thứ tự ưu tiên của chất lượng thumbnail
    thumbnail_quality_order = ['standard', 'high', 'medium', 'default']
    
    # Thử lấy URL của thumbnail với các chất lượng thumbnail lớn nhất trước
    for quality in thumbnail_quality_order:
        # Gửi yêu cầu để lấy thông tin về video chỉ với trường 'snippet' và 'id'
        request = youtube.videos().list(
            part='snippet',
            id=video_id,
            maxResults=1,
            # Yêu cầu chỉ trả về URL của thumbnail với chất lượng
            fields='items/snippet/thumbnails/' + quality + '/url'
        )
        response = request.execute()
        
        # Nếu có thumbnail với chất lượng quality được trả về
        if 'items' in response:
            # Lấy URL của thumbnail
            thumbnail_url = response['items'][0]['snippet']['thumbnails'].get(quality, {}).get('url')
            if thumbnail_url:
                break
    else:
        thumbnail_url = None

    # Gửi yêu cầu để lấy thông tin về video với trường 'snippet' và 'id'
    request = youtube.videos().list(
        part='snippet',
        id=video_id
    )
    # Thực hiện yêu cầu
    response = request.execute()
    
    if 'items' in response:
        # Lấy thông tin về video
        video_info = response['items'][0]
        # Lấy tiêu đề của video
        title = video_info['snippet']['title']
        return jsonify({'title': title, 'thumbnailUrl': thumbnail_url})
    else:
        return {'error': 'Video not found'}

@lru_cache(maxsize=128)
def get_video_resolution(video_url):
    yt = YouTube(video_url)
    stream = yt.streams.get_highest_resolution()
    resolution = stream.resolution
    return str(resolution)  # Convert resolution to string before returning

@lru_cache(maxsize=128)
def get_video_size(video_url):
    yt = YouTube(video_url)
    stream = yt.streams.get_highest_resolution()
    video_size = stream.filesize
    # Chuyển đổi kích thước từ byte sang megabyte và làm tròn đến 2 chữ số thập phân
    video_size_mb = round(video_size / (1024 * 1024), 2)
    return f"{video_size_mb} MB"

# ---- Thực thi code và render HTML ----

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/download', methods=['POST'])
def download_post():
    data = request.json
    video_url = data['videoUrl']
    video_id = get_video_id(video_url)
    video_info = get_video_info_from_youtube(video_id)

    return video_info

@app.route('/download/video-res-size', methods=['GET'])
def download_get_res_size():
    try:
        video_url = request.args.get('url')
        video_resolution = get_video_resolution(video_url)
        video_size = get_video_size(video_url)
        return jsonify({'resolution': video_resolution, 'Size': video_size})
    except Exception as e:
        traceback.print_exc()  
        return jsonify({'error': 'Failed to get video resolution'}), 500

@app.route('/download', methods=['GET'])
def download_get():
    try:
        video_url_1 = request.args.get('url')
        video_url_2 = extract_video_url(video_url_1)
        yt = YouTube(video_url_2)
        stream = yt.streams.get_highest_resolution()
        download_path = 'downloads/'
        stream.download(download_path)
        return jsonify({'message': 'Video downloaded successfully'})
    except Exception as e:
        traceback.print_exc()  
        return jsonify({'error': 'Failed to download video'}), 500
if __name__ == '__main__':
    app.run(debug=True)