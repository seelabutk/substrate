#!/usr/bin/env python3
from argparse import ArgumentParser
import os
from pathlib import Path
import signal

from docker import from_env
import paramiko
import yaml

from modules import Tapestry, VCI


MODULES = {
	'tapestry': Tapestry,
	'vci': VCI
}


class Substrate():
	def __init__(self, cli_args, path=None):
		self.docker = from_env()
		self.network = None

		self.config_name = 'substrate.config.yaml'
		self.config = self.parse_yaml(path)

		self.tool_name = cli_args.tool
		if self.tool_name not in MODULES:
			raise Exception(f'No tool named {self.tool_name}')
		self.tool = MODULES[self.tool_name](self.docker, self.config, cli_args)

		ssh_dir = os.path.join(Path.home(), '.ssh')
		ssh_dirfiles = os.listdir(ssh_dir)
		ssh_keys = [keyfile for keyfile in ssh_dirfiles if keyfile.startswith('id_')]
		ssh_pkeys = [keyfile for keyfile in ssh_keys if not keyfile.endswith('.pub')]
		self.key_paths = [os.path.join(ssh_dir, keyfile) for keyfile in ssh_pkeys]

	def create_swarm(self):
		advertise_addr = self.config['cluster'].get('advertise_addr', '0.0.0.0')
		self.docker.swarm.init(advertise_addr=advertise_addr)

		self.network = self.docker.networks.create(
			f'substrate-{self.tool_name}-net',
			driver='overlay'
		)

		manager_token = self.docker.swarm.attrs['JoinTokens']['Manager']
		worker_token = self.docker.swarm.attrs['JoinTokens']['Worker']

		nodes = []
		for node in self.config['cluster'].get('managers', []):
			nodes.append(('manager', node))
		for node in self.config['cluster'].get('workers', []):
			nodes.append(('worker', node))

		for node_type, node in nodes:
			username, location = node.split('@')
			if node_type == 'manager':
				token = manager_token
			elif node_type == 'worker':
				token = worker_token

			self.log(f'Adding remote {node} to swarm as {node_type}…')

			with paramiko.client.SSHClient() as ssh_client:
				ssh_client.load_system_host_keys()
				ssh_client.connect(
					location,
					username=username,
					key_filename=self.key_paths
				)

				_, _, stderr = ssh_client.exec_command(
					f'docker swarm join --token {token} {advertise_addr}'
				)
				stderr = stderr.read()
				if stderr:
					self.log(f'✕\nremote error ({location}): {stderr}\n')
				else:
					self.log('✓\n')

		# TODO: support AWS

	def destroy_swarm(self):
		nodes = []
		for node in self.config['cluster'].get('managers', []):
			nodes.append(node)
		for node in self.config['cluster'].get('workers', []):
			nodes.append(node)

		for node in nodes:
			username, location = node.split('@')

			self.log(f'Removing remote {node} from swarm…')

			with paramiko.client.SSHClient() as ssh_client:
				ssh_client = paramiko.client.SSHClient()
				ssh_client.load_system_host_keys()
				ssh_client.connect(
					location,
					username=username,
					key_filename=self.key_paths
				)

				_, _, stderr = ssh_client.exec_command('docker swarm leave --force')
				stderr = stderr.read()
				if stderr:
					self.log(f'✕\nremote error ({location}): {stderr}\n')
				else:
					self.log('✓\n')

		self.docker.swarm.leave(force=True)

	# TODO: use more sophisticated logging setup
	def log(self, message):
		print(message, end='')

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
		self.create_swarm()
		self.log('Initialized Swarm.\n')
		self.tool.start()
		self.log(f'Started {self.tool_name}. Press Ctrl+C to exit.\n')

	def stop(self):
		self.tool.stop()
		self.log(f'Stopped {self.tool_name}.\n')
		self.destroy_swarm()
		self.log('Destroyed Swarm.\n')


if __name__ == '__main__':
	parser = ArgumentParser(description='Launches a Substrate instance')

	parser.add_argument(
		'tool',
		help='The visualization tool to run (choices: tapestry, vci).',
		metavar='TOOL'
	)
	parser.add_argument('-c', '--config', dest='path')
	parser.add_argument('--tapestry_dir')
	parser.add_argument('--vci_dir')
	args = parser.parse_args()

	substrate = Substrate(args, path=args.path)

	substrate.start()
	signal.sigwait([signal.SIGINT])
	substrate.stop()
