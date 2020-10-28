import time


import pynput



def on_move(x, y):
    print('Move at {0}'.format((x, y)))

def on_click(x, y, button, pressed):
    print('Click at {0} with {1} ({2})'.format((x, y), button, pressed))

def on_scroll(x, y, dx, dy):
    print('Scroll at {0} with {1}'.format((x, y), (dx, dy)))


mlistener = pynput.mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll
)


mlistener.start()
try:
    time.sleep(10)
except KeyboardInterrupt:
    pass
finally:
    mlistener.stop()


mcontroller = pynput.mouse.Controller()

print('scrolling...')
mcontroller.scroll(0, 4)
time.sleep(0.1)
mcontroller.scroll(0, -4)
time.sleep(0.1)
mcontroller.scroll(0, 4)
