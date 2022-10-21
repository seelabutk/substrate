from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class HelloWorld(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'hello-world'
		self.port = 8000

		self.config = config
		self.data_sources = data_sources

		self.service_command = (
			'docker service create '
			'--name hello_world '
			'--publish 80:5000/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'seelab/substrate-hello-world:latest '
			'python3 -m http.server 5000'
		)

	def start(self):
		mounts = super().start()

		docker = from_env()

		self.port = self.config['docker'].get('port', self.port)
		docker.services.create(
			'seelab/substrate-hello-world:latest',
			'python3',
			args=['-m', 'http.server', '8000'],
			endpoint_spec=EndpointSpec(ports={self.port: (8000, 'tcp')}),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['docker'].get('replicas', 1)
			),
			mounts=mounts,
			name='hello-world',
			networks=[f'substrate-{self.name}-net']
		)
