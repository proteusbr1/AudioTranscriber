import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="AudioTranscriber: Extract and transcribe audio from video files.")
    parser.add_argument('--input', '-i', required=True, help='Path to the input audio or video file.')
    parser.add_argument('--language', '-l', default='en', help='Language code for transcription (default: en).')
    return parser.parse_args()

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import necessary exceptions from OpenAI
from openai import (
    APIError,
    OpenAIError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
)


def extract_audio(video_file_path, audio_format='mp3'):
    """
    Extracts audio from a video file and saves it as an audio file.

    :param video_file_path: Path to the video file.
    :param audio_format: Desired audio format (default: 'mp3').
    :return: Path to the extracted audio file.
    """
    try:
        print(f"Extracting audio from video file: {video_file_path}")
        # Load the video file
        audio = AudioSegment.from_file(video_file_path)

        # Create a temporary file to save the extracted audio
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}")
        audio.export(temp_audio_file.name, format=audio_format)
        print(f"Audio extracted and saved to temporary file: {temp_audio_file.name}")
        return temp_audio_file.name
    except Exception as e:
        print(f"Failed to extract audio from video file: {e}")
        return None


def split_audio(file_path, max_size_mb=25, safety_margin=5000):
    """
    Splits an audio file into smaller segments that are below the specified maximum size.

    :param file_path: Path to the original audio file.
    :param max_size_mb: Maximum size of each segment in megabytes.
    :param safety_margin: Number of bytes to subtract as safety margin.
    :return: List of paths to the split audio files.
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_file(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024 - safety_margin

        # Set the bitrate for exporting in bytes per second
        export_bitrate_kbps = 128  # kbps
        export_bitrate_bps = (export_bitrate_kbps * 1000) / 8  # Convert to bytes per second

        # Calculate the duration for each segment in milliseconds
        segment_duration_sec = max_size_bytes / export_bitrate_bps
        segment_duration_ms = segment_duration_sec * 1000

        print(f"Export bitrate: {export_bitrate_kbps} kbps")
        print(f"Estimated duration per segment: {segment_duration_sec:.2f} seconds")

        segments = []
        # Split the audio into segments
        for start_ms in range(0, len(audio), int(segment_duration_ms)):
            end_ms = start_ms + int(segment_duration_ms)
            segment = audio[start_ms:end_ms]
            segment_file = f"{os.path.splitext(file_path)[0]}_part{len(segments)+1}.mp3"
            segment.export(segment_file, format="mp3", bitrate=f"{export_bitrate_kbps}k")
            segments.append(segment_file)
            actual_file_size = os.path.getsize(segment_file)
            print(f"Exported: {segment_file} ({start_ms/1000:.2f} - {min(end_ms/1000, len(audio)/1000):.2f} seconds), size: {actual_file_size} bytes")
        return segments
    except Exception as e:
        print(f"Failed to split audio file: {e}")
        return []


def transcribe_audio(file_path, language=None, response_format="json"):
    """
    Transcribes an audio file using the OpenAI Whisper API.

    :param file_path: Path to the audio file.
    :param language: (Optional) Language code of the audio (e.g., "en" for English).
    :param response_format: Response format ("json", "text", "verbose_json", etc.).
    :return: Transcription text or None in case of error.
    """
    try:
        with open(file_path, "rb") as audio_file:
            print(f"Sending {file_path} to OpenAI Whisper API for transcription...")
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format=response_format
            )
            print(f"Transcription successful for file: {file_path}")
            return transcription.text
    except AuthenticationError as e:
        print("Authentication error with OpenAI API:", e)
    except RateLimitError as e:
        print("Rate limit exceeded. Please try again later:", e)
    except APIConnectionError as e:
        print("Connection issue with OpenAI API:", e)
    except APIError as e:
        print("General API error from OpenAI:", e)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
    return None


def main(input_file_path, language="en"):
    """
    Main function to extract audio from video (if necessary), split it if too large, and transcribe.

    :param input_file_path: Path to the original audio or video file.
    :param language: Language code of the audio (default: "en" for English).
    """
    # Check if the file exists
    if not os.path.exists(input_file_path):
        print(f"File not found: {input_file_path}")
        return

    # Determine if the input file is a video based on its extension
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
    file_ext = os.path.splitext(input_file_path)[1].lower()

    audio_file_path = input_file_path  # Default to input file

    # If the file is a video, extract the audio
    if file_ext in video_extensions:
        audio_file_path = extract_audio(input_file_path, audio_format='mp3')
        if not audio_file_path:
            print("Audio extraction failed. Cannot proceed with transcription.")
            return

    try:
        # Check the file size
        file_size = os.path.getsize(audio_file_path)
        max_size_mb = 25
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size <= max_size_bytes:
            print("The file is within the size limit. Proceeding with transcription.")
            transcription = transcribe_audio(audio_file_path, language=language)
            if transcription:
                print("\n--- Audio Transcription ---")
                print(transcription)
            else:
                print("Failed to transcribe the audio.")
        else:
            print(f"The file exceeds the {max_size_mb} MB limit (current size: {file_size / (1024 * 1024):.2f} MB).")
            print("Splitting the file into smaller parts...")

            # Split the audio into smaller parts
            segments = split_audio(audio_file_path, max_size_mb=max_size_mb)
            all_transcriptions = []

            # Transcribe each segment
            for segment in segments:
                print(f"\nTranscribing: {segment}")
                transcription = transcribe_audio(segment, language=language)
                if transcription:
                    all_transcriptions.append(transcription)
                    print(f"Transcription of {segment} completed.")
                else:
                    print(f"Failed to transcribe {segment}.")

            # Combine all transcriptions
            combined_transcription = "\n".join(all_transcriptions)
            print("\n--- Complete Audio Transcription ---")
            print(combined_transcription)
    finally:
        # Clean up temporary audio file if it was extracted from a video
        if file_ext in video_extensions and audio_file_path and os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                print(f"Temporary audio file deleted: {audio_file_path}")
            except Exception as e:
                print(f"Failed to delete temporary audio file: {e}")


if __name__ == "__main__":
    args = parse_arguments()
    main(args.input, language=args.language)