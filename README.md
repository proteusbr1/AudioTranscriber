# AudioTranscriber

**AudioTranscriber** is a Python-based tool designed to automate the process of converting audio from video files into text. It efficiently extracts audio from various video formats, splits large audio files into manageable segments, and leverages OpenAI's Whisper API to transcribe the audio. This tool is ideal for content creators, researchers, and developers seeking an automated and reliable transcription solution.

## 🛠️ Features

- **Audio Extraction**: Extracts audio from video formats such as MP4, MOV, AVI, MKV, FLV, and WMV.
- **Audio Splitting**: Automatically splits very large audio files into smaller parts to comply with size limitations.
- **Transcription**: Utilizes OpenAI's Whisper API for efficient and accurate audio transcription.
- **Summarization**: Creates a summary of the transcribed content using a configurable GPT model.
- **Error Handling**: Handles authentication, rate limits, connection issues, and other types of failures.
- **Environment Configuration**: Easy setup using an `.env` file to securely manage the API key.

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/proteusbr1/AudioTranscriber
cd AudioTranscriber
```

### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Ensure you have [pip](https://pip.pypa.io/en/stable/) installed. Then run:

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory of the project and add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note**: Replace `your_openai_api_key_here` with your actual OpenAI API key. You can obtain an API key from the [OpenAI Platform](https://platform.openai.com/account/api-keys).

## ⚙️ Usage

### Basic Usage

Run the main script `main.py` by providing the path to an audio or video file:

```bash
python main.py --input path/to/audio_or_video.mp4
```

By default, the audio language and the transcription/summarization languages will be English (`en`). You can specify the audio language, transcription language, and summary language using the options below:

- `--audio_language` or `-al`: Defines the original language of the audio. (Default: `en`)
- `--transcript_language` or `-tl`: Defines the language for the final transcription. (Note: Whisper does not automatically translate)
- `--summary_language` or `-sl`: Defines the language for the summary. (Default: `en`)

Example:

```bash
python main.py --input path/to/video.mp4 --output path/to/output_transcription.txt --audio_language en --transcript_language en --summary_language pt
```

In this example, the audio will be transcribed in English, and a summary will subsequently be generated in Portuguese.

### Help

To see all available options:

```bash
python main.py -h
```

## 🤝 Contributing

Contributions are welcome! To enhance the project, follow these steps:

1. **Fork the Repository**

2. **Create a New Branch**

    ```bash
    git checkout -b feature/YourFeature
    ```

3. **Commit Your Changes**

    ```bash
    git commit -m "Add Your Feature"
    ```

4. **Push to the Branch**

    ```bash
    git push origin feature/YourFeature
    ```

5. **Open a Pull Request**

Provide a clear description of your changes and the reasons behind them.

## 📜 License

This project is licensed under the [MIT License](LICENSE).

## 📚 Acknowledgements

- [OpenAI](https://www.openai.com/) for the Whisper API.
- [Pydub](https://github.com/jiaaro/pydub) for audio manipulation.
- [dotenv](https://github.com/theskumar/python-dotenv) for environment variable management.