import os
import tempfile
import argparse
import datetime
from dotenv import load_dotenv
from pydub import AudioSegment
import openai
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

# Models used
TRANSCRIPTION_MODEL = "whisper-1"
SUMMARY_MODEL = "gpt-4o-mini"

# Default languages (ISO Codes)
DEFAULT_AUDIO_LANGUAGE = "en"      # Original language of the audio
DEFAULT_TRANSCRIPT_LANGUAGE = "en" # Language of the final transcription (Whisper does not translate automatically)
DEFAULT_SUMMARY_LANGUAGE = "en"    # Language of the summary

# Maximum file size for direct processing (in MB)
MAX_SIZE_MB = 25

# List of languages supported by Whisper
SUPPORTED_LANGUAGES = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "hy": "Armenian",
    "az": "Azerbaijani",
    "be": "Belarusian",
    "bs": "Bosnian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "zh": "Chinese",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "gl": "Galician",
    "de": "German",
    "el": "Greek",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "is": "Icelandic",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "kk": "Kazakh",
    "ko": "Korean",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "mk": "Macedonian",
    "ms": "Malay",
    "mr": "Marathi",
    "mi": "Maori",
    "ne": "Nepali",
    "no": "Norwegian",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sr": "Serbian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "es": "Spanish",
    "sw": "Swahili",
    "sv": "Swedish",
    "tl": "Tagalog",
    "ta": "Tamil",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "cy": "Welsh"
}

# Extensions considered as video files
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}

# -------------------------------------------------------
# Argument Parsing and Validation Functions
# -------------------------------------------------------
def parse_arguments():
    """
    Parses command-line arguments.
    Returns an object with the provided parameters.
    """
    parser = argparse.ArgumentParser(
        description="AudioTranscriber: Extracts, transcribes, and summarizes audio from video files.",
        epilog=("Supported languages: " + ", ".join([f"{code} ({name})" for code, name in SUPPORTED_LANGUAGES.items()]))
    )

    parser.add_argument('--input', '-i', required=True, help='Path to the input audio or video file.')
    parser.add_argument('--audio_language', '-al', default=DEFAULT_AUDIO_LANGUAGE, help='Language code of the original audio (default: en).')
    parser.add_argument('--transcript_language', '-tl', default=DEFAULT_TRANSCRIPT_LANGUAGE, help='Language of the final transcription (Whisper does not translate by default).')
    parser.add_argument('--summary_language', '-sl', default=DEFAULT_SUMMARY_LANGUAGE, help='Language for the summary (default: en).')
    parser.add_argument('--output', '-o', help='Path to the output transcription text file.')

    args = parser.parse_args()

    # Validate languages
    for lang_arg in [args.audio_language, args.transcript_language, args.summary_language]:
        if lang_arg not in SUPPORTED_LANGUAGES:
            parser.error(f"Unsupported language: '{lang_arg}'.")

    return args

# -------------------------------------------------------
# Utility Functions
# -------------------------------------------------------
def load_api_key():
    """
    Loads the OpenAI API key from the .env file.
    """
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise EnvironmentError("OpenAI API key not found. Please set 'OPENAI_API_KEY' in the .env file.")

def is_video_file(file_path):
    """
    Returns True if the file is considered a video based on its extension.
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower() in VIDEO_EXTENSIONS

def generate_output_paths(input_file_path, provided_output_path=None):
    """
    Generates default output paths for the transcription and summary files
    if they are not provided.
    """
    if provided_output_path:
        transcription_path = provided_output_path
    else:
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        transcription_path = f"{base_name}_{timestamp}_transcription.txt"

    summary_path = transcription_path.replace("_transcription.txt", "_summary.txt")
    return transcription_path, summary_path

def file_size_in_mb(file_path):
    """
    Returns the file size in MB.
    """
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

# -------------------------------------------------------
# Audio Processing Functions
# -------------------------------------------------------
def extract_audio_from_video(video_file_path, audio_format='mp3'):
    """
    Extracts audio from a video file, returning the path to the temporary audio file.
    """
    print(f"Extracting audio from: {video_file_path}")
    try:
        audio = AudioSegment.from_file(video_file_path)
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}")
        audio.export(temp_audio.name, format=audio_format)
        print(f"Audio extracted to temporary file: {temp_audio.name}")
        return temp_audio.name
    except Exception as e:
        print(f"Failed to extract audio from video: {e}")
        return None

def split_audio(file_path, max_size_mb=MAX_SIZE_MB, safety_margin=5000):
    """
    Splits an audio file into smaller parts, each up to max_size_mb MB.
    Returns a list of paths to the segmented files.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024 - safety_margin

        # Assuming a bitrate for export (128kbps)
        export_bitrate_kbps = 128
        export_bitrate_bps = (export_bitrate_kbps * 1000) / 8

        # Calculate segment duration in ms
        segment_duration_sec = max_size_bytes / export_bitrate_bps
        segment_duration_ms = int(segment_duration_sec * 1000)

        print(f"Splitting audio into segments of approximately {max_size_mb}MB...")
        print(f"Bitrate: {export_bitrate_kbps} kbps, Duration per segment: {segment_duration_sec:.2f} s")

        segments = []
        base_name = os.path.splitext(file_path)[0]
        start_ms = 0

        while start_ms < len(audio):
            end_ms = start_ms + segment_duration_ms
            segment = audio[start_ms:end_ms]

            segment_file_name = f"{base_name}_part{len(segments)+1}.mp3"
            segment.export(segment_file_name, format="mp3", bitrate=f"{export_bitrate_kbps}k")
            segments.append(segment_file_name)

            segment_size = os.path.getsize(segment_file_name)
            print(f"Exported: {segment_file_name} (from {start_ms/1000:.2f}s to {min(end_ms/1000, len(audio)/1000):.2f}s), size: {segment_size} bytes")

            start_ms = end_ms

        return segments
    except Exception as e:
        print(f"Failed to split the audio: {e}")
        return []

