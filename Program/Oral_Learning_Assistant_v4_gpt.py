import pyaudio
import struct
import wave
import os
import sys
import openai
from retry import retry


## text to speech:
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

## can't find path of ffmpeg.exe and ffprobe.exe, so add them manually:
path_to_ffmpeg_bin = "C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin"
os.environ["PATH"] += os.pathsep + path_to_ffmpeg_bin
AudioSegment.converter = os.path.join(path_to_ffmpeg_bin, "ffmpeg.exe")
AudioSegment.ffprobe   = os.path.join(path_to_ffmpeg_bin, "ffprobe.exe")

## speech to text:
if not sys.warnoptions:
    os.environ['PYTHONWARNINGS'] = 'ignore:resource_warning'
from vosk import Model, KaldiRecognizer

## UI
import tkinter as tk
from tkinter import ttk

class Chatbot:
    def __init__(self):
        openai.api_key = ""
        self.history = []
        self.model = "gpt-3.5-turbo"
        self.default_conversation_length = 5
        self.max_response_length = 80

    def generate_message(self, user_input, conversation_length):
        message = {"role": "user", "content": user_input}
        self.history.append(message)
        messages = self.history[-conversation_length:]
        return messages

    @retry(ConnectionResetError, tries=3, delay=2, backoff=2)
    def respond(self, user_input):
        messages = self.generate_message(user_input, self.default_conversation_length)
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=0,
            max_tokens=self.max_response_length,
        )
        response_content = response['choices'][0]['message']['content']
        self.history.append({"role": "system", "content": response_content})
        return response_content

    def run(self):
        while True:
            user_input = input("You: ")
            if user_input == "quit":
                break
            messages = self.generate_message(user_input, self.default_conversation_length)
            response = self.get_response(messages)
            self.history.append({"role": "system", "content": response})
            print("system: " + response)





