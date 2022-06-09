#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import sys
from urllib.request import urlretrieve
from urllib.parse import urlparse

import yaml

from targets import AWSStack, DockerSwarm
from tools import HelloWorld, NetCDFSlicer, OSPRayStudio, Tapestry, Braid

TOOLS = {
	'hello_world': HelloWorld,
	'nc_slicer': NetCDFSlicer,
	'ospray_studio': OSPRayStudio,
	'tapestry': Tapestry,
	'braid': Braid
}


class Substrate():
	def __init__(self, tool_name, path=None):
		self.tool_name = tool_name
		self.path, self.config = self._parse_yaml(path)

		self.target = None
		if self.config.get('aws', None) is not None:
			self.target = AWSStack
		elif self.config.get('docker', None) is not None:
			self.target = DockerSwarm

		self.data_sources = self._get_data(self.config)
		if tool_name not in TOOLS:
			raise Exception(f'No tool named {tool_name}')
		self.tool = TOOLS[tool_name](self.config, self.data_sources)

		self.target_obj = self.target(self.path, self.config, self.tool)

	def _get_data(self, config):
		source_paths = config['data']['source']
		data_paths = []
		data_urls = []

		for source_path in source_paths:
			is_url = urlparse(source_path).scheme.startswith(('ftp', 'http'))

			# Download the dataset if necessary to the target location
			if is_url and self.target == DockerSwarm:
				target_path = os.path.abspath(config['data']['target'])

				os.makedirs(os.path.dirname(target_path), exist_ok=True)
				urlretrieve(source_path, target_path)

				if target_path not in data_paths:
					data_paths.append(target_path)
			elif is_url:
				data_urls.append(source_path)
			else:
				data_paths.append(os.path.abspath(source_path))

			if os.path.isfile(data_paths[-1]):
				data_paths[-1] = os.path.dirname(data_paths[-1])

		return (data_paths, data_urls)

	def _parse_yaml(self, path):
		config_name = 'substrate.config.yaml'

		if path is None:
			path = os.getcwd()

			files = os.listdir(path)
			if config_name not in files:
				raise FileNotFoundError(config_name)

			path = os.path.join(path, config_name)

		with open(path, 'r', encoding='utf8') as stream:
			_config = yaml.load(stream, Loader=yaml.Loader)

		if _config.get('docker', None) and _config.get('aws', None):
			sys.exit('The "docker" and "aws" options cannot be used simultaneously.')

		return (path, _config)

	def start(self):
		return f'http://{self.target_obj.start()}'

	def stop(self):
		self.target_obj.stop()


def main():
	parser = ArgumentParser(description='Launches a Substrate instance')

	parser.add_argument(
		'tool',
		help='The visualization tool to run [hello_world, nc_slicer, ospray_studio, tapestry, braid]',  # noqa: E501
		metavar='TOOL'
	)
	parser.add_argument(
		'action',
		help='[start, stop]',
		metavar='ACTION'
	)
	parser.add_argument('-c', '--config', dest='path')
	args = parser.parse_args()

	if args.action not in ['start', 'stop', 'synth']:
		sys.exit('Invalid action specified.')

	substrate = Substrate(args.tool, args.path)
	if args.action == 'start':
            print(f'You may view your new visualization stack here: {substrate.start()}.')
	if args.action == 'stop':
		substrate.stop()

if __name__ == "__main__": 
	main()
