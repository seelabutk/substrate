#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import yaml


CONFIG_FNAME = 'vci.config.yaml'


def parse_yaml(path):
	if path is None:
		path = os.getcwd()

		files = os.listdir(path)
		while CONFIG_FNAME not in files:
			path = os.path.abspath(os.path.join(path, '..'))
			files = os.listdir(path)

			if path == '/':
				break

		if CONFIG_FNAME not in files:
			raise FileNotFoundError(CONFIG_FNAME)

		path = os.path.join(path, CONFIG_FNAME)

	with open(path, 'r', encoding='utf8') as stream:
		return yaml.load(stream, Loader=yaml.Loader)


if __name__ == '__main__':
	parser = ArgumentParser(description='Launches a VCI instance')

	parser.add_argument(
		'tool',
		help='The visualization tool to run (choices: tapestry, tannerlol).',
		metavar='TOOL'
	)
	parser.add_argument('-c', '--config', dest='path')
	args = parser.parse_args()

	config = parse_yaml(args.path)

	print(f'Loading {args.tool}')
	print(f'Config {config}')
