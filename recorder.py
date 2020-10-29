import argparse
#import collections
import logging
import os
import sys
import threading
import time

import pyperclip
from pynput import keyboard, mouse



class FunctionRecorder:
    def __init__(self, data_path='data'):
        self.data_path = data_path

        if not os.path.isdir(data_path):
            os.makedirs(data_path)

        #self.stop_recording_event = threading.Event()


    def load_functions(self):
        raise NotImplementedError


    def save(self, events):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def event_handler(self, event):
        raise NotImplementedError

    def read_variable_name(self, supress=True):
        print('Variable name: ', end='', flush=True)

        chars = []

        def on_press(key):
            if key == keyboard.Key.enter:
                if len(chars):
                    print('')
                    return False

            elif key == keyboard.Key.backspace:
                if len(chars):
                    chars.pop()
                    sys.stdout.write('\b \b') # delete previous printed character
                    sys.stdout.flush()
            else:
                try:
                    char = key.char
                    if char.isalnum() or char == '_':
                        if len(chars) == 0 and char.isnumeric():
                            return
                        chars.append(char)
                        print(char, end='', flush=True)
                except AttributeError:
                    pass

        with keyboard.Listener(
                on_press=on_press,
                suppress=suppress
            ) as listener:
            listener.join()

        return ''.join(chars)


    def record(self, function_name):
        filename = os.path.join(self.data_path, function_name)
        if os.path.exists(filename):
            raise FileExistsError('Function "{}" already exists'.format(function_name))

        logging.info('Starting recording ...')
        logging.info('Press Ctrl+ESC to mark clipboard content as output variable')
        logging.info('Press Ctrl+ESC+O to mark paste content from input variable')
        logging.info('Press ESC to stop')

        self.events = []


    def call(self, function_name) -> dict:
        raise NotImplementedError
        return {}



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Framework engine CLI')
    parser.add_argument('-p', '--path', default='data', help='path to store function data')
    parser.add_argument('-r', '--record', help='name of function to record')
    args = parser.parse_args()

    recorder = FunctionRecorder(args.path)

    if args.record:
        recorder.record(function_name=args.record)

    #name = recorder.read_variable_name()
    #print('Read "{}"'.format(name))
