#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import subprocess
import sys

from aws_cdk import App
import yaml

from classes import SubstrateStack, SubstrateSwarm


class Substrate():
	def __init__(self, _args):
		path, config = self.parse_yaml(_args.path)

		if config.get('aws', None):
			file_path = os.path.realpath(__file__)
			os.chdir(os.path.dirname(file_path))

			if _args.action == 'synth':
				app = App()
				SubstrateStack(app, 'substrate-stack', config=config)
				app.synth()
			if _args.action == 'start':
				subprocess.run([
					'npx',
					'cdk',
					'deploy',
					'--app',
					f'"python {file_path} {_args.tool} synth -c {path}"'
				], check=True)
			if _args.action == 'stop':
				subprocess.run([
					'npx',
					'cdk',
					'destroy',
					'--app',
					f'"python {file_path} {_args.tool} synth -c {path}"'
				], check=True)

		elif config.get('cluster', None):
			substrate = SubstrateSwarm(_args.tool, config)

			if _args.action == 'start':
				substrate.start()
			if _args.action == 'stop':
				substrate.stop()

	def parse_yaml(self, path):
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


if __name__ == '__main__':
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

	Substrate(args)
