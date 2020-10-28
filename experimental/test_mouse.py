import time


from external.mouse import mouse



print('Press Right Click to stop ...')
mouse.hook(print)
mouse.wait(button=mouse.RIGHT, target_types=(mouse.UP,))
mouse.unhook(print)

# mouse.play(mouse.record())
