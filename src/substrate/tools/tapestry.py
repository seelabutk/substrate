import os
import subprocess

from docker import from_env
from docker.types import Mount
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class Tapestry(Tool):  # pylint: disable=too-many-instance-attributes
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'tapestry'
		self.config = config
		self.port = 8000

		self.service_command = (
			'docker service create '
			'--env APP_DIR=/app '
			'--name tapestry '
			'--publish 80:9010/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/app,dst=/app '
			'--mount type=bind,src=/mnt/efs/config,dst=/config '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'evilkermit/substrate_tapestry:latest '
			'./server /config 9010 /app'
		)

		fallback_dir = os.path.join(os.path.dirname(__file__), 'tapestry')

		self.tapestry_path = self.config['tapestry'].get('directory', [fallback_dir])[0]  # noqa: E501
		self.app_path = os.path.join(self.tapestry_path, 'app')
		self.config_path = os.path.join(self.tapestry_path, 'config')
		self.data_sources = data_sources

	def start(self):
		mounts = super().start()
		docker = from_env()

		mounts.append(Mount('/app', self.app_path, type='bind', read_only=True))
		mounts.append(
			Mount('/config', self.config_path, type='bind', read_only=True)
		)

		self.port = self.config['docker'].get('port', self.port)
		docker.services.create(
			'evilkermit/substrate_tapestry:latest',
			'./server',
			args=['/config', '9010', '/app'],
			endpoint_spec=EndpointSpec(ports={self.port: (9010, 'tcp')}),
			env=['APP_DIR=/app'],
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['docker'].get('replicas', 1)
			),
			mounts=mounts,
			name='tapestry',
			networks=[f'substrate-{self.name}-net']
		)

	def upload_to_s3(self):
		super().upload_to_s3()

		subprocess.run(
			f'aws s3 sync {self.app_path} s3://{self.config["aws"]["bucket"]}/app',
			check=True,
			shell=True
		)

		subprocess.run(
			f'aws s3 sync {self.config_path} s3://{self.config["aws"]["bucket"]}/config',  # noqa: E501
			check=True,
			shell=True
		)
