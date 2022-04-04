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
from .tools import OSPRayStudio, Tapestry, VCI

MODULES = {
	'ospray_studio': OSPRayStudio,
	'tapestry': Tapestry,
	'vci': VCI
}


class Substrate():
	def __init__(self, tool_name, path=None):
		self.tool_name = tool_name
		self.path, self.config = self._parse_yaml(path)

		self.is_aws = self.config.get('aws', None) is not None
		self.is_local = self.config.get('cluster', None) is not None

		self.data_sources = self._get_data(self.config)

		if tool_name not in MODULES:
			raise Exception(f'No tool named {tool_name}')
		self.tool = MODULES[tool_name](self.config, self.data_sources)

		if self.is_aws:
			app = App()
			SubstrateStack(
				app,
				'substrate-stack',
				self.tool,
				self.config,
				self.data_sources[1]
			)
			app.synth()

	def _get_data(self, config):
		source_paths = config['data']['source']
		data_paths = []
		data_urls = []

		for source_path in source_paths:
			is_url = urlparse(source_path).scheme.startswith(('ftp', 'http'))

			# Download the dataset if necessary to the target location
			if is_url and self.is_local:
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

		# TODO: add as much error checking as I have time for
		if _config.get('cluster', None) and _config.get('aws', None):
			sys.exit('The "cluster" and "aws" options cannot be used simultaneously.')

		return (path, _config)

	def start(self):
		location = None

		if self.is_aws:
			subprocess.run([
				'npx',
				'cdk',
				'deploy',
				'--require-approval',
				'never',
				'--app',
				f'"substrate {self.tool_name} -c {self.path} synth"'
			], check=True)

			location = subprocess.check_output([
				'aws',
				'ec2',
				'describe-instances',
				'--filters',
				'Name=instance-state-name,Values=running',
				'Name=tag:Name,Values=substrate-stack/substrate-leader',
				'--query',
				'Reservations[*].Instances[*].[PublicIpAddress]',
				'--output',
				'text'
			]).strip().decode('utf-8')

		if self.is_local:
			swarm = SubstrateSwarm(self.tool, self.config)
			location = swarm.start()

		return f'https://{location}'

	def stop(self):
		if self.is_aws:
			subprocess.run([
				'npx',
				'cdk',
				'destroy',
				'--force',
				'--app',
				f'"substrate {self.tool_name} -c {self.path} synth"'
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
		help='The visualization tool to run [ospray_studio, tapestry, vci]',
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
		print(
			f'You may view your new visualization stack here: {substrate.start()}.'
		)
	if args.action == 'stop':
		substrate.stop()
