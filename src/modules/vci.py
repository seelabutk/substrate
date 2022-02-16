from docker.types.services import EndpointSpec, ServiceMode


class VCI():
	def __init__(self, docker, config):
		self.docker = docker
		self.config = config

		self.service = None

	def get_data(self):
		pass

	def start(self):
		port = self.config['cluster'].get('port', 8080)
		self.service = self.docker.services.create(
			'evilkermit/substrate_vci',
			endpoint_spec=EndpointSpec(ports={port: (8840, 'tcp')}),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 0)
			),
			name='VCI'
		)

	def stop(self):
		self.service.remove()
