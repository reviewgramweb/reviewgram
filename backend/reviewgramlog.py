from datetime import datetime
import time
import os

# Запись данных в лог
def append_to_log(text):
    date_time_now = datetime.now()
    str_date_time = date_time_now.strftime("%d-%m-%Y (%H:%M:%S)")
    text_file = open(os.getenv("APP_FOLDER") + "/log.txt", "a")
    text_file.write("["  + str_date_time + "]" + text + "\n")
    text_file.close()
