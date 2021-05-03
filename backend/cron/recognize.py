# encoding=UTF-8
# Клонирует или обновляет репозитории
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import json
import os
import os.path
import pymysql
import traceback
import time
import sys
import re
import subprocess
import io
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from scipy.io import wavfile
from pydub import AudioSegment
from pydub.silence import split_on_silence
from socketserver import *
import noisereduce as nr
import os
import wave
import numpy as np
import concurrent.futures
import soundfile as sf

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path + "/../")

import reviewgramdb
from reviewgramlog import *
from pythonlanguage import PythonLanguage
from genericlanguage import GenericLanguage

file = os.path.dirname(os.path.abspath(__file__)) + "/recognize_pid.txt"
env_path = Path(path + "/../") / '.env'
load_dotenv(dotenv_path=env_path)
#os.chdir(path + "/../repos/");

def ogg2wav_convert(old, new):
    result = subprocess.run(['ffmpeg', "-hide_banner", "-loglevel", "panic", "-y", "-i", old, new], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stderr.decode("UTF-8")

def try_recognize_voice(arg):
    hints = arg[0]
    fileName = arg[1]
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    sample_rate_hertz = 48000
    language_code = 'en-US'
    model = 'command_and_search'
    config = {'encoding': encoding, 'sample_rate_hertz': sample_rate_hertz, 'language_code': language_code, 'model': model, 'speech_contexts': [ speech.types.SpeechContext(phrases=hints) ]}
    streaming_config = types.StreamingRecognitionConfig(config=config)
    content = ""
    with io.open(fileName, "rb") as f:
        content = f.read()
    audio = {'content': content}
    stream = [content]
    requests = (types.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream)
    client = speech.SpeechClient.from_service_account_file(os.getenv("GOOGLE_SPEECH_CREDENTIALS"))
    responses = client.streaming_recognize(streaming_config, requests)
    total_result = []
    for response in responses:
        for result in response.results:
            alternative = result.alternatives[0]
            total_result.append(alternative.transcript)
    return " ".join(total_result)

def try_recognize(fileName, table, lang, sourceFileContent):
    start = time.perf_counter() 
    perfLogFileName =  os.getenv("APP_FOLDER") + "/perf_log.txt"
    fileObject = open(perfLogFileName, 'at')
    hints = []
    for row in table:
        hints.append(row[1])
    if lang is not None:
        hints = hints + lang.getRecognitionHints()
    measure1 = time.perf_counter()
    fileObject.write("Making hints table: " + str(measure1 - start)  + "\n")
    source = fileName 
    
    rate, data = wavfile.read(fileName) 
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
    measure2 = time.perf_counter()
    fileObject.write("Denoising: " + str(measure2 - measure1)  + "\n")
    
    original = AudioSegment.from_wav(source)
    chunks = split_on_silence (
        original, 
        min_silence_len = 300,
        silence_thresh = -70
    )

    print("Split file " + source + " into "  + str(len(chunks)) + "")
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
        args.append([hints, my_dest])
    measure3 = time.perf_counter()
    fileObject.write("Split on silence: " + str(measure3 - measure2)  + "\n")

    result = ""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(try_recognize_voice, arg) for arg in args]
        result = " ".join([future.result() for future in futures])

    measure4 = time.perf_counter()
    fileObject.write("Recognition: " + str(measure4 - measure3)  + "\n")
    
    for arg in args:
        os.remove(arg[1])

    measure5 = time.perf_counter()
    fileObject.write("Removing files: " + str(measure5 - measure4)  + "\n")
    
    if (lang is None):
        lang = GenericLanguage()
    new_result = lang.recognizeStatement(result, table, sourceFileContent)

    measure6 = time.perf_counter()
    fileObject.write("recognizeStatement: " + str(measure6 - measure5)  + "\n")

    fileObject.close()
    return new_result
    
