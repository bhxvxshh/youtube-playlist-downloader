#!/usr/bin/env python3
"""
YouTube Playlist Downloader - Professional Edition
Downloads entire YouTube playlists in highest quality with size estimation.

Author: bhxvxshh
License: MIT
Repository: https://github.com/bhxvxshh/youtube-playlist-downloader
"""

import yt_dlp
import os
import sys
import argparse
from pathlib import Path


def format_size(bytes_size):
    """Convert bytes to human readable format."""
    if not bytes_size or bytes_size == 0:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"


def format_duration(seconds):
    """Convert seconds to human readable duration."""
    if not seconds:
        return "Unknown"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def get_cookies_path():
    """Get the default cookies.txt path in the script directory."""
    return Path(__file__).parent / 'cookies.txt'


def get_playlist_info(playlist_url, browser=None, cookies_file=None, use_android=False):
    """
    Extract playlist information without downloading.
    
    Args:
        playlist_url: YouTube playlist URL
        browser: Browser name for cookie extraction ('chrome', 'firefox', 'edge')
        cookies_file: Path to cookies.txt file
        use_android: Use Android client to bypass age restrictions
    
    Returns:
        dict: Playlist information including entries
    """
    ydl_opts = {
        'format': 'bestvideo*+bestaudio/best',
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'ignoreerrors': True,
        'verbose': False,
    }
    
    if use_android:
        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['android']}}
        print("📱 Using Android client to bypass age restrictions...\n")
    
    if cookies_file and Path(cookies_file).exists():
        ydl_opts['cookiefile'] = str(cookies_file)
        print(f"🍪 Using cookies from file: {cookies_file}\n")
    elif browser:
        ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
        print(f"🍪 Using cookies from {browser.capitalize()} browser...\n")
    
    print("🔍 Analyzing playlist... Please wait.\n")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        
    return info


def calculate_total_size(info):
    """
    Calculate estimated total download size.
    
    Args:
        info: Playlist information dict from yt-dlp
    
    Returns:
        dict: Size statistics including total_size, total_duration, valid_videos, etc.
    """
    total_size = 0
    total_duration = 0
    valid_videos = 0
    skipped_videos = 0
    video_details = []
    
    entries = info.get('entries', [])
    
    for i, entry in enumerate(entries, 1):
        if entry is None:
            skipped_videos += 1
            continue
            
        formats = entry.get('formats', [])
        
        # Get best video format
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('vcodec') is not None]
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('acodec') is not None]
        
        video_size = 0
        audio_size = 0
        resolution = "Unknown"
        
        if video_formats:
            best_video = max(video_formats, key=lambda f: (f.get('height', 0) or 0, f.get('filesize_approx', 0) or 0))
            video_size = best_video.get('filesize_approx', 0) or best_video.get('filesize', 0) or 0
            resolution = f"{best_video.get('height', '?')}p"
            
        if audio_formats:
            best_audio = max(audio_formats, key=lambda f: f.get('filesize_approx', 0) or f.get('filesize', 0) or 0)
            audio_size = best_audio.get('filesize_approx', 0) or best_audio.get('filesize', 0) or 0
        
        entry_size = video_size + audio_size
        duration = entry.get('duration', 0) or 0
        
        total_size += entry_size
        total_duration += duration
        valid_videos += 1
        
        video_details.append({
            'index': i,
            'title': entry.get('title', 'Unknown')[:50],
            'duration': duration,
            'size': entry_size,
            'resolution': resolution
        })
    
    return {
        'total_size': total_size,
        'total_duration': total_duration,
        'valid_videos': valid_videos,
        'skipped_videos': skipped_videos,
        'video_details': video_details
    }


def display_playlist_summary(info, size_info, show_videos=True):
    """Display playlist summary before download."""
    print("=" * 70)
    print("📋 PLAYLIST SUMMARY")
    print("=" * 70)
    print(f"📁 Playlist: {info.get('title', 'Unknown')}")
    print(f"👤 Channel: {info.get('uploader', 'Unknown')}")
    print(f"🎬 Total Videos: {size_info['valid_videos']}")
    if size_info['skipped_videos'] > 0:
        print(f"⚠️  Skipped (Private/Deleted): {size_info['skipped_videos']}")
    print(f"⏱️  Total Duration: {format_duration(size_info['total_duration'])}")
    print(f"💾 Estimated Size: {format_size(size_info['total_size'])}")
    print("=" * 70)
    
    # Show video list (limit to first 20 if too many)
    if show_videos and size_info['video_details']:
        print("\n📝 VIDEO LIST:")
        print("-" * 70)
        videos_to_show = size_info['video_details'][:20]
        for video in videos_to_show:
            title = video['title'][:40].ljust(40)
            duration = format_duration(video['duration']).ljust(10)
            size = format_size(video['size']).ljust(12)
            res = video['resolution']
            print(f"  {video['index']:3}. {title} | {duration} | {size} | {res}")
        
        if len(size_info['video_details']) > 20:
            print(f"  ... and {len(size_info['video_details']) - 20} more videos")
        print("-" * 70)


