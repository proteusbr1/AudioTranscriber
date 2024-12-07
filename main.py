import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
import argparse
import datetime
import openai
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError

# -------------------- Configuration --------------------
# Adjust these variables as needed:
TRANSCRIPTION_MODEL = "whisper-1"      # Whisper model for transcription
SUMMARY_MODEL = "gpt-3.5-turbo"        # GPT model for summarization
DEFAULT_AUDIO_LANGUAGE = "en"          # Language of the original audio
DEFAULT_TRANSCRIPT_LANGUAGE = "en"     # Transcription language (Whisper transcription does not translate automatically)
DEFAULT_SUMMARY_LANGUAGE = "en"        # Summary language
MAX_SIZE_MB = 25
# -------------------------------------------------------


# -------------------- Supported Languages by Whisper --------------------
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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="AudioTranscriber: Extract and transcribe audio from video files.",
        epilog="Supported languages: " + ", ".join([f"{code} ({name})" for code, name in SUPPORTED_LANGUAGES.items()])
    )
    parser.add_argument('--input', '-i', required=True, help='Path to the input audio or video file.')
    parser.add_argument('--audio_language', '-al', default=DEFAULT_AUDIO_LANGUAGE, help='Language code of the original audio (default: en).')
    parser.add_argument('--transcript_language', '-tl', default=DEFAULT_TRANSCRIPT_LANGUAGE, help='Language of the final transcription. (Note: Whisper transcriptions do not translate by default.)')
    parser.add_argument('--summary_language', '-sl', default=DEFAULT_SUMMARY_LANGUAGE, help='Language for the summary (default: en).')
    parser.add_argument('--output', '-o', help='Path to the output transcription text file.')
    args = parser.parse_args()

    if args.audio_language not in SUPPORTED_LANGUAGES:
        parser.error(f"Unsupported audio language code: '{args.audio_language}'.")

    if args.transcript_language not in SUPPORTED_LANGUAGES:
        parser.error(f"Unsupported transcription language code: '{args.transcript_language}'.")

    if args.summary_language not in SUPPORTED_LANGUAGES:
        parser.error(f"Unsupported summary language code: '{args.summary_language}'.")

    return args

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def extract_audio(video_file_path, audio_format='mp3'):
    """
    Extract audio from a video file.
    """
    try:
        print(f"Extracting audio from video file: {video_file_path}")
        audio = AudioSegment.from_file(video_file_path)
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}")
        audio.export(temp_audio_file.name, format=audio_format)
        print(f"Audio extracted to temporary file: {temp_audio_file.name}")
        return temp_audio_file.name
    except Exception as e:
        print(f"Failed to extract audio: {e}")
        return None


