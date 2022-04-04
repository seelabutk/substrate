from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class OSPRayStudio(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'ospray-studio'
		self.port = 8000

		self.config = config
		self.data_sources = data_sources

		self.service_command = (
			'docker service create '
			'--name ospray_studio '
			'--publish 80:5000/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'evilkermit/substrate_ospray_studio:latest '
			'flask run --host=0.0.0.0'
		)

	def start(self):
		mounts = super().start()

		docker = from_env()

		self.port = self.config['cluster'].get('port', self.port)
		docker.services.create(
			'evilkermit/substrate_ospray_studio:latest',
			'flask',
			args=['run', '--host=0.0.0.0'],
			endpoint_spec=EndpointSpec(ports={self.port: (5000, 'tcp')}),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 1)
			),
			mounts=mounts,
			name='ospray_studio',
			networks=['substrate-ospray-studio-net']
		)
