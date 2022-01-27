#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import yaml


class VCI():
	def __init__(self, tool, path=None):
		self.tool = tool
		self.config_name = 'vci.config.yaml'
		self.config = self.parse_yaml(path)

		print(self.config)

	def parse_yaml(self, path):
		if path is None:
			path = os.getcwd()

			files = os.listdir(path)
			while self.config_name not in files:
				path = os.path.abspath(os.path.join(path, '..'))
				files = os.listdir(path)

				if path == '/':
					break

			if self.config_name not in files:
				raise FileNotFoundError(self.config_name)

			path = os.path.join(path, self.config_name)

		with open(path, 'r', encoding='utf8') as stream:
			return yaml.load(stream, Loader=yaml.Loader)

	def start(self):
		print(f'Starting {self.tool}')

	def stop(self):
		print(f'Stopping {self.tool}')


if __name__ == '__main__':
	parser = ArgumentParser(description='Launches a VCI instance')

	parser.add_argument(
		'tool',
		help='The visualization tool to run (choices: tapestry, tannerlol).',
		metavar='TOOL'
	)
	parser.add_argument('-c', '--config', dest='path')
	args = parser.parse_args()

	vci = VCI(args.tool, path=args.path)
	vci.start()
	vci.stop()
