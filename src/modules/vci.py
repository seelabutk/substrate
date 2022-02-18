from docker.types.services import EndpointSpec, ServiceMode


class VCI():
	def __init__(self, docker, config, _):
		self.docker = docker
		self.config = config

		self.service = None

	def get_data(self):
		pass

	def start(self):
		# TODO: make this conform to the following docker run command
		# docker run -p 8988:8840 -it -v /home/jduggan1/vci:/opt/run -v /mnt/seenas2/data/climate/gen3:/data -w /opt/run --env VCI_ROOT=/data --env VCI_PATTERN=UGRD-1yr-720x361-fcst0-*of*_*of*_*of*_*of*.dat evilkermit/substrate_vci python3.7 -u -m vci
		port = self.config['cluster'].get('port', 8080)
		self.service = self.docker.services.create(
			'evilkermit/substrate_vci',
			endpoint_spec=EndpointSpec(ports={port: (8840, 'tcp')}),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 0)
			),
			mounts=['/mnt/seenas2/data/climate/gen3:/data:ro'],
			name='VCI'
		)

	def stop(self):
		self.service.remove()
