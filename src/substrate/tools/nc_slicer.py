from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class NetCDFSlicer(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'nc-slicer'
		self.port = 8000

		self.config = config
		self.data_sources = data_sources

		self.service_command = (
			'docker service create '
			'--name dchm '
			'--publish 80:5000/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'npatel79/water-and-land:latest '
			'flask run --host=0.0.0.0'
		)

	def start(self):
		mounts = super().start()

		docker = from_env()

		self.port = self.config['cluster'].get('port', self.port)
		docker.services.create(
			'npatel79/water-and-land:latest',
			'flask',
			args=['run', '--host=0.0.0.0'],
			endpoint_spec=EndpointSpec(ports={self.port: (5000, 'tcp')}),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 1)
			),
			mounts=mounts,
			name='nc_slicer',
			networks=['substrate-nc-slicer-net']
		)