def progress_hook(d):
    """Display download progress."""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        filename = os.path.basename(d.get('filename', 'Unknown'))[:40]
        print(f"\r⬇️  {filename}... {percent} at {speed} ETA: {eta}    ", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\r✅ Downloaded: {os.path.basename(d.get('filename', 'Unknown'))[:50]}")


def download_playlist(playlist_url, output_dir=None, browser=None, cookies_file=None, use_android=False):
    """
    Download the entire playlist in highest quality.
    
    Args:
        playlist_url: YouTube playlist URL
        output_dir: Output directory (default: current directory)
        browser: Browser name for cookie extraction
        cookies_file: Path to cookies.txt file
        use_android: Use Android client to bypass age restrictions
    """
    if output_dir is None:
        output_dir = os.getcwd()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        # Best quality format
        'format': 'bestvideo*+bestaudio/best',
        
        # Merge into mp4
        'merge_output_format': 'mp4',
        
        # Output template
        'outtmpl': str(output_dir / '%(playlist_title)s' / '%(playlist_index)s - %(title)s.%(ext)s'),
        
        # Download entire playlist
        'noplaylist': False,
        
        # Multi-connection download for speed
        'concurrent_fragment_downloads': 5,
        
        # Continue interrupted downloads
        'continuedl': True,
        
        # Skip errors (private/deleted videos)
        'ignoreerrors': True,
        
        # Add metadata
        'addmetadata': True,
        
        # Embed thumbnail
        'writethumbnail': False,
        
        # Progress hook
        'progress_hooks': [progress_hook],
        
        # Don't re-download existing files
        'download_archive': str(output_dir / 'downloaded_videos.txt'),
        
        # Postprocessors
        'postprocessors': [{
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        }],
    }
    
    # Use Android client to bypass age restriction
    if use_android:
        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['android']}}
    
    if cookies_file and Path(cookies_file).exists():
        ydl_opts['cookiefile'] = str(cookies_file)
    elif browser:
        ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
    
    print("\n🚀 Starting download...\n")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])
    
    print("\n" + "=" * 70)
    print("✅ DOWNLOAD COMPLETE!")
    print("=" * 70)