def select_and_perform_task():
    expiration_time = 30 * 60
    start = time.perf_counter() 
    con = reviewgramdb.connect_to_db()
    perfLogFileName =  os.getenv("APP_FOLDER") + "/perf_log.txt"
    fileObject = open(perfLogFileName, 'at')
    with con:
        timestamp = int(time.time())
        request = "SELECT" \
              "   r.ID, " \
              "   r.FILENAME, " \
              "   r.RES," \
              "   r.LANG_ID," \
              "   r.LOG," \
              "   r.CONTENT,"  \
              "   r.REPO_ID " \
              " FROM " \
              "`recognize_tasks` AS r  " \
              " WHERE  " \
              " ((DATE_START IS NULL) OR (" + str(timestamp) + " - UNIX_TIMESTAMP(`DATE_START`) >= " + str(expiration_time) + ")) AND (DATE_END IS NULL) " \
              " LIMIT 1 "
        row = reviewgramdb.select_and_fetch_one(con, request, [])
        if (row is not None):
            id = row[0]
            fileName = row[1]
            if (row[6] is not None):
                repoId = int(row[6])
            else:
                repoId = 0
            table = []
            rows = reviewgramdb.select_and_fetch_all(con, "SELECT FROM_TEXT, TO_TEXT FROM `replace_tables` WHERE `REPO_ID` = %s ORDER BY `ID` ASC" ,[repoId])
            for localRow in rows:
                table.append([localRow[0], localRow[1]])
            langId = 0
            if (row[3] is not None):
                langId = int(row[3])
            lang = None
            if (langId == 1):
                lang = PythonLanguage()
            content = ""
            if (row[5] is not None):
                content = row[5]
            measure1 = time.perf_counter()
            fileObject.write("Fetching task from db: " + str(measure1 - start)  + "\n")
            reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `DATE_START` = NOW()  WHERE `ID` = %s", [id])
            if (os.path.exists(fileName) and os.path.isfile(fileName)):
                try:
                    print(fileName)
                    newFileName = fileName.replace("ogg", "wav")
                    errors = ogg2wav_convert(fileName, newFileName)
                    if (len(errors) > 0):
                        print("Errors while converting ogg to wav:" + errors)
                        reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Errors in running ffmpeg ' + errors, id])
                    else:
                        reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Processed ogg 2 wav', id])
                        print("Recognizing...")
                        result = try_recognize(newFileName, table, lang, content)
                        measure2 = time.perf_counter()
                        fileObject.write("Total run for try_recognize: " + str(measure2 - measure1)  + "\n")
                        reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", [result, 'Successfully processed result', id])
                        measure3 = time.perf_counter()
                        fileObject.write("Updating result in DB: " + str(measure3 - measure2)  + "\n")
                    fileObject.close()
                except Exception as e:
                    fileObject.close()
                    print('Exception: ' + traceback.format_exc())
                    reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Exception: ' + traceback.format_exc(), id])
            else:
                fileObject.close()
                reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Unable to find file ', id])
            reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `DATE_END` = NOW()  WHERE `ID` = %s", [id])
    print("Performed")



class TCPHandler(StreamRequestHandler):
    def handle(self):     
        select_and_perform_task()


def pid_exists(pid): 
    if pid < 0: return False
    try:
        os.kill(pid, 0) 
    except ProcessLookupError:
        return False
    except PermissionError:
        return True 
    else:
        return True


if __name__== "__main__":
    host = '127.0.0.1'
    port = 9090
    addr = (host,port)

    mypid = os.getpid()

    print("PID storage file " + file)
    notRunningAlready = True
    if (os.path.isfile(file)):
        with open(file, 'rt') as handle:
            pid = handle.read().replace('\n', '')
            try:
                pid = int(pid)
            except:
                pid = -1
            notRunningAlready = not pid_exists(pid)

    if (notRunningAlready):
        print("Running with pid: " + str(mypid))
        with open(file, 'wt') as handle:
            handle.write(str(mypid))
        i = 0
        max = 20 #max performed tasks
        start_time = int(time.time())
        while (i < max):
            i = i + 1
            select_and_perform_task()
        print("Done serving tasks, starting task")
        server = TCPServer(addr, TCPHandler)
        server.serve_forever()
        print("Done!")