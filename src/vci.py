#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import yaml

from modules import Tapestry


MODULES = {
	'tapestry': Tapestry
}


class VCI():
	def __init__(self, tool_name, path=None):
		self.config_name = 'vci.config.yaml'
		self.config = self.parse_yaml(path)

		self.tool_name = tool_name
		if self.tool_name not in MODULES:
			raise Exception(f'No tool named {self.tool_name}')
		self.tool = MODULES[self.tool_name](self.config)

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
		self.tool.start()

	def stop(self):
		self.tool.stop()


if __name__ == '__main__':
	parser = ArgumentParser(description='Launches a VCI instance')

	parser.add_argument(
		'tool',
		help='The visualization tool to run (choices: tapestry).',
		metavar='TOOL'
	)
	parser.add_argument('-c', '--config', dest='path')
	args = parser.parse_args()

	vci = VCI(args.tool, path=args.path)
	vci.start()
	vci.stop()
