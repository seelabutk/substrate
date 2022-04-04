import os
import subprocess

from docker import from_env
from docker.types import Mount
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class VCI(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'vci'
		self.config = config
		self.port = 8000

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

		fallback_dir = os.path.join(os.path.dirname(__file__), 'vci')

		self.vci_path = self.config['vci'].get('directory', fallback_dir)
		self.data_sources = data_sources

	def start(self):
		mounts = super().start()

		docker = from_env()

		mounts.append(Mount('/opt/run', self.vci_path, type='bind', read_only=True))

		self.port = self.config['cluster'].get('port', self.port)
		docker.services.create(
			'evilkermit/substrate_vci:latest',
			'python3.7',
			args=['-u', '-m', 'vci'],
			endpoint_spec=EndpointSpec(ports={self.port: (8840, 'tcp')}),
			env=[
				f'VCI_PATTERN={self.vci_pattern}',
				'VCI_ROOT=/data'
			],
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 1)
			),
			mounts=mounts,
			name='VCI',
			networks=['substrate-vci-net'],
			workdir='/opt/run'
		)

	def upload_to_s3(self):
		super().upload_to_s3()

		subprocess.run([
			'aws',
			's3',
			'sync',
			self.vci_path,
			f's3://{self.config["aws"]["bucket"]}/app'
		], check=True)