# -------------------------------------------------------
# OpenAI API Communication Functions
# -------------------------------------------------------
def transcribe_audio(file_path, audio_language):
    """
    Transcribes the audio using OpenAI's Whisper-1 model.
    """
    try:
        print(f"Sending {file_path} for transcription...")
        with open(file_path, "rb") as audio_file:
            transcription = openai.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL,
                file=audio_file,
                language=audio_language
            )
        print(f"Transcription completed for {file_path}.")
        return transcription.text
    except (AuthenticationError, RateLimitError, APIConnectionError, APIError) as api_err:
        print(f"API error: {api_err}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Unexpected error during transcription: {e}")
    return None

def summarize_transcript(transcript, summary_language):
    """
    Generates a summary of the transcript using a GPT model.
    """
    print("Generating summary...")
    system_prompt = (
        f"You are an assistant that summarizes lectures. Please provide a summary of the main points discussed. "
        f"The summary should be in {summary_language}."
    )
    user_prompt = f"Here is the lecture transcription:\n\n{transcript}\n\nPlease provide a summary of the main points above."

    try:
        response = openai.chat.completions.create(
            model=SUMMARY_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
        print("Summary generated successfully.")
        return summary
    except Exception as e:
        print(f"Failed to generate summary: {e}")
    return None

# -------------------------------------------------------
# Main Function
# -------------------------------------------------------
def main(input_file_path, audio_language, transcript_language, summary_language, output_file_path):
    # Check if the input file exists
    if not os.path.exists(input_file_path):
        print(f"File not found: {input_file_path}")
        return

    # Load API key
    try:
        load_api_key()
    except EnvironmentError as e:
        print(e)
        return

    # Generate output paths
    transcription_path, summary_path = generate_output_paths(input_file_path, output_file_path)

    # If the input is a video, extract the audio first
    if is_video_file(input_file_path):
        audio_file_path = extract_audio_from_video(input_file_path)
        if not audio_file_path:
            print("Audio extraction failed. Exiting.")
            return
    else:
        audio_file_path = input_file_path

    # Check file size
    current_size_mb = file_size_in_mb(audio_file_path)
    max_size_bytes = MAX_SIZE_MB * 1024 * 1024

    # If the file is within the size limit, transcribe directly
    if current_size_mb <= max_size_bytes:
        print("File is within the size limit. Starting transcription...")
        transcription = transcribe_audio(audio_file_path, audio_language=audio_language)
        if transcription:
            # Save transcription
            with open(transcription_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            print(f"Transcription saved to: {transcription_path}")

            # Generate summary
            summary = summarize_transcript(transcription, summary_language=summary_language)
            if summary:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"Summary saved to: {summary_path}")
            else:
                print("Failed to generate summary.")
        else:
            print("Transcription failed.")
    else:
        # File is too large, split into segments
        print(f"The file exceeds {MAX_SIZE_MB} MB (current size: {current_size_mb:.2f} MB). Splitting the audio...")
        segments = split_audio(audio_file_path, max_size_mb=MAX_SIZE_MB)
        all_transcriptions = []

        for segment in segments:
            print(f"\nTranscribing segment: {segment}")
            segment_transcription = transcribe_audio(segment, audio_language=audio_language)
            if segment_transcription:
                all_transcriptions.append(segment_transcription)
                print(f"Transcription completed for segment: {segment}.")
            else:
                print(f"Failed to transcribe segment: {segment}.")

        combined_transcription = "\n".join(all_transcriptions)
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(combined_transcription)
        print(f"Complete transcription saved to: {transcription_path}")

        # Generate summary of the entire text
        summary = summarize_transcript(combined_transcription, summary_language=summary_language)
        if summary:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to: {summary_path}")
        else:
            print("Failed to generate summary.")

    # If the input was a video, remove the temporary audio file
    if is_video_file(input_file_path) and audio_file_path and os.path.exists(audio_file_path):
        try:
            os.remove(audio_file_path)
            print(f"Temporary audio file removed: {audio_file_path}")
        except Exception as e:
            print(f"Failed to remove temporary audio file: {e}")

if __name__ == "__main__":
    args = parse_arguments()
    main(
        input_file_path=args.input,
        audio_language=args.audio_language,
        transcript_language=args.transcript_language,
        summary_language=args.summary_language,
        output_file_path=args.output
    )