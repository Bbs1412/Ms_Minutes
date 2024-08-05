import os
import time
import gtts
import openai
import subprocess
import RPi.GPIO as GPIO
import speech_recognition as sr


# Enter your API key here:
key = "your_key"
openai.api_key = key 


# Initialize the recognizer
recognizer = sr.Recognizer()

# setting up paths
pathRecordingOn = "./assets/alerts/rec_on_Fb.wav"
pathRecordingOff = "./assets/alerts/rec_google_off.wav"
pathRecordingFailed = "./assets/alerts/rec_failed.wav"
pathCouldntUnderstand = "./assets/alerts/pooja_couldnt_understand.wav"

# Define a function to capture audio and convert to text
def capture_audio():
    with sr.Microphone() as source:
        # Adjust for ambient noise
        print("\n\n** Say something...")
        subprocess.run(["aplay", pathRecordingOn, "-D", "plughw:1,0"])
        recognizer.adjust_for_ambient_noise(source)

        # Record audio with a timeout
        # audio = recognizer.listen(source, timeout=10)
        # removing timeout fixes the error of timeout leaving the while loop 
        audio = recognizer.listen(source)
        print("Mic turned off...")
        subprocess.run(["aplay", pathRecordingOff, "-D", "plughw:1,0"])

        try:
            # Recognize speech using Google Web Speech API
            prompt = recognizer.recognize_google(audio)
            return prompt        
        
        except sr.UnknownValueError:
            print("\n\n** Sorry, I couldn't understand what you said.")
            subprocess.run(["aplay", pathCouldntUnderstand, "-D", "plughw:1,0"])
            return 

        except sr.RequestError as e:
            print(e)
            subprocess.run(["aplay", pathRecordingFailed, "-D", "plughw:1,0"])
            return 
    
        except sr.WaitTimeoutError as e3:
            print(e3)
            print("xxxxxxxxxxxxxxxxxx")
            subprocess.run(["aplay", pathRecordingFailed, "-D", "plughw:1,0"])
            return 
    
        except sr.exceptions as e2:
            print(e2)
            subprocess.run(["aplay", pathRecordingFailed, "-D", "plughw:1,0"])
            return 


def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [
        {"role": "user", "content": prompt},
        {"role": "system", "content":"Your name is Miss Minutes, developed by Bhushan Songire. You are a helpful assistant. Give your answer in the not more than 400 characters. Be precise and clear in answer and not be very verbose"}
        ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


def getResponseAndClear(response):
    #tts
    fl_name_base = "output_audio"
    fl_name_mp3 = fl_name_base+".mp3"
    fl_name_wav = fl_name_base+".wav"

    tts = gtts.gTTS(text=response, lang='en-in')
    tts.save(fl_name_mp3)
    subprocess.run(["sudo", "ffmpeg", "-i", fl_name_mp3, fl_name_wav])
    subprocess.run(["aplay", fl_name_wav])
    subprocess.run(["sudo", "rm", fl_name_mp3])
    subprocess.run(["sudo", "rm", fl_name_wav])

# Setting up the things for solenoid
# Use physical pin numbering
GPIO.setmode(GPIO.BOARD) 
# solenoid is in third pin
solenoid = 3 
# solenoid is for output in GPIO
GPIO.setup(solenoid, GPIO.OUT) 

# actually bcz of wiring solenoid is acting opposite
# so dont get confused, use true and false in opp manner.    
def unlock_solenoid_lock():
    try:
        print("Turning on")
        GPIO.output(solenoid, False)
        time.sleep(7)

        print("Turning off")
        GPIO.output(solenoid, True)

    except KeyboardInterrupt:
        print("\nExiting the program.")
        print("Turning off")
        GPIO.output(solenoid, True)
        GPIO.cleanup()

def keep_open_solenoid_lock():
    print("Turning on")
    GPIO.output(solenoid, False)

def keep_closed_solenoid_lock():
    print("Turning off")
    GPIO.output(solenoid, True)

def start_assistant():
    # prompt = input("Enter the question:\n\t")
    prompt = capture_audio()

    # prompt = "Capital of India"
    if prompt:
        print("\n\n **You said: ",prompt)
        
        # khul ja sim sim
        if ("khul" in prompt.lower()) or ("sim" in prompt.lower()):
            response = "Ok opening the lock for 7 seconds."
            print("\n",response)
            getResponseAndClear(response)
            unlock_solenoid_lock()

        elif "open the lock" in prompt.lower():
            response = "Ok opening the lock for infinite time."
            print("\n",response)
            getResponseAndClear(response)
            keep_open_solenoid_lock()

        elif "close the lock" in prompt.lower():
            response = "Ok closing the lock for infinite time."
            print("\n",response)
            getResponseAndClear(response)
            keep_closed_solenoid_lock()
        
        elif ("shut down" in prompt.lower()) or ("shutdown" in prompt.lower()):
            response = "Turning the raspberry pi off."
            print("\n",response)
            getResponseAndClear(response)
            time.sleep(5)
            subprocess.run(["aplay","./alerts/pi_shutdown.wav", "-D", "plughw:1,0"])
            # print("wait 10")
            # time.sleep(10)
            subprocess.run(["sudo","shutdown", "0"])

        else:
            response = get_completion(prompt)

            if "ai language model" in response.lower():
                # response = "Hahaha nice question. Just go and google it!"
                response = "Sorry, I am not capable of answering this question right now. Feel free to ask something else."

            print("\n",response)
            # TTS:
            getResponseAndClear(response)
    else:
        # subprocess.run(["aplay","./alerts/rec_failed.wav", "-D", "plughw:1,0"])
        print("No prompt found...")
        # exit()

# *********************************************************************

# Set pin 10 to be an input pin and 
# set initial value to be pulled low (off)
button = 10
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 

print(" ** [#] Welcome To Assistant [#]")
while True:
    try:
        if GPIO.input(button) == GPIO.HIGH:
            print("Button was pushed!")
            print("Starting the assistant!!")
            start_assistant()
    except KeyboardInterrupt:
        print("\nExiting the entire program.")
        GPIO.cleanup()



"""
Connect the Realy 3 pins
(pin1) 3.3V vcc relay
(pin3) in of relay
(pin2) 5V push button +ve directly 
(pin6) GND of relay 
(pin10) push buttons +ve side
"""