

from vosk import Model, KaldiRecognizer
import wave
import pyaudio
import struct
SHORT_NORMALIZE = (1.0/32768.0)
from gtts import gTTS
import os
import playsound
import tkinter as tk
import random


model      = Model('model')
recognizer = KaldiRecognizer(model,16000)
commands = ['stop','repeat','speak']
sound_level_low,sound_level_high = 0.1, 2



def speak(text):
    tts = gTTS(text = text, lang = 'en')
    filename = "abc.mp3"
    tts.save(filename)
    playsound.playsound(filename)
    os.remove(filename)



def play_sound(file_name):
    # Set chunk size of 1024 samples per data frame
    chunk = 1024 
     
    # Open the soaudio/sound file
    af = wave.open(file_name, 'rb')
     
    # Create an interface to PortAudio
    pa = pyaudio.PyAudio()
     
    # Open a .Stream object to write the WAV file
    # 'output = True' indicates that the
    # sound will be played rather than
    # recorded and opposite can be used for recording
    stream = pa.open(format = pa.get_format_from_width(af.getsampwidth()),
                    channels = af.getnchannels(),
                    rate = af.getframerate(),
                    output = True)
     
    # Read data in chunks
    rd_data = af.readframes(chunk)
    
    # Play the sound by writing the audio
    # data to the Stream using while loop
    while len(rd_data)!=0:
    ##while rd_data != b'':
        stream.write(rd_data)
        rd_data = af.readframes(chunk)
     
    # Close and terminate the stream
    stream.stop_stream()
    stream.close()
    pa.terminate()



def analyze_block(block):
    ## input a audio block in byte format
    ## output its attribute
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )
    shorts = [x*SHORT_NORMALIZE for x in shorts]
    block_avg = sum([abs(x) for x in shorts])/len(shorts)*100
    
    return [block_avg]
    

def byte_to_int(block): ## use for block = stream.read()

    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )
    shorts = [x*SHORT_NORMALIZE for x in shorts]
    return shorts




def test_ambient_sound():
    
    text = 'Now we are going to test your ambient sound, please say something in the next 5 seconds'
    speak(text)
    
    cap = pyaudio.PyAudio()
    stream = cap.open(format = pyaudio.paInt16, channels = 1,rate = 16000,input = True, frames_per_buffer = 8192)
    stream.start_stream()
    
    test_time_ambient = 5
    blocks = []
    for i in range(test_time_ambient*16):
        print(i)
        data = stream.read(1000)
        block = byte_to_int(data)
        block_avg = sum([abs(x) for x in block])/len(block)*100
        blocks.append(block_avg)
    blocks.sort()
    low_level = sum(blocks[1:4])/3
    high_level = sum(blocks[-4:-1])/3
    
    stream.stop_stream()
    stream.close()
    cap.terminate()
    return (low_level,high_level)
    
    
    




def block_voice_gathering(sound_level_low,sound_level_high,slience_waiting = 1):
    ## output: text and audio data
    print('##################################')
    print('             listening')
    print('##################################')
    ## detect when human is making speaking and start recording
    ## decide when stop speaking then stop recording and return
    ## output is cur_text and data
    threshold = sound_level_low + (sound_level_high-sound_level_low)*0.2
    
    cap = pyaudio.PyAudio()
    ## print(111111111111)
    ## print(cap.get_sample_size(pyaudio.paInt16))
    stream = cap.open(format = pyaudio.paInt16, channels = 1,rate = 16000,input = True, frames_per_buffer = 8192)
    stream.start_stream()
    
    temp = []
    record = []
    is_recording = False
    slience_count = 0
    slience_waiting = int(slience_waiting*4)
    while True:
        data = stream.read(4096)
        block_avg = analyze_block(data)[0]
        print(block_avg)
        
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
    
    stream.stop_stream()
    stream.close()
    cap.terminate()
    
    data = b''.join(record)
    
    
    '''
    cur_text = ''
    if recognizer.AcceptWaveform(data):
        cur_text = recognizer.Result()

    else:
        cur_text = recognizer.PartialResult()
    '''
    
    recognizer.AcceptWaveform(data)
    cur_text = recognizer.Result()
    cur_text = cur_text.split(':')[1]
    if len(cur_text)>=6:
        cur_text = cur_text[2:-3]

    
    return (cur_text,data)





