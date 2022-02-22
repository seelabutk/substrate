from docker.types.services import EndpointSpec, ServiceMode


class VCI():
	def __init__(self, docker, config, data_path):
		self.docker = docker
		self.config = config

		self.service = None

		self.vci_path = self.config['vci']['directory']
		self.data_path = data_path

		self.vci_pattern = self.config['vci']['file_pattern']

	def start(self):
		port = self.config['cluster'].get('port', 8080)
		self.service = self.docker.services.create(
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

	def stop(self):
		self.service.remove()
