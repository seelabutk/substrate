#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import subprocess
import sys
from urllib.parse import urlparse
import json
import copy

import yaml

from .targets import AWSStack, DockerSwarm
from .tools import (
	HelloWorld,
	NetCDFSlicer,
	OSPRayStudio,
	Tapestry,
	Braid,
	GenericTool
)

TOOLS = {
	'hello-world': HelloWorld,
	'nc_slicer': NetCDFSlicer,
	'ospray-studio': OSPRayStudio,
	'tapestry': Tapestry,
	'braid': Braid
}


def deep_merge(obj_a, obj_b):
	new_obj = copy.deepcopy(obj_a)
	for key, val in obj_b.items():
		if (
			key in new_obj and isinstance(new_obj[key], dict) and isinstance(val, dict)
		):
			new_obj[key] = deep_merge(new_obj[key], val)
		else:
			new_obj[key] = val
	return new_obj


def parse_yaml(path):
	config_name = 'substrate.config.yaml'

	if path is None:
		path = os.getcwd()

		files = os.listdir(path)
		if config_name not in files:
			raise FileNotFoundError(config_name)

		path = os.path.join(path, config_name)

	with open(path, 'r', encoding='utf8') as stream:
		_config = yaml.load(stream, Loader=yaml.Loader)

	return (path, _config)


class Substrate():
	def __init__(self, tool_name, config, path=None):
		pathconfig = {}
		if path:
			path, pathconfig = parse_yaml(path)

		self.tool_name = tool_name
		self.config = deep_merge(pathconfig, config)
		self.path = path
		self._check_config()

		self.target = None
		if self.config.get('aws', None) is not None:
			self.target = AWSStack
		elif self.config.get('docker', None) is not None:
			self.target = DockerSwarm

		self.data_sources = self._get_data(self.config)
		if tool_name not in TOOLS:
			# look in config for tool
			if tool_name not in self.config:
				raise Exception(f'No tool named {tool_name}')

			self.tool = GenericTool(tool_name, self.config, self.data_sources)
		else:
			self.tool = TOOLS[tool_name](self.config, self.data_sources)

		self.target_obj = self.target(self.path, self.config, self.tool)

	def _check_config(self):
		config = self.config

		if 'aws' not in config and 'docker' not in config:
			raise Exception(
				'No deployment target was chosen. Please choose either "aws" or "docker".'
			)

		if 'aws' in config and 'docker' in config:
			raise Exception(
				'The "aws" and "docker" options cannot be used simultaneously.'
			)

		if 'aws' in config:
			if not os.environ.get('AWS_ACCESS_KEY_ID', False):
				raise Exception(
					'AWS_ACCESS_KEY_ID environment variable must be set to deploy to AWS.'
				)

			if not os.environ.get('AWS_SECRET_ACCESS_KEY', False):
				raise Exception(
					'AWS_SECRET_ACCESS_KEY environment variable must be set to deploy to AWS.'
				)

			if 'service_command' not in config['aws']:
				raise Exception(
					'Option "aws.service_command" must be set to deploy to AWS.'
				)

		if 'docker' in config:
			try:
				subprocess.check_call(
					'docker info',
					shell=True,
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL
				)
			except subprocess.CalledProcessError as exc:
				raise Exception(
					"Docker doesn't appear to be running. Please check that it's installed "
					"and the daemon is running."
				) from exc

	def _get_data(self, config):
		source_paths = config.get('data', {}).get('source', [])
		data_paths = []
		data_urls = []

		for source_path in source_paths:
			is_url = urlparse(source_path).scheme.startswith(('ftp', 'http', 's3'))

			if is_url and self.target == DockerSwarm:
				raise Exception(
					'You cannot use remote data sources with a local deployment. Please '
					'download the dataset and reference it locally in data.source.'
				)

			if is_url:
				data_urls.append(source_path)
			else:
				data_paths.append(os.path.abspath(source_path))

			if data_paths and os.path.isfile(data_paths[-1]):
				data_paths[-1] = os.path.dirname(data_paths[-1])

		return (data_paths, data_urls)

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
	parser.add_argument(
		'-c',
		'--config',
		dest='input_config',
		default='{}',
		type=str,
		nargs='?',
		const=1
	)
	parser.add_argument('-f', '--config-file', dest='path')
	args = parser.parse_args()

	if args.action not in ['start', 'stop', 'synth']:
		sys.exit('Invalid action specified.')

	tool = args.tool
	path = args.path
	config = json.loads(args.input_config)

	if (not bool(config)) and (path is None):
		sys.exit('no config file specified')

	substrate = Substrate(tool, config, path)
	if args.action == 'start':
		print(f'You may view your new visualization stack here: {substrate.start()}.')  # noqa: E501

	if args.action == 'stop':
		substrate.stop()
