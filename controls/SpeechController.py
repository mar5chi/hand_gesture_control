import subprocess
import os
import signal

class SpeechController:
    """ This class handles the speech output to give an auditive feedback to the user's input. """
    def __init__(self):
        self.pid = None
        self.proc = None
        #------------------------------------------------
        #print(f'SpeechController pid: {self.pid}')
        #------------------------------------------------

    def say(self, text):
        #print(f'SpeechController say(): {text}')
        #print(f'SpeechController os.getpid(): {os.getpid()}')
        p = subprocess.Popen(["espeak","-s180 -ven+18 -z",text])
        p.daemon = True
        #print(p)
        #print(f'SpeechController say() p.pid: {p.pid}')
        self.proc = p
        self.pid = p.pid

    def kill_proc(self):
        if self.pid is not None:
            #print(f'SpeechController kill_proc(): {self.pid}')
            os.kill(self.pid, signal.SIGKILL)
        self.pid = None
        self.proc = None
