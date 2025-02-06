from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import re

app = Flask(__name__)

def sanitize_filename(filename):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def get_video_formats(url):
    """Get available formats for the video"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except:
            return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.form.get('url')
        if not url:
            return jsonify({'error': 'Please provide a URL'}), 400

        # Create downloads directory if it doesn't exist
        download_path = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(download_path, exist_ok=True)

        # First, try to get video information
        info = get_video_formats(url)
        if not info:
            return jsonify({'error': 'Could not fetch video information'}), 400

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Try different format combinations
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
            'verbose': True,
            'no_warnings': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': []
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Try to download the video
                info = ydl.extract_info(url, download=True)
                if not info:
                    return jsonify({'error': 'Failed to download video'}), 400

                video_title = info.get('title', 'video')
                video_title = sanitize_filename(video_title)
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully downloaded: {video_title}'
                })

            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                if 'Sign in' in error_msg:
                    return jsonify({'error': 'This video requires authentication. Please try a different video.'}), 403
                elif 'This video is unavailable' in error_msg:
                    return jsonify({'error': 'This video is unavailable. It might be private or deleted.'}), 404
                elif 'Video unavailable' in error_msg:
                    return jsonify({'error': 'Video is unavailable. Please check if the video exists and is public.'}), 404
                else:
                    return jsonify({'error': f'Download failed: {error_msg}'}), 400

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2525, debug=True)
