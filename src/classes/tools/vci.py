import subprocess

from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class VCI(Tool):
	def __init__(self, config, data_path):
		super().__init__(config, data_path)

		self.name = 'vci'
		self.config = config

		self.vci_pattern = self.config['vci']['file_pattern']

		self.service_command = (
			'docker service create '
			f'--env VCI_PATTERN={self.vci_pattern} '
			'--env VCI_ROOT=/data '
			'--name tapestry '
			'--publish 80:8840/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'--mount type=bind,src=/mnt/efs/app,dst=/opt/run '
			'-w /opt/run'
			'evilkermit/substrate_vci:latest '
			'python3.7 -u -m vci'
		)

		self.vci_path = self.config['vci']['directory']
		self.data_path = data_path

	def start(self):
		docker = from_env()

		port = self.config['cluster'].get('port', 8080)
		docker.services.create(
			'evilkermit/substrate_vci:latest',
			'python3.7',
			args=['-u', '-m', 'vci'],
			endpoint_spec=EndpointSpec(ports={port: (8840, 'tcp')}),
			env=[
				f'VCI_PATTERN={self.vci_pattern}',
				'VCI_ROOT=/data'
			],
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 1)
			),
			mounts=[
				f'{self.data_path}:/data:ro',
				f'{self.vci_path}:/opt/run:ro'
			],
			name='VCI',
			networks=['substrate-vci-net'],
			workdir='/opt/run'
		)

	def upload_to_s3(self):
		subprocess.run([
			'aws',
			's3',
			'sync',
			self.vci_path,
			f's3://{self.config["aws"]["bucket"]}/app'
		], check=True)

		subprocess.run([
			'aws',
			's3',
			'sync',
			self.data_path,
			f's3://{self.config["aws"]["bucket"]}/data'
		], check=True)
