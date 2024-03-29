from docker import from_env
from docker.types.services import EndpointSpec, ServiceMode

from . import Tool


class GenericTool(Tool):  # pylint: disable=too-many-instance-attributes
	def __init__(self, name, config, data_sources):
		super().__init__(config, data_sources)
		# Provide a name for this tool
		self.name = name

		self.config = config
		self.tool_config = config[name]
		self.data_sources = data_sources

		# Get the command to start the service from the config
		self.service_command = self.tool_config.get('service_command', '')
		self.port = 8000
		self.internal_port = self.tool_config.get('internal_port', None)
		self.image = self.tool_config.get('image', None)
		if self.internal_port is None:
			raise Exception('Option "internal_port" must be defined.')

	# Start a local Docker swarm service
	def start(self):
		# ensure image is defined
		if self.image is None:
			raise Exception(
				'Option "docker.image" must be defined when running substrate generic '
				'tool locally.'
			)

		mounts = super().start()
		docker = from_env()

		network_name = self.config['docker'].get(
			'network',
			f'substrate-{self.name}-net'
		)

		self.port = self.config['docker'].get('port', self.port)
		environment_variables = self.config['docker'].get('env', [])
		arguments = self.config.get('args', [])
		docker.services.create(
			self.image,
			endpoint_spec=EndpointSpec(
				ports={self.port: (self.internal_port, 'tcp', 'host')}
			),
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['docker'].get('replicas', 1)
			),
			args=arguments,
			env=environment_variables,
			mounts=mounts,
			name=self.name,
			networks=[network_name],
			init=True
		)
