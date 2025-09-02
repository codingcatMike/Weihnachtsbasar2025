from datetime import datetime
import datetime as dt
import os
import sys


def log(message, level=0):
    info = None
    if level == 0:
        info = ('[Info] ' + message + ' --at-- ' + str(datetime.now()))
    elif level == 1:
        info = ('[Warning] ' + message + ' --at-- ' + str(datetime.now()))
    elif level == 2:
        info = ('[Error] ' + message + ' --at-- ' + str(datetime.now()))
    elif level == 3:
        info = ('[Critical Error] ' + message + ' --at-- ' + str(datetime.now()))

    os.makedirs('logs', exist_ok=True)
    if not os.path.exists('logs/log-' + str(dt.date.today()) + '.txt'):
        with open('logs/log-' + str(dt.date.today()) + '.txt', 'w') as f:
            f.write('Log file for ' + str(dt.date.today()) + '\n')
            f.write('Created at: ' + str(datetime.now()) + '\n')
            f.write('Device : ' + str(os.name) + '\n')
            f.write('User : ' + str(os.getlogin()) + '\n')
            f.write('Python version : ' + str(sys.version) + '\n')
            f.write('--------------------------------------------------' + '\n')
            f.write('\n')

    with open('logs/log-' + str(dt.date.today()) + '.txt', 'a') as f:
        f.write(info + '\n')
