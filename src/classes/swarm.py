import os
from pathlib import Path
from urllib.request import urlretrieve
from urllib.parse import urlparse

from docker import from_env
import paramiko

from .tools import Tapestry, VCI


MODULES = {
	'tapestry': Tapestry,
	'vci': VCI
}


class SubstrateSwarm():
	def __init__(self, tool_name, config):
		self.tool_name = tool_name
		if self.tool_name not in MODULES:
			raise Exception(f'No tool named {self.tool_name}')
		self.config = config

		self.docker = from_env()
		self.network = None

		data_path = self.get_data()

		self.tool = MODULES[self.tool_name](self.docker, self.config, data_path)

		ssh_dir = os.path.join(Path.home(), '.ssh')
		ssh_dirfiles = os.listdir(ssh_dir)
		ssh_keys = [keyfile for keyfile in ssh_dirfiles if keyfile.startswith('id_')]
		ssh_pkeys = [keyfile for keyfile in ssh_keys if not keyfile.endswith('.pub')]
		self.key_paths = [os.path.join(ssh_dir, keyfile) for keyfile in ssh_pkeys]

	def create_swarm(self):
		advertise_addr = self.config['cluster'].get('advertise_addr', None)
		if advertise_addr:
			self.docker.swarm.init(advertise_addr=advertise_addr)
		else:
			self.docker.swarm.init()

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

		self.tool.start()

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

	def get_data(self):
		source_path = self.config['data']['source']

		# Download the dataset if necessary to the target location
		if urlparse(source_path).scheme != '':
			target_path = os.path.abspath(self.config['data']['target'])

			os.makedirs(os.path.dirname(target_path), exist_ok=True)
			urlretrieve(source_path, target_path)

			data_path = target_path
		else:
			data_path = os.path.abspath(source_path)

		if os.path.isfile(data_path):
			data_path = os.path.dirname(data_path)

		return data_path

	# TODO: use more sophisticated logging setup
	def log(self, message):
		print(message, end='')

	def start(self):
		self.create_swarm()

	def stop(self):
		self.destroy_swarm()