class VoicePal:
    SHORT_NORMALIZE = (1.0/32768.0)
    def __init__(self):
        self.sound_level_low = 0.02
        self.sound_level_high = 4
        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 16000
        self.audio_input = True
        self.audio_frames_per_buffer = 8192
        self.audio_record_path = "AudioRecord"
        self.audio_record_index = 0

        self.chatbot = Chatbot()


        self.command = ""
        
        self.mode = "practice"
        self.keyboard_input = False

        ## delete all files in AudioRecord folder, and create a new one
        if os.path.exists(self.audio_record_path):
            for file in os.listdir(self.audio_record_path):
                os.remove(os.path.join(self.audio_record_path, file))
        else:
            os.makedirs(self.audio_record_path)
        

    #################################### Listen ####################################

    def _byte_to_int(self, block): ## use for block = stream.read(), get the loudness and represent using float after normalized
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )
        shorts = [x* self.SHORT_NORMALIZE for x in shorts]
        return shorts

    def _get_block_average_amplitude(self, block):
        ## input a audio block in byte format
        ## output its attribute
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )
        shorts = [x*self.SHORT_NORMALIZE for x in shorts]
        block_avg = sum([abs(x) for x in shorts])/len(shorts)*100
        return [block_avg]

    def measure_noise_and_input_levels(self):
        ## add a voice reminder
        print("testing ambient noise")
        cap = pyaudio.PyAudio()
        stream = cap.open(format = self.audio_format, channels = self.audio_channels,rate = self.audio_rate,input = self.audio_input, frames_per_buffer = self.audio_frames_per_buffer)
        stream.start_stream()
        
        test_time_ambient = 5
        blocks = []
        for i in range(test_time_ambient*self.audio_rate//1000):
            print(i)
            data = stream.read(1000)
            block = self._byte_to_int(data)
            block_avg = sum([abs(x) for x in block])/len(block)*100
            blocks.append(block_avg)
        blocks.sort()
        low_level = sum(blocks[1:4])/3
        high_level = sum(blocks[-4:-1])/3
        
        stream.stop_stream()
        stream.close()
        cap.terminate()
        print("testing ambient noise done")
        self.sound_level_high = high_level
        self.sound_level_low = low_level

    def audio_to_wav(self, audio,record_path):
        ## FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        WAVE_OUTPUT_FILENAME = record_path

        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        ## waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setsampwidth(2)
        waveFile.setframerate(RATE)
        waveFile.writeframes(audio)
        waveFile.close()


    def record_audio(self, audio):
        whole_path = os.path.join(self.audio_record_path, str(self.audio_record_index)+'.wav')

        self.audio_record_index += 1
        self.audio_to_wav(audio, whole_path)
        return whole_path


    def get_audio_block(self):
        ## output: audio date in bytes format
        print()
        print('##################################')
        print('             listening')
        print('##################################')

        slience_waiting = 1
        threshold = self.sound_level_low + (self.sound_level_high-self.sound_level_low)*0.2
        cap = pyaudio.PyAudio()
        ## print(cap.get_sample_size(pyaudio.paInt16))
        stream = cap.open(format = self.audio_format, channels = self.audio_channels,rate = self.audio_rate,input = self.audio_input, frames_per_buffer = self.audio_frames_per_buffer)
        stream.start_stream()
        
        temp = []
        record = []
        is_recording = False
        slience_count = 0
        slience_waiting = int(slience_waiting*4)

        ## detect when human is making speaking and start recording
        ## decide when stop speaking then stop recording and return
        while True:
            data = stream.read(4096)
            block_avg = self._get_block_average_amplitude(data)[0]
            ## print(block_avg)
            
            if is_recording == False:
                if len(temp)>4:
                    del temp[0]
                temp.append(data)
                if block_avg>threshold:
                    ## start recording
                    record += temp
                    is_recording = True
                    
            else: ## is_recording == True
                record.append(data)
                if block_avg<=threshold:
                    slience_count+=1
                    ## stop recording, return this block
                else:
                    slience_count = 0
                
                if slience_count>slience_waiting:
                    is_recording = False
                    break
        ## clean stream
        stream.stop_stream()
        stream.close()
        cap.terminate()
        

        data = b''.join(record)
        return data

    #################################### Analyze ####################################
    def audio_to_text(self, audio):
        model      = Model('model')
        recognizer = KaldiRecognizer(model, self.audio_rate)
        recognizer.AcceptWaveform(audio)
        cur_text = recognizer.Result()
        cur_text = cur_text.split(':')[1]
        if len(cur_text)>=6:
            cur_text = cur_text[2:-3]
        return cur_text

    def detect_command(self, text):
        ## command stop: will 
        command_noise = 6
        if text == 'stop' or ((len(text)-len('stop'))< command_noise and 'stop' in text):
            self.command = 'stop'

        ## command repeat: repeat the most recent recoreded audio
        if text == 'play' or ((len(text)-len('play'))<command_noise and 'play' in text):
            self.command = 'play'
        
        ## command repeat
        if text == 'repeat' or ((len(text)-len('repeat'))<command_noise and 'repeat' in text):
            self.command = 'repeat'
            
        ## command response
        if text == 'response' or ((len(text)-len('response'))<command_noise and 'response' in text):
            self.command = 'response'
            
        ## command practice mode
        if text == 'practice mode' or ((len(text)-len('practice'))<command_noise and 'practice' in text):
            self.command = 'practice mode'
        
        ## command conversation mode
        if text == 'conversation mode' or ((len(text)-len('conversation'))<command_noise and 'conversation' in text):
            self.command = 'conversation mode'
        
        ## command input
        if text == 'input' or ((len(text)-len('input'))<command_noise and 'input' in text):
            self.command = 'keyboard input'
        
        




    #################################### React ####################################

    def play_recorded_audio(self, file_path):
        wav_file = wave.open(file_path, 'rb')
        audio_format = pyaudio.paInt16
        audio_channels = wav_file.getnchannels()
        audio_rate = wav_file.getframerate()
        audio_frames_per_buffer = 1024

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=audio_format,
            channels=audio_channels,
            rate=audio_rate,
            output=True,
            frames_per_buffer=audio_frames_per_buffer
        )

        data = wav_file.readframes(audio_frames_per_buffer)
        while data:
            stream.write(data)
            data = wav_file.readframes(audio_frames_per_buffer)

        stream.stop_stream()
        stream.close()
        pa.terminate()
        wav_file.close()

    def speak(self, text):
        # convert text to speech using the Google Text-to-Speech API
        tts = gTTS(text=text, lang='en')
        # save the audio to a file
        filename = "abc.mp3"
        tts.save(filename)

        # load the audio file and play it back
        audio = AudioSegment.from_file(filename, format="mp3")
        play(audio)

        # delete the audio file
        os.remove(filename)


    def run_practice_mode(self):
        while self.mode == "practice":
            audio = self.get_audio_block()
            text = self.audio_to_text(audio)
            print('my text: ',text)
            
            self.detect_command(text)
            if self.command:
                if self.command == 'stop':
                    self.mode = ""
                    self.command = ''
                    break
                if self.command == 'play':
                    self.command = ''
                    whole_path = os.path.join(self.audio_record_path, str(self.audio_record_index-1)+'.wav')
                    self.play_recorded_audio(whole_path)
                if self.command == 'conversation mode' and self.mode!="conversation":
                    self.command = ''
                    self.mode = 'conversation'
                    self.speak("switch to conversation mode")
                    break
                if self.command == 'practice mode' and self.mode!="practice":
                    self.command = ''
                    self.mode = 'practice'
                    self.speak("switch to practice mode")
                    break
                if self.command == 'repeat':
                    self.command = ''
                    ## find the text from history
                    if self.chatbot.history:
                        self.speak(self.chatbot.history[-1]['content'])
                    continue
                    
                
                    
            audio_path = self.record_audio(audio)
            self.play_recorded_audio(audio_path)
            ## self.speak(text)
            
            

    def run_conversation_mode(self):
        while self.mode == "conversation":
            if self.keyboard_input:
                ## let user to input
                text = input("Waiting for user input.\nYou: ")
                self.keyboard_input = False
                self.speak(text)
                audio = None
            else:
                ## get audio from microphone
                audio = self.get_audio_block()
                text = self.audio_to_text(audio)
                print('You: ', text)
            
            self.detect_command(text)
            if self.command:
                if self.command == 'stop':
                    self.command = ''
                    self.mode = ""
                    break
                if self.command == 'play':
                    self.command = ''
                    whole_path = os.path.join(self.audio_record_path, str(self.audio_record_index-1)+'.wav')
                    self.play_recorded_audio(whole_path)
                if self.command == 'conversation mode' and self.mode!="conversation":
                    self.command = ''
                    self.mode = 'conversation'
                    self.speak("switch to conversation mode")
                    break
                if self.command == 'practice mode' and self.mode!="practice":
                    self.command = ''
                    self.mode = 'practice'
                    self.speak("switch to practice mode")
                    break
                if self.command == 'keyboard input':
                    self.command = ''
                    self.keyboard_input = True
                    continue
                if self.command == 'repeat':
                    self.command = ''
                    ## find the text from history
                    if self.chatbot.history:
                        self.speak(self.chatbot.history[-1]['content'])
                    continue
                    
                ## reset the command
                self.command = ''
    
            else:
                ## respond
                # Save audio to file
                if audio:
                    audio_path = self.record_audio(audio)
                    
                # Get chatbot response
                response = self.chatbot.respond(text)
    
                print("System: " + response)
        
                # Speak the response
                self.speak(response)


    def run(self):
        ## if not self.mode 
        while self.mode:
            if self.mode == "practice":
                self.run_practice_mode()
            if self.mode == "conversation":
                self.run_conversation_mode()


        self.speak("good bye")
        return





pal = VoicePal()
## pal.measure_noise_and_input_levels()
pal.run()





























