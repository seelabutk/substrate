import os

from docker.types.services import EndpointSpec, ServiceMode


class VCI():
	def __init__(self, docker, config, args):
		self.docker = docker
		self.config = config

		self.service = None

		# TODO: provide a default "good" directory if none is set
		self.vci_path = args.vci_dir
		self.data_path = None

		self.vci_pattern = ''

		self.get_data()

	def get_data(self):
		source_path = self.config['data']['source']

		# TODO: use a downloadable dataset
		self.data_path = os.path.abspath(source_path)

		# TODO: get this from self.data_path or self.vci_path
		self.vci_pattern = 'UGRD-1yr-720x361-fcst0-*of*_*of*_*of*_*of*.dat'

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
				replicas=self.config['cluster'].get('replicas', 0)
			),
			mounts=[
				f'{self.data_path}:/data:ro',
				f'{self.vci_path}:/opt/run:ro',
				'/etc/hosts:/etc/hosts:ro'
			],
			name='VCI',
			workdir='/opt/run'
		)

	def stop(self):
		self.service.remove()
