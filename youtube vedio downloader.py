from pytubefix import YouTube
from pytubefix.exceptions import VideoUnavailable
import os
import subprocess

def download_video(url, destination_folder):
    """
    Downloads a YouTube video, falling back to merging separate
    video and audio streams if no progressive stream is available.
    """
    try:
        if not os.path.isdir(destination_folder):
            print(f"📁 Folder doesn't exist. Creating: {destination_folder}")
            os.makedirs(destination_folder, exist_ok=True)

        print("🔍 Fetching video info...")
        yt = YouTube(url)

        print(f"\nTitle: {yt.title}")
        print(f"Length: {yt.length // 60} min {yt.length % 60} sec")
        print(f"Views: {yt.views:,}")

        # Try progressive stream first (video+audio combined, usually 360p/720p)
        stream = yt.streams.get_highest_resolution()

        if stream:
            print(f"\n⬇️ Downloading in {stream.resolution} (progressive)...")
            stream.download(output_path=destination_folder)
            print(f"\n✅ Download complete! Saved to: {destination_folder}")
            return

        # Fall back to adaptive streams (separate video and audio, higher quality)
        print("\nℹ️ No progressive stream found. Trying adaptive video+audio...")

        video_stream = yt.streams.filter(adaptive=True, file_extension="mp4", only_video=True).order_by("resolution").desc().first()
        audio_stream = yt.streams.filter(adaptive=True, only_audio=True).order_by("abr").desc().first()

        if not video_stream or not audio_stream:
            print("❌ No downloadable stream found for this video.")
            return

        print(f"⬇️ Downloading video ({video_stream.resolution})...")
        video_path = video_stream.download(output_path=destination_folder, filename="temp_video.mp4")

        print(f"⬇️ Downloading audio...")
        audio_path = audio_stream.download(output_path=destination_folder, filename="temp_audio.mp4")

        # Merge video and audio using ffmpeg
        safe_title = "".join(c for c in yt.title if c.isalnum() or c in " _-").strip()
        output_path = os.path.join(destination_folder, f"{safe_title}.mp4")

        print("🔧 Merging video and audio with ffmpeg...")
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c", "copy", output_path],
            capture_output=True, text=True
        )

        # Clean up temp files
        os.remove(video_path)
        os.remove(audio_path)

        if result.returncode != 0:
            print("❌ ffmpeg merge failed. Is ffmpeg installed and on your PATH?")
            print(result.stderr[-500:])  # show last part of the error
            return

        print(f"\n✅ Download complete! Saved to: {output_path}")

    except VideoUnavailable:
        print("❌ This video is unavailable (may be private, deleted, or region-locked).")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

def main():
    print("=" * 45)
    print("       YOUTUBE VIDEO DOWNLOADER")
    print("=" * 45)

    url = input("Enter the YouTube video URL: ").strip()
    destination = input("Enter destination folder path: ").strip()

    if not url:
        print("❌ URL cannot be empty.")
        return

    download_video(url, destination)

if __name__ == "__main__":
    main()