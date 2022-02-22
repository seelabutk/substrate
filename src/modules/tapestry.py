from glob import glob
import json
import os
from urllib.request import urlretrieve
from urllib.parse import urlparse

from docker.types.services import EndpointSpec, ServiceMode


class Tapestry():
	def __init__(self, docker, config, args):
		self.docker = docker
		self.config = config

		self.service = None

		# TODO: provide a default "good" directory if none is set
		self.tapestry_path = args.tapestry_dir
		self.app_path = os.path.join(self.tapestry_path, 'app')
		self.config_path = os.path.join(self.tapestry_path, 'config')
		self.data_path = None

		self.get_data()
		self.set_config()

	def get_data(self):
		source_path = self.config['data']['source']

		# Download the dataset if necessary to the target location
		if urlparse(source_path).scheme != '':
			target_path = os.path.abspath(self.config['data']['target'])

			os.makedirs(os.path.dirname(target_path), exist_ok=True)
			urlretrieve(source_path, target_path)

			self.data_path = target_path
		else:
			self.data_path = os.path.abspath(source_path)

	def set_config(self):
		config_file = glob(os.path.join(self.config_path, '*.json'))[0]
		with open(config_file, 'r', encoding='utf8') as _file:
			tapestry_config = json.load(_file)

			# Set dataset-specific Tapestry configuration
			tapestry_config['filename'] = f'/data/{os.path.split(self.data_path)[1]}'
			tapestry_config['dimensions'] = self.config['data']['dimensions']
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
				replicas=self.config['cluster'].get('replicas', 0)
			),
			mounts=[
				f'{self.app_path}:/app:ro',
				f'{self.config_path}:/config:ro',
				f'{os.path.dirname(self.data_path)}:/data:ro'
			],
			name='tapestry'
		)

	def stop(self):
		self.service.remove()
