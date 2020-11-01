import os
import shutil
import threading
import time

import pytest
from pynput import keyboard, mouse

import pyrobodesk.manager as pm



data_path = 'tests/data'

def test_path():
    shutil.rmtree(data_path, ignore_errors=True)

    manager = pm.FunctionManager(data_path)

    assert os.path.isdir(data_path)


def test_serialization():
    manager = pm.FunctionManager(data_path)
    function = pm.MyFunction([pm.MyInputEvent(pm.KeyPressEvent)])

    manager.save(function, os.path.join(data_path, 'dummy'))
    function2 = manager.load(os.path.join(data_path, 'dummy'))

    assert function.input_variables == function2.input_variables
    assert function.output_variables == function2.output_variables


def test_read_name1():
    manager = pm.FunctionManager(data_path)
    controller = keyboard.Controller()

    name = 'name_1'

    def typing_thread():
        time.sleep(0.1)
        controller.type(name)
        controller.tap(keyboard.Key.enter)

    threading.Thread(target=typing_thread).start()

    assert name == manager.read_variable_name()


def test_read_name2():
    manager = pm.FunctionManager(data_path)
    controller = keyboard.Controller()

    name = 'name_2'

    def typing_thread():
        time.sleep(0.1)
        controller.type(name)
        controller.tap(keyboard.Key.esc)

    threading.Thread(target=typing_thread).start()

    assert '' == manager.read_variable_name()


#def test_record_play():
