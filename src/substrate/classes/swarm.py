import os
from pathlib import Path
import subprocess
import time

from docker import from_env
import paramiko


class SubstrateSwarm():
	def __init__(self, tool, config):
		self.tool = tool
		self.config = config

		self.docker = from_env()
		self.network = None

		ssh_dir = os.path.join(Path.home(), '.ssh')
		ssh_dirfiles = os.listdir(ssh_dir)
		ssh_keys = [keyfile for keyfile in ssh_dirfiles if keyfile.startswith('id_')]
		ssh_pkeys = [keyfile for keyfile in ssh_keys if not keyfile.endswith('.pub')]
		self.key_paths = [os.path.join(ssh_dir, keyfile) for keyfile in ssh_pkeys]

	def create_swarm(self):
		self.log('Initializing the swarm…')
		advertise_addr = self.config['cluster'].get('advertise_addr', None)
		if advertise_addr:
			self.docker.swarm.init(advertise_addr=advertise_addr)
		else:
			self.docker.swarm.init()
		self.log('✓\n')

		self.network = self.docker.networks.create(
			f'substrate-{self.tool.name}-net',
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

		self.log('Creating the swarm service…')
		self.tool.start()
		self.log('✓\n')

		self.log('Waiting for the service to be stable…')
		output = subprocess.check_output([
			'docker',
			'service',
			'ps',
			'ospray_studio',
			'--format',
			'"{{.CurrentState}}"'
		]).decode('utf-8').split('\n')
		invalid_outputs = [line for line in output if len(line) > 0 and not line.startswith('"Running')]  # noqa: E501
		while invalid_outputs:
			time.sleep(1)
			output = subprocess.check_output([
				'docker',
				'service',
				'ps',
				'ospray_studio',
				'--format',
				'"{{.CurrentState}}"'
			]).decode('utf-8').split('\n')
			invalid_outputs = [line for line in output if len(line) > 0 and not line.startswith('"Running')]  # noqa: E501
		self.log('✓\n')

		return f'127.0.0.1:{self.tool.port}'

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

		self.log('Destroying the swarm…')
		self.docker.swarm.leave(force=True)
		self.log('✓\n')

	def log(self, message):
		print(message, end='')

	def start(self):
		return self.create_swarm()

	def stop(self):
		self.destroy_swarm()
