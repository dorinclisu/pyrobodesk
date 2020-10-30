import argparse
import os
import pickle
import sys
import threading
import time
from typing import List, Optional, Union

import pyperclip
from pynput import keyboard, mouse



class KeyPressEvent(keyboard.Events.Press): pass
class KeyReleaseEvent(keyboard.Events.Release): pass
class MoveEvent(mouse.Events.Move): pass
class ClickEvent(mouse.Events.Click): pass
class ScrollEvent(mouse.Events.Scroll): pass
class CopyToVarEvent(str): pass
class PasteFromVarEvent(str): pass

EventTypeAnnotation = Union [
    KeyPressEvent,
    KeyReleaseEvent,
    MoveEvent,
    ClickEvent,
    ScrollEvent,
    CopyToVarEvent,
    PasteFromVarEvent
]

class MyInputEvent():
    def __init__(self, event: EventTypeAnnotation, timestamp: Optional[float]=None):
        self.event = event

        if timestamp is None:
            timestamp = time.time()

        self.timestamp = timestamp


class FunctionRecorder:
    def __init__(self, data_path='data'):
        self.data_path = data_path

        if not os.path.isdir(data_path):
            os.makedirs(data_path)


    def load_functions(self):
        raise NotImplementedError


    def save(self, events, filepath):
        with open(filepath, 'wb') as file:
            pickle.dump(events, file)


    def load(self, filepath):
        with open(filepath, 'rb') as file:
            events = pickle.load(file)
        return events


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
        if os.path.isfile(filename):
            raise FileExistsError('Function "{}" already exists'.format(function_name))

        print('Starting recording ...')
        print('Press Ctrl+ESC to mark clipboard content as output variable')
        print('Press Ctrl+ESC+O to mark paste content from input variable')
        print('Press ESC to stop')

        myevents: List[MyInputEvent] = []
        stop_event = threading.Event()

        def on_press(key):
            if key == keyboard.Key.esc:
                stop_event.set()
                return False
            myevent = MyInputEvent(KeyPressEvent(key))
            myevents.append(myevent)

        def on_release(key):
            myevent = MyInputEvent(KeyReleaseEvent(key))
            myevents.append(myevent)

        listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        listener.start()

        # mlistener = mouse.Listener(
        #     on_move=on_move,
        #     on_click=on_click,
        #     on_scroll=on_scroll
        # )
        # mlistener.start()

        last_move_event = None

        with mouse.Events() as events:
            while True:
                if stop_event.is_set():
                    stop_event.clear()
                    break

                event = events.get(0.5)
                if event is None:
                    continue

                if isinstance(event, mouse.Events.Move):
                    myevent = MyInputEvent(MoveEvent(x=event.x, y=event.y))

                    if last_move_event:
                        if myevent.timestamp - last_move_event.timestamp < 0.1:
                            continue # no need to keep all move events
                    last_move_event = myevent

                elif isinstance(event, mouse.Events.Click):
                    myevent = MyInputEvent(ClickEvent(x=event.x, y=event.y, button=event.button, pressed=event.pressed))

                elif isinstance(event, mouse.Events.Scroll):
                    myevent = MyInputEvent(ScrollEvent(x=event.x, y=event.y, dx=event.dx, dy=event.dy))

                else:
                    raise RuntimeError('Unrecognized mouse event: {}'.format(event))

                myevents.append(myevent)

        if myevents:
            self.save(myevents, filename)
        else:
            print('WARNING: no input events detected!')


    def play(self, function_name, **kwargs):
        filename = os.path.join(self.data_path, function_name)
        if not os.path.isfile(filename):
            raise FileNotFoundError('Function "{}" does not exist'.format(function_name))

        myevents = self.load(filename)

        key_controller = keyboard.Controller()
        mouse_controller = mouse.Controller()

        print('Starting play ...')

        recording_start_time = myevents[0].timestamp
        delta_reference = time.time() - recording_start_time + 0.01

        for myevent in myevents:
            event = myevent.event
            timestamp = myevent.timestamp

            delta = time.time() - timestamp
            if delta < delta_reference:
                time.sleep(delta_reference - delta)
            else:
                print('WARNING: Event replay lags real-time')

            if isinstance(event, KeyPressEvent):
                key_controller.press(event.key)

            elif isinstance(event, KeyReleaseEvent):
                key_controller.release(event.key)

            elif isinstance(event, MoveEvent):
                mouse_controller.position = (event.x, event.y)
                pass

            elif isinstance(event, ClickEvent):
                mouse_controller.position = (event.x, event.y) #ensure pointer is in correct place
                if event.pressed:
                    mouse_controller.press(event.button)
                else:
                    mouse_controller.release(event.button)

            elif isinstance(event, ScrollEvent):
                mouse_controller.position = (event.x, event.y) #ensure pointer is in correct place
                mouse_controller.scroll(event.dx, event.dy)

            else:
                raise RuntimeError('Unrecognized event: {}'.format(event))


    def call(self, function_name) -> dict:
        raise NotImplementedError
        return {}



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Framework engine CLI')
    parser.add_argument('-p', '--path', default='data', help='path to store function data')
    parser.add_argument('-r', '--record', help='name of function to record')
    parser.add_argument('--play', help='name of function to play')
    args = parser.parse_args()

    recorder = FunctionRecorder(args.path)

    if args.record:
        recorder.record(function_name=args.record)

    if args.play:
        recorder.play(function_name=args.play)

    #name = recorder.read_variable_name()
    #print('Read "{}"'.format(name))
