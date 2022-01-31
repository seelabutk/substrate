from pathlib import Path
import os
import pickle

from docker.types.services import EndpointSpec


class Tapestry():
	def __init__(self, docker, config):
		self.docker = docker
		self.config = config

		self.file_path = os.path.join(Path.home(), '.vci', 'tapestry.vci')
		os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

	def start(self):
		service = self.docker.services.create(
			'seelabutk/tapestry',
			endpoint_spec=EndpointSpec(ports={80: (9010, 'tcp')}),
			env=['APP_DIR=/app'],
			mounts=[
				'/home/john/utk/tapestry/examples/app:/app:ro',
				'/home/john/utk/tapestry/examples/configs:/config:ro',
				'/home/john/utk/tapestry/examples/data:/data:ro'
			],
			name='tapestry'
		)

		with open(self.file_path, 'wb') as state_file:
			pickle.dump(
				{
					'id': service.id
				},
				state_file
			)

	def stop(self):
		with open(self.file_path, 'rb') as state_file:
			service_obj = pickle.load(state_file)
			service = self.docker.services.get(service_obj['id'])
			service.remove()

		os.remove(self.file_path)