def save_into_wav(audio,prev_record_path):
    
    ## FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = prev_record_path

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    ## waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setsampwidth(2)
    waveFile.setframerate(RATE)
    waveFile.writeframes(audio)
    waveFile.close()

def clear_path(path):
    ## create folder to store all records
    if not os.path.exists(path):
        os.mkdir(path)
    ## empty records folder
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))


def welcome():
    ## for demo use, will have some interaction with user
    ## it is a while loop 
    ## will break when 
    speak('Welcome to this project')
    ## GUI
    root = tk.Tk()
    root.geometry("800x600")
    recording_label = tk.Label(root,text = 'Not Recording',font=('times', 40),width = 780)
    recording_label.pack()
    
    var = tk.StringVar()
    myLabel = tk.Message(root,textvariable = var,relief = tk.RAISED)
    myLabel.config(font=('times', 24, 'italic'),padx = 10,pady = 10,width = 400)

    ## myLabel = tk.Label(root,text = '',font=("Helvetica",20), fg= "blue")
    var.set('Welcome to this project')
    myLabel.pack(pady=20,fill=tk.BOTH)
    root.update()
    
    ################# Text #######################
    
    ## note, preset question should be all lower case and no parameter
    cmd1 = 'stop'
    ans1 = 'OK, good bye'
    cmd2 = 'practice mode'
    ans2 = 'switching'
    cmd3 = 'yes'
    ans3 = 'OK!'
    que4 = 'hello'
    ans4 = 'Hello, I am here.'
    que5 = 'can you tell me what you can do’'
    ans5 = 'I can help you to improve your pronunciation, I will record your voice and replay it to you, making you embarrassed by your plain pronunciation, I think motivation is the key to success'
    que6 = 'so you are a sound recorder'
    ans6 = 'This is very disrespectful. I am able to judge when you stop speaking and automatically replay your funny voice and, always ready to catch your next voice. And, If you beg me, I will teach you using a much standard voice to repeat what you have just said.'
    que7 = 'sounds better do you like to handle this demonstration'
    ans7 = 'I think that is your job, I am just a ruthless machine'
    ## ans7 = 'I will repeat what you said, and then you can hear your own pronunciation. You can also give me voice commands, for example, you say speak, and then I will repeat what you say in a standard pronunciation.'
    que8 = "anyway let's see if you are boasting yourself"
    ans8 = 'I am ready'
    
    q_a = [[cmd1,ans1],[cmd2,ans2],[cmd3,ans3],[que4,ans4],[que5,ans5],[que6,ans6],[que7,ans7],[que8,ans8]]
    
    
    q_a = [[x[0].split(' '),x[1]] for x in q_a]
    
    def match(text,q_a):
        ## input is the recognized text, and question and answers
        ## output the index of q_a 
            ## if not recognized as any question, return -1
            ## you can play sound by speak(q_a[i][1])
        text_words = text.split(' ')
        

        ## match rules:
        ## len_punish: length of two text should be similar, or will be punished somehow
        ## match_score: it will see if all the information in the preset question is mentioned in the text
        ## note, preset question should be all lower case and no parameter
        for i in range(len(q_a)):
            cur_q,_ = q_a[i]
            cur_q = cur_q.copy()
            ## compare is cur_q is same with text word
            len_punish = (len(text_words)-len(cur_q))/len(cur_q)
            ori_len = len(cur_q)
            divider_count = len(cur_q)
            for word in text_words:
                if word in cur_q:
                    cur_q.remove(word)
            
            match_score = (ori_len-len(cur_q))/ori_len
            ## match socre in range (0,1),average 0.7
            ## len_punish in range(0,3),
            similar_threshold = 0.70
            total_score = match_score - len_punish*0.3
            print(total_score,match_score,len_punish*0.3)
            print(q_a[i][0],text_words)
            if total_score>similar_threshold:
                return i
        else:
            return -1

    ## listening part
    while True:
        recording_label.config(text = 'Recording....',fg = 'red')
        root.update()
        text,audio = block_voice_gathering(sound_level_low,sound_level_high)
        
        recording_label.config(text = 'Not Recording',fg = 'black')
        root.update()
        print('you seems talking about: ',text)
        var.set(text)
        ## myLabel.configure(text = text)
        root.update()
        
        ## find how to answer it
        match_res = match(text,q_a)
        ## sorry part
        if match_res == -1:
            dice = random.randint(0,2)
            if dice == 0:
                speak("sorry, I didn't understand, could you repeat that?")
            if dice == 1:
                speak("could you repeat it for me?")
            if dice == 2:
                speak("Sorry, could you say it in another way?")
        ## match success and answering
        elif match_res == 0:
            ## exit program
            speak('OK')
            root.destroy()
            break
        elif match_res == 1:
            text = q_a[match_res][1]
            speak(text)
            root.destroy()
            break
        else:
            text = q_a[match_res][1]
            speak(text)


