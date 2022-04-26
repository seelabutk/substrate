import signal

from substrate import Substrate


s = Substrate('ospray_studio')
location = s.start()

print(f'You may view your visualization at {location}.')


def stop(*args):  # pylint: disable=unused-argument
	s.stop()


signal.signal(signal.SIGINT, stop)
signal.pause()
