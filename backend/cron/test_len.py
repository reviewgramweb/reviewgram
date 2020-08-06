from scipy.io import wavfile
from pydub import AudioSegment
from pydub.silence import split_on_silence
import noisereduce as nr
import os
import wave
import numpy as np
import concurrent.futures
import soundfile as sf

import io
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
from google.cloud.speech_v1 import types
import subprocess

source = "/root/reviewgram/records/3b40df3a-9ecc-4544-9ea2-3f2c3e657af5-1596654876.341333.ogg"
def ogg2wav_convert(old, new):
    result = subprocess.run(['ffmpeg', "-hide_banner", "-loglevel", "panic", "-y", "-i", old, new], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stderr.decode("UTF-8")

ogg2wav_convert(source, "/root/reviewgram/records/8b93eeaa-548f-4b0d-9df1-fa70e0fc8b57-1596653786.1714177.wav")
source = "/root/reviewgram/records/8b93eeaa-548f-4b0d-9df1-fa70e0fc8b57-1596653786.1714177.wav"


table = []


def recognize_data(fileName):
    credentials = "/root/reviewgram/credentials.json"
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    sample_rate_hertz = 48000
    language_code = 'en-US'
    model = 'command_and_search'
    config = {'encoding': encoding, 'sample_rate_hertz': sample_rate_hertz, 'language_code': language_code, 'model': model, 'speech_contexts': [ speech_v1.types.SpeechContext(phrases=['insert', 'tab', 'space', 'juggle', 'remove', 'master', 'branch', 'backend', 'frontend', 'main', 'dot', 'py', 'import', 'os', 'sys', 'pymongo', 'tokenize', 'untokenize', 'comma', 'op', 'colon', 'semicolon', 'quote', 'single', 'round', 'square', 'curvy', 'bracket', 'opening', 'closing', 'left', 'right', 'brace', 'caret', 'modulus', 'floor', 'division', 'ampersand', 'bitwise', 'assign', 'arrow', 'lambda', 'def', 'as', 'while', 'assert', 'del', 'async', 'elif', 'yield', 'shell', 'utilities', 'unit', 'test', 'find', 'copy', 'path', 'json', 'calendar', 'pickle', 'iteration', 'tools', 'weak', 'built-ins', 'debug', 'functools', 'context', 'heap', 'queue', 'warnings', 'doc', 'structure', 'string', 'config', 'parser', 'shelve', 'tar', 'temp', 'error', 'file', 'mapping', "parse", "signal", "select", "registry", "asynchronous", "chat", "core"]) ]}
    content = ""
    with io.open(fileName, "rb") as f:
        content = f.read()
    audio = {'content': content}
    client = speech_v1.SpeechClient.from_service_account_file(credentials)
    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result()
    total_result = []
    for result in response.results:
        alternative = result.alternatives[0]
        total_result.append(alternative.transcript)
    return " ".join(total_result)

rate, data = wavfile.read(source) 

length = len(data)/rate
noise_length = 1

dest = source
reduce = False
if (length > 2.0):
    data = data/1.0
    reduce = True
    rate, data = wavfile.read(source) 
    data = data/1.0
    noisy_part = data[0:rate*noise_length]
    


original = AudioSegment.from_wav(source)
chunks = split_on_silence (
    original, 
    min_silence_len = 300,
    silence_thresh = -70
)

print(len(chunks))

args = []
for i, chunk in enumerate(chunks):
    my_dest = dest + "-" + str(i) + ".wav"
    chunk.export(my_dest, format="wav")
    #if (reduce):
    #    rate, data = wavfile.read(my_dest) 
    #    data = data/1.0
    #    reduced_noise = nr.reduce_noise(audio_clip=data, noise_clip=noisy_part, verbose=True)
    #    wavfile.write(my_dest, rate, reduced_noise)
    data, samplerate = sf.read(my_dest)
    sf.write(my_dest, data, samplerate, subtype='PCM_16')
    args.append(my_dest)
    
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(recognize_data, arg) for arg in args]
    print(" ".join([future.result() for future in futures]))

print(recognize_data(source))