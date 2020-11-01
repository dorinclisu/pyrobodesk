import argparse
import os
import pickle
import sys
import threading
import time
from typing import Dict, List, Optional, Union

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
    def __init__(self, event: EventTypeAnnotation, timestamp: Optional[float]=None, time_delta: Optional[float]=None):
        self.event = event

        if timestamp is None:
            timestamp = time.time()

        if time_delta:
            timestamp -= time_delta

        self.timestamp = timestamp


class MyFunction():
    def __init__(self, events: List[MyInputEvent], input_variables: List[str]=[], output_variables: List[str]=[]):
        self.events = events
        self.input_variables = input_variables
        self.output_variables = output_variables


class FunctionManager:
    def __init__(self, data_path: str='data'):
        if data_path[0:2] == '~/':
            data_path = os.path.join(os.path.expanduser('~'), data_path[2:])

        self.data_path = data_path

        if not os.path.isdir(data_path):
            os.makedirs(data_path)


    def save(self, myfunction: MyFunction, filepath: str):
        #TODO: use more robust serialization
        with open(filepath, 'wb') as file:
            pickle.dump(myfunction, file)


    def load(self, filepath: str) -> MyFunction:
        with open(filepath, 'rb') as file:
            myfunction = pickle.load(file)
        return myfunction


    def load_functions(self) -> Dict[str, MyFunction]:
        myfunctions = {}

        for name in os.listdir(self.data_path):
            filepath = os.path.join(self.data_path, name)

            if not os.path.isfile(filepath):
                continue
            try:
                myfunction = self.load(filepath)
                myfunctions[name] = myfunction

                def func(rate: float=1, **kwargs) -> Dict[str, str]:
                    return self.play(name, rate, **kwargs)

                setattr(self, name, func)

            except:
                print('WARNING: could not load "{}"'.format(filepath))

        return myfunctions


    def list(self):
        myfunctions = self.load_functions()

        for name, myfunction in myfunctions.items():
            print('- {}:'.format(name))
            print('\tInputs:  {}'.format(myfunction.input_variables))
            print('\tOutputs: {}'.format(myfunction.output_variables))
            print('')


    def delete(self, function_name: str):
        filename = os.path.join(self.data_path, function_name)
        if not os.path.isfile(filename):
            raise FileNotFoundError('Function "{}" does not exist'.format(function_name))
        confirm = input('Confirm delete "{}" (y/n): '.format(function_name))
        if confirm not in ['n', 'N']:
            os.unlink(filename)
        else:
            print('Canceled delete')


    def read_variable_name(self, kind: str='Variable name', suppress: bool=True) -> str:
        print('{} (ESC to cancel): '.format(kind), end='', flush=True)

        chars: List[str] = []

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

        def on_release(key):
            if key == keyboard.Key.esc:
                chars.clear()
                print('')
                return False

        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
                suppress=suppress
            ) as listener:
            listener.join()

        return ''.join(chars)


    def record(self, function_name: str):
        filename = os.path.join(self.data_path, function_name)
        if os.path.isfile(filename):
            raise FileExistsError('Function "{}" already exists'.format(function_name))

        input_hotkey_str = '<ESC>+I'
        output_hotkey_str ='<ESC>+O'

        print('Starting recording ...')
        print('Press {} to put clipboard content into output variable'.format(output_hotkey_str))
        print('Press {} to put input variable into clipboard'.format(input_hotkey_str))
        print('Press <ESC> to stop')

        myevents: List[MyInputEvent] = []
        input_variables: List[str] = []
        output_variables: List[str] = []

        stop_event = threading.Event()
        input_event = threading.Event()
        output_event = threading.Event()
        time_delta: float = 0

        def on_input():
            input_event.set()
            stop_event.set()

        def on_output():
            output_event.set()
            stop_event.set()

        input_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(input_hotkey_str),
            on_input)

        output_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(output_hotkey_str),
            on_output)

        def on_press(key):
            input_hotkey.press(listener.canonical(key))
            output_hotkey.press(listener.canonical(key))

            myevent = MyInputEvent(KeyPressEvent(key), time_delta=time_delta)
            myevents.append(myevent)

        def on_release(key):
            if key == keyboard.Key.esc:
                stop_event.set()
                return False

            input_hotkey.release(listener.canonical(key))
            output_hotkey.release(listener.canonical(key))

            myevent = MyInputEvent(KeyReleaseEvent(key), time_delta=time_delta)
            myevents.append(myevent)

        last_move_myevent = None
        def on_mouse_event(event):
            nonlocal last_move_myevent

            if isinstance(event, mouse.Events.Move):
                myevent = MyInputEvent(MoveEvent(x=event.x, y=event.y), time_delta=time_delta)

                if last_move_myevent:
                    if myevent.timestamp - last_move_myevent.timestamp < 0.1:
                        return # no need to keep all move events

                last_move_myevent = myevent

            elif isinstance(event, mouse.Events.Click):
                myevent = MyInputEvent(ClickEvent(x=event.x, y=event.y, button=event.button, pressed=event.pressed), time_delta=time_delta)

            elif isinstance(event, mouse.Events.Scroll):
                myevent = MyInputEvent(ScrollEvent(x=event.x, y=event.y, dx=event.dx, dy=event.dy), time_delta=time_delta)

            else:
                raise RuntimeError('Unrecognized mouse event: {}'.format(event))

            myevents.append(myevent)

        while True:
            stop_event.clear()

            listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            listener.start()

            with mouse.Events() as events:
                while True:
                    if stop_event.is_set():
                        listener.stop()
                        break
                    event = events.get(0.5)
                    if event is None:
                        continue
                    on_mouse_event(event)

            if input_event.is_set():
                input_event.clear()

                t0 = time.time()
                name = self.read_variable_name(kind='Input variable name')
                if not name:
                    continue

                example_value = self.read_variable_name(kind='Input example value')
                if example_value:
                    pyperclip.copy(example_value)

                deadtime = time.time() - t0
                time_delta += deadtime

                if name in input_variables:
                    print('WARNING: input variable "{}" already exists'.format(name))
                else:
                    input_variables.append(name)
                    myevent = MyInputEvent(PasteFromVarEvent(name), time_delta=time_delta)
                    myevents.append(myevent)

            elif output_event.is_set():
                output_event.clear()

                t0 = time.time()
                name = self.read_variable_name(kind='Output variable name')
                if not name:
                    continue
                deadtime = time.time() - t0
                time_delta += deadtime

                if name in output_variables:
                    print('WARNING: output variable "{}" already exists'.format(name))
                else:
                    output_variables.append(name)
                    myevent = MyInputEvent(CopyToVarEvent(name), time_delta=time_delta)
                    myevents.append(myevent)
            else:
                break

        if myevents:
            myfunction = MyFunction(events=myevents, input_variables=input_variables, output_variables=output_variables)
            self.save(myfunction, filename)
        else:
            print('WARNING: no input events detected!')


    def play(self, function_name: str, rate: float=1, **kwargs) -> Dict[str, str]:
        output: Dict[str, str] = {}

        filename = os.path.join(self.data_path, function_name)
        if not os.path.isfile(filename):
            raise FileNotFoundError('Function "{}" does not exist'.format(function_name))

        myfunction = self.load(filename)

        for input_var in myfunction.input_variables:
            if input_var not in kwargs:
                raise ValueError('Input variable "{}" required as argument'.format(input_var))

        for input_var in kwargs:
            if input_var not in myfunction.input_variables:
                print('WARNING: Input variable "{}" not used'.format(input_var))

        myevents = myfunction.events

        key_controller = keyboard.Controller()
        mouse_controller = mouse.Controller()

        print('Starting play ...')

        start_time = time.time()
        recording_start_time = myevents[0].timestamp
        delta_reference = start_time - recording_start_time + 0.01

        for myevent in myevents:
            event = myevent.event
            timestamp = myevent.timestamp

            now = start_time + (time.time() - start_time) * rate
            delta = now - timestamp

            if delta < delta_reference:
                time.sleep(delta_reference - delta)
            else:
                print('WARNING: Event "{}" lags the desired playback rate'.format(type(event)))

            if isinstance(event, KeyPressEvent):
                key_controller.press(event.key)

            elif isinstance(event, KeyReleaseEvent):
                key_controller.release(event.key)

            elif isinstance(event, MoveEvent):
                mouse_controller.position = (event.x, event.y)
                pass

            elif isinstance(event, ClickEvent):
                mouse_controller.position = (event.x, event.y) # ensure pointer is in correct place
                if event.pressed:
                    mouse_controller.press(event.button)
                else:
                    mouse_controller.release(event.button)

            elif isinstance(event, ScrollEvent):
                mouse_controller.position = (event.x, event.y) # ensure pointer is in correct place
                mouse_controller.scroll(event.dx, event.dy)

            elif isinstance(event, CopyToVarEvent):
                clipboard_value = pyperclip.paste()
                output[event] = clipboard_value # event is just a str subclass

            elif isinstance(event, PasteFromVarEvent):
                input_value = kwargs.get(event, None) # event is just a str subclass
                if input_value:
                    pyperclip.copy(str(input_value))
                else:
                    raise ValueError('Input argument "{}" not found'.format(event))

            else:
                raise RuntimeError('Unrecognized event: {}'.format(event))

        return output



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Function Manager CLI')
    parser.add_argument('--path', default='~/.pyrobodesk/functions', help='path to store function data')
    parser.add_argument('-r', '--record', help='name of function to record')
    parser.add_argument('-p', '--play', help='name of function to play')
    parser.add_argument('--rate', type=float, default=1, help='playback rate (1 = original)')
    parser.add_argument('-l', '--list', action='store_true', help='list available functions')
    parser.add_argument('--delete', help='name of function to delete')
    parser.add_argument('-i', '--inputs', help='input arguments for play function in the form of name1=value1,name2=value2,...,nameN=valueN')
    args = parser.parse_args()

    manager = FunctionManager(args.path)

    try:
        if args.record:
            manager.record(function_name=args.record)

        if args.play:
            inputs = {}
            if args.inputs:
                try:
                    nameval_pair_list = args.inputs.split(',')
                    for nameval in nameval_pair_list:
                        [name, val] = nameval.split('=')
                        inputs[name] = val
                except ValueError:
                    raise ValueError('Inputs must be in the form of: name1=value1,name2=value2,...,nameN=valueN')

            output = manager.play(function_name=args.play, rate=args.rate, **inputs)
            print(output)

        elif args.list:
            manager.list()

        elif args.delete:
            manager.delete(args.delete)

    except KeyboardInterrupt:
        print('\nCanceled')

    #manager.test()
    #name = manager.read_variable_name()
    #print('Read "{}"'.format(name))
