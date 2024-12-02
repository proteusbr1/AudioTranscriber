# AudioTranscriber

**AudioTranscriber** is a Python-based tool designed to streamline the process of converting audio from video files into text. It efficiently extracts audio from various video formats, splits large audio files into manageable segments, and leverages OpenAI's Whisper API to transcribe the audio into text. This tool is ideal for content creators, researchers, and developers seeking an automated and reliable transcription solution.

## 🛠️ Features

- **Audio Extraction**: Extracts audio from multiple video formats such as MP4, MOV, AVI, MKV, FLV, and WMV.
- **Audio Splitting**: Automatically splits large audio files into smaller segments to comply with size limitations.
- **Transcription**: Utilizes OpenAI's Whisper API for accurate and efficient audio transcription.
- **Error Handling**: Comprehensive error handling for API authentication, rate limits, connection issues, and more.
- **Environment Configuration**: Easy setup using environment variables for secure API key management.

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AudioTranscriber.git
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

### 4. Setup Environment Variables

Create a `.env` file in the root directory of the project and add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note**: Replace `your_openai_api_key_here` with your actual OpenAI API key. You can obtain an API key from the [OpenAI Dashboard](https://platform.openai.com/account/api-keys).

## ⚙️ Usage

### Basic Usage

Run the main script with the path to your audio or video file:

```bash
python main.py --input video.mp4 --language en
```


## 🤝 Contributing

Contributions are welcome! If you'd like to enhance the project, follow these steps:

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

## 📧 Contact

For any questions or suggestions, feel free to open an issue or contact me at [your-email@example.com](mailto:your-email@example.com).

## 📚 Acknowledgements

- [OpenAI](https://www.openai.com/) for the Whisper API.
- [Pydub](https://github.com/jiaaro/pydub) for audio manipulation.
- [dotenv](https://github.com/theskumar/python-dotenv) for environment variable management.

---

Feel free to customize this `README.md` further to better fit your project's specific needs and to add any additional sections or information you find necessary.