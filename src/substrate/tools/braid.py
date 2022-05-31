import os
import subprocess

from docker import from_env
from docker.types import Mount
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class Braid(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'braid'
		self.config = config
		self.port = 8000

		self.braid_pattern = self.config['braid']['file_pattern']

		self.service_command = (
			'docker service create '
			f'--env VCI_PATTERN={self.braid_pattern} '
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

		fallback_dir = os.path.join(os.path.dirname(__file__), 'braid')

		self.braid_path = self.config['braid'].get('directory', fallback_dir)
		self.data_sources = data_sources

	def start(self):
		mounts = super().start()

		docker = from_env()

		mounts.append(
			Mount('/opt/run', self.braid_path, type='bind', read_only=True)
		)

		self.port = self.config['docker'].get('port', self.port)
		docker.services.create(
			'evilkermit/substrate_vci:latest',
			'python3.7',
			args=['-u', '-m', 'vci'],
			endpoint_spec=EndpointSpec(ports={self.port: (8840, 'tcp')}),
			env=[
				f'VCI_PATTERN={self.braid_pattern}',
				'VCI_ROOT=/data'
			],
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['docker'].get('replicas', 1)
			),
			mounts=mounts,
			name='braid',
			networks=['substrate-braid-net'],
			workdir='/opt/run'
		)

	def upload_to_s3(self):
		super().upload_to_s3()

		subprocess.run(
			f'aws s3 sync {self.braid_path} s3://{self.config["aws"]["bucket"]}/app',
			check=True,
			shell=True
		)
