from glob import glob
import json
import os

from docker.types.services import EndpointSpec, ServiceMode


class Tapestry():
	def __init__(self, docker, config, data_path):
		self.docker = docker
		self.config = config

		self.service = None

		self.tapestry_path = self.config['tapestry']['directory']
		self.app_path = os.path.join(self.tapestry_path, 'app')
		self.config_path = os.path.join(self.tapestry_path, 'config')
		self.data_path = data_path

		self.set_config()

	def set_config(self):
		config_file = glob(os.path.join(self.config_path, '*.json'))[0]
		with open(config_file, 'r', encoding='utf8') as _file:
			tapestry_config = json.load(_file)

			data_file = os.listdir(self.data_path)[0]
			filename = os.path.split(data_file)[1]

			# Set dataset-specific Tapestry configuration
			tapestry_config['filename'] = filename
			tapestry_config['dimensions'] = self.config['tapestry']['dimensions']
			tapestry_config['cameraPosition'] = [
				0,
				0,
				tapestry_config['dimensions'][-1] * 2
			]

		# Save the config so it can be changed by the user
		with open(config_file, 'w', encoding='utf8') as _file:
			json.dump(tapestry_config, _file)

	def start(self):
		port = self.config['cluster'].get('port', 8080)
		self.service = self.docker.services.create(
			'evilkermit/substrate_tapestry:latest',
			endpoint_spec=EndpointSpec(ports={port: (9010, 'tcp')}),
			env=['APP_DIR=/app'],
			mode=ServiceMode(
				mode='replicated',
				replicas=self.config['cluster'].get('replicas', 1)
			),
			mounts=[
				f'{self.app_path}:/app:ro',
				f'{self.config_path}:/config:ro',
				f'{self.data_path}:/data:ro'
			],
			name='tapestry',
			networks=['substrate-tapestry-net']
		)

	def stop(self):
		self.service.remove()
