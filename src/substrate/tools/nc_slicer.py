from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class NetCDFSlicer(Tool):
	def __init__(self, config, data_sources):
		super().__init__(config, data_sources)

		self.name = 'nc_slicer'
		self.port = 8000

		self.config = config
		self.data_sources = data_sources

		self.service_command = (
			'docker service create '
			'--name dchm '
			'--publish 80:5000/tcp '
			f'--replicas {self.config.get("aws", {}).get("replicas", 1)} '
			'--mount type=bind,src=/mnt/efs/data,dst=/data '
			'jhammer3/substrate:nc_slicer'
			'python app.py'
		)

	def start(self):
		mounts = super().start()
		docker = from_env()

		docker.services.create(
			'jhammer3/substrate:nc_slicer',
			endpoint_spec=EndpointSpec(ports={self.port: (5000, 'tcp')}),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['docker'].get('replicas', 1)
			),
			mounts=mounts,
			name='nc_slicer',
			networks=[f'substrate-{self.name}-net'],
			init=True
		)

	# TODO: 
	# fix nc-slicer -> nc_slicer and init=True in main substrate repo
	# set up dockerhub org and move images to it
	# impliment water-and-land changes to nc_slicer image 

