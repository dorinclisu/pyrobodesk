import time


from pynput import mouse, keyboard



def on_move(x, y):
    print('Move at {0}'.format((x, y)))

def on_click(x, y, button, pressed):
    print('Click at {0} with {1} ({2})'.format((x, y), button, pressed))

def on_scroll(x, y, dx, dy):
    print('Scroll at {0} with {1}'.format((x, y), (dx, dy)))


mlistener = mouse.Listener(
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


mcontroller = mouse.Controller()

print('scrolling...')
mcontroller.scroll(0, 4)
time.sleep(0.1)
mcontroller.scroll(0, -4)
time.sleep(0.1)
mcontroller.scroll(0, 4)


with mouse.Events() as events:
    for event in events:
        print('Received event {}'.format(event))

        if isinstance(event, mouse.Events.Click):
            if event.button == mouse.Button.right:
                break

# The event listener will be running in this block
# with keyboard.Events() as events:
#     for event in events:
#         print('Received event {}'.format(event))

#         if event.key == keyboard.Key.esc:
#             break
