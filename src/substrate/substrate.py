#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import subprocess
import sys
from urllib.request import urlretrieve
from urllib.parse import urlparse

from aws_cdk.core import App
import yaml

from .classes import SubstrateStack, SubstrateSwarm
from .classes.tools import Tapestry, VCI

MODULES = {
	'tapestry': Tapestry,
	'vci': VCI
}


class Substrate():
	def __init__(self, tool_name, path=None):
		self.tool_name = tool_name
		self.path, self.config = self._parse_yaml(path)

		data_path = self._get_data(self.config)

		if tool_name not in MODULES:
			raise Exception(f'No tool named {tool_name}')
		self.tool = MODULES[tool_name](self.config, data_path)

		self.is_aws = self.config.get('aws', None) is not None
		self.is_local = self.config.get('cluster', None) is not None

		if self.is_aws:
			app = App()
			SubstrateStack(app, 'substrate-stack', self.tool, self.config)
			app.synth()

	def _get_data(self, config):
		source_path = config['data']['source']

		# Download the dataset if necessary to the target location
		if urlparse(source_path).scheme != '':
			target_path = os.path.abspath(config['data']['target'])

			os.makedirs(os.path.dirname(target_path), exist_ok=True)
			urlretrieve(source_path, target_path)

			data_path = target_path
		else:
			data_path = os.path.abspath(source_path)

		if os.path.isfile(data_path):
			data_path = os.path.dirname(data_path)

		return data_path

	def _parse_yaml(self, path):
		config_name = 'substrate.config.yaml'

		if path is None:
			path = os.getcwd()

			files = os.listdir(path)
			while config_name not in files:
				path = os.path.abspath(os.path.join(path, '..'))
				files = os.listdir(path)

				if path == '/':
					break

			if config_name not in files:
				raise FileNotFoundError(config_name)

			path = os.path.join(path, config_name)

		with open(path, 'r', encoding='utf8') as stream:
			_config = yaml.load(stream, Loader=yaml.Loader)

		# TODO: add as much error checking as I have time for
		if _config.get('cluster', None) and _config.get('aws', None):
			sys.exit('The "cluster" and "aws" options cannot be used simultaneously.')

		return (path, _config)

	def start(self):
		if self.is_aws:
			file_path = os.path.realpath(__file__)

			subprocess.run([
				'npx',
				'cdk',
				'deploy',
				'--app',
				f'"python {file_path} {self.tool_name} synth -c {self.path}"'
			], check=True)
		elif self.is_local:
			swarm = SubstrateSwarm(self.tool, self.config)
			swarm.start()

	def stop(self):
		if self.is_aws:
			file_path = os.path.realpath(__file__)

			subprocess.run([
				'npx',
				'cdk',
				'destroy',
				'--app',
				f'"python {file_path} {self.tool_name} synth -c {self.path}"'
			], check=True)
			subprocess.run([
				'aws',
				's3',
				'rm',
				f's3://{self.config["aws"]["bucket"]}',
				'--recursive'
			], check=True)
		elif self.is_local:
			swarm = SubstrateSwarm(self.tool, self.config)
			swarm.stop()


def main():
	parser = ArgumentParser(description='Launches a Substrate instance')

	parser.add_argument(
		'tool',
		help='The visualization tool to run (choices: tapestry, vci).',
		metavar='TOOL'
	)
	parser.add_argument(
		'action',
		help='choices: start, stop)',
		metavar='ACTION'
	)
	parser.add_argument('-c', '--config', dest='path')
	args = parser.parse_args()

	if args.action not in ['start', 'stop', 'synth']:
		sys.exit('Invalid action specified.')

	substrate = Substrate(args.tool, args.path)
	if args.action == 'start':
		substrate.start()
	if args.action == 'stop':
		substrate.stop()
