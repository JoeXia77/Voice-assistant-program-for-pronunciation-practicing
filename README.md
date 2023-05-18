# Voice Assistant for Pronunciation Practicing (VAPP)

VAPP is an AI-based tool that uses OpenAI's language model to help users with pronunciation practice. This voice assistant takes voice commands and offers different modes like conversation and practice. By default, VAPP starts in practice mode, automatically repeating what you just said for practicing. But, you can switch to conversation mode for general chatting. 

## Requirements

Before starting with VAPP, make sure you have:

- An input device (like a microphone) connected to your system to capture your voice.

- OpenAI API key. If you don't have one, you can get it by signing up on OpenAI's official website.

## Setup

To set up VAPP, follow the steps below:

1. Clone this repository to your local machine.
2. Install the necessary dependencies by running the following commands:

    ```
    pip install pyaudio
    pip install struct
    pip install wave
    pip install os
    pip install sys
    pip install openai
    pip install retry
    pip install gtts
    pip install pydub
    pip install vosk
    pip install tkinter
    ```

3. Make sure you have `ffmpeg` and `ffprobe` in your PATH. If not, add them manually:

    ```
    path_to_ffmpeg_bin = "C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin"
    os.environ["PATH"] += os.pathsep + path_to_ffmpeg_bin
    AudioSegment.converter = os.path.join(path_to_ffmpeg_bin, "ffmpeg.exe")
    AudioSegment.ffprobe   = os.path.join(path_to_ffmpeg_bin, "ffprobe.exe")
    ```

4. Replace `"your_key_like sk-123456789"` with your OpenAI API key in the line `openai.api_key = "your_key_like sk-123456789"`

## Voice Commands

Here are the voice commands you can use with VAPP:

- `'stop'`: Stops the current process.

- `'play'`: Plays the last recorded voice input.

- `'conversation mode'`: Switches VAPP to conversation mode for general chatting.

- `'practice mode'`: Switches VAPP back to practice mode where it automatically repeats your phrases for practice.

- `'repeat'`: Makes the AI repeat the same content you just said. Useful in both practice and conversation modes.

## Usage

Just start VAPP and say your command. VAPP will recognize and respond accordingly. You can switch between modes or have sentences repeated as needed.

## Contributions

VAPP is an open-source project, and we welcome contributions. If you discover any bugs or if you have a feature request, please open an issue or submit a pull request.

Please note: Keep your OpenAI API Key confidential. Do not share it publicly or upload it to public repositories.