def interactive_mode():
    """Run the downloader in interactive mode."""
    print("\n" + "=" * 70)
    print("🎬 YOUTUBE PLAYLIST DOWNLOADER - PROFESSIONAL EDITION")
    print("    Downloads in Highest Quality (4K/8K if available)")
    print("=" * 70)
    
    # Get playlist URL
    playlist_url = input("\n📎 Enter YouTube Playlist URL: ").strip()
    
    if not playlist_url:
        print("❌ No URL provided. Exiting.")
        return
    
    # Validate URL
    if 'youtube.com' not in playlist_url and 'youtu.be' not in playlist_url:
        print("⚠️  Warning: URL doesn't appear to be from YouTube.")
    
    # Select authentication method
    print("\n🔐 Select authentication method (for age-restricted content):")
    print("   1. No login - Android client bypass (RECOMMENDED)")
    print("   2. Use cookies.txt file")
    print("   3. Use Chrome cookies (close Chrome first)")
    print("   4. Use Firefox cookies (close Firefox first)")
    print("   5. Use Edge cookies (close Edge first)")
    print("   6. Skip age-restricted videos")
    
    auth_choice = input("\nEnter choice (1-6): ").strip()
    
    cookies_file = None
    browser = None
    use_android = False
    
    if auth_choice == '1':
        use_android = True
        print("\n📱 Android client bypass enabled - no login needed!")
        
    elif auth_choice == '2':
        cookies_path = get_cookies_path()
        print("\n" + "=" * 60)
        print("📋 HOW TO EXPORT COOKIES:")
        print("=" * 60)
        print("1. Install browser extension 'Get cookies.txt LOCALLY'")
        print("   Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        print("   Firefox: https://addons.mozilla.org/addon/cookies-txt/")
        print("2. Go to YouTube.com and make sure you're signed in")
        print("3. Click the extension icon → 'Export' or 'Current Site'")
        print(f"4. Save as 'cookies.txt' in: {cookies_path.parent}")
        print("=" * 60)
        
        if cookies_path.exists():
            print(f"\n✅ Found cookies.txt at: {cookies_path}")
            cookies_file = cookies_path
        else:
            custom_path = input(f"\n📂 Enter cookies.txt path (or press Enter to cancel): ").strip()
            if custom_path and Path(custom_path).exists():
                cookies_file = Path(custom_path)
            else:
                print("\n❌ Cookies file not found. Continuing without authentication.")
            
    elif auth_choice == '3':
        browser = 'chrome'
        print("\n⚠️  Make sure Chrome is COMPLETELY CLOSED!")
        input("Press Enter when ready...")
    elif auth_choice == '4':
        browser = 'firefox'
        print("\n⚠️  Make sure Firefox is COMPLETELY CLOSED!")
        input("Press Enter when ready...")
    elif auth_choice == '5':
        browser = 'edge'
        print("\n⚠️  Make sure Edge is COMPLETELY CLOSED!")
        input("Press Enter when ready...")
    else:
        print("\n⚠️  No authentication - age-restricted videos will be skipped")
    
    try:
        # Get playlist info
        info = get_playlist_info(playlist_url, browser, cookies_file, use_android)
        
        if not info:
            print("❌ Could not retrieve playlist information.")
            return
        
        # Calculate sizes
        size_info = calculate_total_size(info)
        
        if size_info['valid_videos'] == 0:
            print("❌ No downloadable videos found in this playlist.")
            return
        
        # Display summary
        display_playlist_summary(info, size_info)
        
        # Ask for confirmation
        print(f"\n💾 This will download approximately {format_size(size_info['total_size'])}")
        
        confirm = input("\n🤔 Do you want to proceed with download? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'yeah', 'yep']:
            # Ask for output directory
            output_dir = input("\n📂 Enter output directory (press Enter for current directory): ").strip()
            if not output_dir:
                output_dir = os.getcwd()
            
            # Start download
            download_playlist(playlist_url, output_dir, browser, cookies_file, use_android)
            
            print(f"\n📂 Files saved to: {Path(output_dir) / info.get('title', 'Playlist')}")
        else:
            print("\n❌ Download cancelled.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Tips:")
        print("   - Make sure yt-dlp is installed: pip install -U yt-dlp")
        print("   - Make sure ffmpeg is installed and in PATH")
        print("   - Check if the playlist URL is correct and accessible")


def main():
    """Main entry point with CLI argument support."""
    parser = argparse.ArgumentParser(
        description='Download YouTube playlists in highest quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s URL                                # Download with Android bypass
  %(prog)s URL -o ./downloads                 # Specify output directory
  %(prog)s URL --cookies cookies.txt          # Use cookies file
  %(prog)s URL --browser chrome               # Use Chrome cookies
  %(prog)s URL --info-only                    # Show info without downloading
        '''
    )
    
    parser.add_argument('url', nargs='?', help='YouTube playlist URL')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('--cookies', help='Path to cookies.txt file', default=None)
    parser.add_argument('--browser', choices=['chrome', 'firefox', 'edge', 'brave', 'opera'],
                        help='Browser to extract cookies from')
    parser.add_argument('--android', action='store_true', default=True,
                        help='Use Android client to bypass age restrictions (default)')
    parser.add_argument('--no-android', action='store_true',
                        help='Disable Android client bypass')
    parser.add_argument('--info-only', action='store_true',
                        help='Only show playlist info, don\'t download')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # If no URL provided, run interactive mode
    if not args.url:
        interactive_mode()
        return
    
    # CLI mode
    use_android = args.android and not args.no_android
    cookies_file = args.cookies
    browser = args.browser
    
    try:
        print("\n🔍 Analyzing playlist...")
        info = get_playlist_info(args.url, browser, cookies_file, use_android)
        
        if not info:
            print("❌ Could not retrieve playlist information.")
            sys.exit(1)
        
        size_info = calculate_total_size(info)
        
        if size_info['valid_videos'] == 0:
            print("❌ No downloadable videos found.")
            sys.exit(1)
        
        display_playlist_summary(info, size_info)
        
        if args.info_only:
            return
        
        print(f"\n💾 Estimated download size: {format_size(size_info['total_size'])}")
        
        if not args.yes:
            confirm = input("\n🤔 Proceed with download? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("❌ Download cancelled.")
                return
        
        download_playlist(args.url, args.output, browser, cookies_file, use_android)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