def main_code():
    
    ## record path settings
    path = 'records'
    file_name = 'record'
    file_index = 1
    clear_path(path)
    
    ## ambient sound level test
    sound_level_low,sound_level_high = 0.1,4
    sound_level_low,sound_level_high = test_ambient_sound()
    print(f'Noise level is {sound_level_low} and your voice level is {sound_level_high}')
    if sound_level_high/sound_level_low>20:
        text = 'your input device seems working great, now we can continue for the next step'
        print(text)
        speak(text)
    else:
        text = 'your input device seems not working well, try restart the program or replace your input device'
        print(text)
        speak(text)
        return None
    
    welcome()
    
    
    ## Gui

    root = tk.Tk()
    root.geometry("800x600")
    recording_label = tk.Label(root,text = 'Not Recording',font=('times', 40),width = 780)
    recording_label.pack()
    
    
    var = tk.StringVar()
    myLabel = tk.Message(root,textvariable = var,relief = tk.RAISED)
    myLabel.config(font=('times', 24, 'italic'),padx = 10,pady = 10,width = 400)

    ## myLabel = tk.Label(root,text = '',font=("Helvetica",20), fg= "blue")
    var.set('Welcome to this project')
    myLabel.pack(pady=20,fill=tk.BOTH)
    root.update()
    
    

    ## gather a block of voice
        ## if this block is not a command
            ## save it and replay it
        ## if this is a command
            ## execute the command
            

            
            
    text = 'practice mode'
    speak(text)
    
    prev_text = 'Listening'
    while True:
        print(f'{file_index}st loop, ','recording your voice now')
        recording_label.config(text = 'Recording....',fg = 'red')
        root.update()
        text,audio = block_voice_gathering(sound_level_low,sound_level_high)
        recording_label.config(text = 'Not Recording',fg = 'black')
        root.update()
        print('you seems talking about: ',text)
        var.set(text)
        ## myLabel.configure(text = text)
        root.update()
        if text not in commands: ## save it
            prev_text = text
            total_path = os.path.join(path,file_name+str(file_index)+'.wav')
            save_into_wav(audio,total_path)
            file_index+=1
            
            print('we will play your sound again for once')
            print('.........replaying..........')
            total_path = os.path.join(path,file_name+str(file_index-1)+'.wav')
            play_sound(total_path)
            print('reply finished')
            
        else:
            print('this seems to be a command')
            print(2)
            cmd = text
            if cmd == 'stop':
                print(f'{cmd} command has been triggered')
                speak('OK, good bye')
                root.destroy()
                break
            if cmd == 'repeat':
                total_path = os.path.join(path,file_name+str(file_index-1)+'.wav')
                play_sound(total_path)
            if cmd == 'speak':
                speak(prev_text)
                
            else:
                pass
        
main_code()



'''
def main_code():
    
    ## text = 'now we can start practicing your english, if you read a sentence or paragraph, you will automatically get a reply for once'
    text = 'start now'
    speak(text)
    
    cap = pyaudio.PyAudio()
    stream = cap.open(format = pyaudio.paInt16, channels = 1,rate = 16000,input = True, frames_per_buffer = 8192)
    stream.start_stream()

    count = 0
    ## this while loop will loop twice per second, no matter what
    ## the recognizer will 
    while True:
        data = stream.read(4096)
        
        block = byte_to_int(data)
        block_avg = sum([abs(x) for x in block])/len(block)*100
    
        count+=1
        print(count)
        
        cur_text = ''
        if recognizer.AcceptWaveform(data):
            cur_text = recognizer.Result()
        else:
            cur_text = recognizer.PartialResult()
        print(cur_text)
        if cur_text == 'stop':
            print('command stop')
            break
        if cur_text == 'repeat':
            pass
            
    

## main_code()


'''





