#!/usr/bin/env python3
from argparse import ArgumentParser
import os
from pathlib import Path
import signal

from docker import from_env
import paramiko
import yaml

from modules import Tapestry


MODULES = {
	'tapestry': Tapestry
}


class VCI():
	def __init__(self, tool_name, path=None):
		self.docker = from_env()

		self.config_name = 'vci.config.yaml'
		self.config = self.parse_yaml(path)

		self.tool_name = tool_name
		if self.tool_name not in MODULES:
			raise Exception(f'No tool named {self.tool_name}')
		self.tool = MODULES[self.tool_name](self.docker, self.config)

		ssh_dir = os.path.join(Path.home(), '.ssh')
		ssh_dirfiles = os.listdir(ssh_dir)
		ssh_keys = [keyfile for keyfile in ssh_dirfiles if keyfile.startswith('id_')]
		ssh_pkeys = [keyfile for keyfile in ssh_keys if not keyfile.endswith('.pub')]
		self.key_paths = [os.path.join(ssh_dir, keyfile) for keyfile in ssh_pkeys]

	def create_swarm(self):
		advertise_addr = self.config['cluster']['advertise_addr']
		self.docker.swarm.init(advertise_addr=advertise_addr)

		manager_token = self.docker.swarm.attrs['JoinTokens']['Manager']
		worker_token = self.docker.swarm.attrs['JoinTokens']['Worker']

		nodes = []
		for node in self.config['cluster']['managers']:
			nodes.append(('manager', node))
		for node in self.config['cluster']['workers']:
			nodes.append(('worker', node))

		for node_type, node in nodes:
			username, location = node.split('@')
			if node_type == 'manager':
				token = manager_token
			elif node_type == 'worker':
				token = worker_token

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
					self.log(f'remote error ({location}): {stderr}')

		# TODO: support AWS

	def destroy_swarm(self):
		for node in self.config['cluster']['managers']:
			username, location = node.split('@')

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
					self.log(f'remote error ({location}): {stderr}')

		self.docker.swarm.leave(force=True)

	# TODO: use more sophisticated logging setup
	def log(self, message):
		print(message)

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
		self.log('Initialized Swarm.')
		self.tool.start()
		self.log(f'Started {self.tool_name.capitalize()}. Press Ctrl+C to exit.')

	def stop(self):
		self.tool.stop()
		self.log(f'Stopped {self.tool_name.capitalize()}.')
		self.destroy_swarm()
		self.log('Destroyed Swarm.')


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
	signal.sigwait([signal.SIGINT])
	# TODO: consider scaling the swarm as needed here
	# scale_interval = vci.config['cluster']['scale_interval']
	# while signal.sigtimedwait([signal.SIGINT], scale_interval) is None:
	# 	vci.scale()
	vci.stop()
