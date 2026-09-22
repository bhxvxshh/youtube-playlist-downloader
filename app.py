#!/usr/bin/env python3
"""
YouTube Downloader - Web UI
A small local web frontend around yt-dlp so downloads can be started
from the browser instead of the command line.

Run with: python app.py
Then open http://127.0.0.1:5000
"""

import re
import sys
import uuid
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / 'downloads'
COOKIES_PATH = BASE_DIR / 'cookies.txt'
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

QUALITY_FORMATS = {
    'best': 'bestvideo*+bestaudio/best',
    '2160': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
    '1440': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
    '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
    '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
    'audio': 'bestaudio/best',
}

# In-memory job store: {job_id: {...}}
JOBS = {}
JOBS_LOCK = threading.Lock()

PROGRESS_RE = re.compile(
    r'\[download\]\s+(?P<percent>[\d.]+)% of\s+(?P<size>[\d.]+\w+)'
    r'(?:\s+at\s+(?P<speed>[\d.]+\w+/s|Unknown))?'
    r'(?:\s+ETA\s+(?P<eta>\S+))?'
)
DEST_RE = re.compile(r'\[download\] Destination:\s+(?P<path>.+)')
MERGE_RE = re.compile(r'\[Merger\] Merging formats into "(?P<path>.+)"')
ALREADY_RE = re.compile(r'\[download\] (?P<path>.+) has already been downloaded')


def build_command(url, quality):
    fmt = QUALITY_FORMATS.get(quality, QUALITY_FORMATS['best'])
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--newline',
        '--no-mtime',
        '--continue',
        '--retries', '50',
        '--fragment-retries', '50',
        '--retry-sleep', '5',
        '--js-runtimes', 'node',
        '--remote-components', 'ejs:github',
        '--extractor-args', 'youtube:player_client=mweb',
    ]

    if COOKIES_PATH.exists():
        cmd += ['--cookies', str(COOKIES_PATH)]

    if quality == 'audio':
        cmd += ['-f', fmt, '-x', '--audio-format', 'mp3']
    else:
        cmd += ['-f', fmt, '--merge-output-format', 'mkv']

    cmd += ['-o', str(DOWNLOAD_DIR / '%(title)s [%(id)s].%(ext)s'), url]
    return cmd


def run_job(job_id, url, quality):
    job = JOBS[job_id]
    cmd = build_command(url, quality)
    job['status'] = 'downloading'

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace', bufsize=1,
        )
        job['pid'] = proc.pid

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            m = PROGRESS_RE.search(line)
            if m:
                job['percent'] = float(m.group('percent'))
                job['size'] = m.group('size')
                job['speed'] = m.group('speed') or job.get('speed')
                job['eta'] = m.group('eta') or job.get('eta')
                continue

            m = DEST_RE.search(line)
            if m:
                job['filename'] = Path(m.group('path')).name
                continue

            m = MERGE_RE.search(line) or ALREADY_RE.search(line)
            if m:
                job['filename'] = Path(m.group('path')).name
                continue

            if line.startswith('ERROR'):
                job['last_error'] = line

        proc.wait()

        if proc.returncode == 0:
            job['status'] = 'done'
            job['percent'] = 100
        else:
            job['status'] = 'error'
            job['error'] = job.get('last_error', f'yt-dlp exited with code {proc.returncode}')

    except Exception as exc:  # noqa: BLE001
        job['status'] = 'error'
        job['error'] = str(exc)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json(force=True) or {}
    url = (data.get('url') or '').strip()
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({'error': 'URL is required'}), 400
    if 'youtube.com' not in url and 'youtu.be' not in url:
        return jsonify({'error': 'Only YouTube URLs are supported'}), 400

    job_id = uuid.uuid4().hex[:8]
    with JOBS_LOCK:
        JOBS[job_id] = {
            'id': job_id,
            'url': url,
            'quality': quality,
            'status': 'queued',
            'percent': 0,
            'size': None,
            'speed': None,
            'eta': None,
            'filename': None,
            'error': None,
        }

    thread = threading.Thread(target=run_job, args=(job_id, url, quality), daemon=True)
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/api/jobs')
def api_jobs():
    with JOBS_LOCK:
        # Newest first
        jobs = sorted(JOBS.values(), key=lambda j: j['id'], reverse=True)
        return jsonify(jobs)


@app.route('/api/cookies-status')
def api_cookies_status():
    return jsonify({'present': COOKIES_PATH.exists()})


if __name__ == '__main__':
    print('YouTube Downloader running at http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
