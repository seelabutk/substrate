from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class DCHM(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'DCHM'
		self.port = 8000
		self.data_sources = data_sources
		self.config = config

	def start(self):
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
			name='DCHM',
		)
