import signal

from substrate import Substrate


# note the dash here, this will be found in substrate.config.yml
s = Substrate('nc-slicer')
location = s.start()

print(f'You may view your visualization at {location}.')


def stop(*args):  # pylint: disable=unused-argument
	s.stop()


signal.signal(signal.SIGINT, stop)
signal.pause()