def split_audio(file_path, max_size_mb=25, safety_margin=5000):
    """
    Split an audio file into smaller parts, each up to max_size_mb megabytes.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024 - safety_margin

        # Assuming 128kbps bitrate for export
        export_bitrate_kbps = 128
        export_bitrate_bps = (export_bitrate_kbps * 1000) / 8

        segment_duration_sec = max_size_bytes / export_bitrate_bps
        segment_duration_ms = segment_duration_sec * 1000

        print(f"Bitrate: {export_bitrate_kbps} kbps")
        print(f"Estimated duration per segment: {segment_duration_sec:.2f} sec")

        segments = []
        for start_ms in range(0, len(audio), int(segment_duration_ms)):
            end_ms = start_ms + int(segment_duration_ms)
            segment = audio[start_ms:end_ms]
            segment_file = f"{os.path.splitext(file_path)[0]}_part{len(segments)+1}.mp3"
            segment.export(segment_file, format="mp3", bitrate=f"{export_bitrate_kbps}k")
            segments.append(segment_file)
            actual_file_size = os.path.getsize(segment_file)
            print(f"Exported: {segment_file} ({start_ms/1000:.2f} - {min(end_ms/1000, len(audio)/1000):.2f} s), size: {actual_file_size} bytes")
        return segments
    except Exception as e:
        print(f"Failed to split the audio: {e}")
        return []


def transcribe_audio(file_path, audio_language=None):
    try:
        with open(file_path, "rb") as audio_file:
            print(f"Sending {file_path} for transcription...")
            transcription = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=audio_language
            )
            print(f"Transcription completed for {file_path}.")
            return transcription.text
    except AuthenticationError as e:
        print("Authentication error:", e)
    except RateLimitError as e:
        print("Rate limit exceeded:", e)
    except APIConnectionError as e:
        print("Connection issue with the API:", e)
    except APIError as e:
        print("API error:", e)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Unexpected error during transcription: {e}")
    return None


def summarize_transcription(transcript, summary_language=DEFAULT_SUMMARY_LANGUAGE):
    """
    Summarize the transcribed text using a GPT model.
    """
    try:
        print("Generating summary...")
        system_prompt = f"You are an assistant that summarizes lectures. Please provide a summary of the main points discussed. The summary should be in {summary_language}."
        user_prompt = f"Here is the lecture transcription:\n\n{transcript}\n\nPlease provide a summary of the main points above."

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


def main(input_file_path, audio_language=DEFAULT_AUDIO_LANGUAGE, transcript_language=DEFAULT_TRANSCRIPT_LANGUAGE, summary_language=DEFAULT_SUMMARY_LANGUAGE, output_file_path=None):
    """
    Main function: extract audio from video (if needed), transcribe, and summarize.
    """
    if not os.path.exists(input_file_path):
        print(f"File not found: {input_file_path}")
        return

    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
    file_ext = os.path.splitext(input_file_path)[1].lower()

    audio_file_path = input_file_path

    # If input is a video, extract its audio
    if file_ext in video_extensions:
        audio_file_path = extract_audio(input_file_path, audio_format='mp3')
        if not audio_file_path:
            print("Audio extraction failed. Exiting.")
            return

    # Check file size
    file_size = os.path.getsize(audio_file_path)
    max_size_bytes = MAX_SIZE_MB * 1024 * 1024

    # Default output paths
    if not output_file_path:
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_file_path = f"{base_name}_{timestamp}_transcription.txt"
    summary_output_file = output_file_path.replace("_transcription.txt", "_summary.txt")

    # If the file is within the size limit
    if file_size <= max_size_bytes:
        print("File size is within limit. Starting transcription...")
        transcription = transcribe_audio(audio_file_path, audio_language=audio_language)
        if transcription:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            print(f"Transcription saved to: {output_file_path}")

            # Generate summary
            summary = summarize_transcription(transcription, summary_language=summary_language)
            if summary:
                with open(summary_output_file, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"Summary saved to: {summary_output_file}")
            else:
                print("Failed to generate summary.")
        else:
            print("Transcription failed.")
    else:
        # If file is too large, split into segments
        print(f"The file exceeds {MAX_SIZE_MB} MB (current size: {file_size / (1024 * 1024):.2f} MB). Splitting the audio...")
        segments = split_audio(audio_file_path, max_size_mb=MAX_SIZE_MB)
        all_transcriptions = []

        for segment in segments:
            print(f"\nTranscribing segment: {segment}")
            segment_transcription = transcribe_audio(segment, audio_language=audio_language)
            if segment_transcription:
                all_transcriptions.append(segment_transcription)
                print(f"Segment transcription completed: {segment}.")
            else:
                print(f"Failed to transcribe segment: {segment}.")

        combined_transcription = "\n".join(all_transcriptions)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(combined_transcription)
        print(f"Complete transcription saved to: {output_file_path}")

        # Generate summary of the entire text
        summary = summarize_transcription(combined_transcription, summary_language=summary_language)
        if summary:
            with open(summary_output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to: {summary_output_file}")
        else:
            print("Failed to generate summary.")

    # Clean up temporary audio file if one was extracted
    if file_ext in video_extensions and audio_file_path and os.path.exists(audio_file_path):
        try:
            os.remove(audio_file_path)
            print(f"Temporary audio file removed: {audio_file_path}")
        except Exception as e:
            print(f"Failed to remove temporary audio file: {e}")


if __name__ == "__main__":
    args = parse_arguments()
    main(
        args.input,
        audio_language=args.audio_language,
        transcript_language=args.transcript_language,
        summary_language=args.summary_language,
        output_file_path=args.output
    )