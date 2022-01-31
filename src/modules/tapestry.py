import json
import os
from pathlib import Path
from urllib.request import urlretrieve
from urllib.parse import urlparse

from docker.types.services import EndpointSpec


class Tapestry():
	def __init__(self, docker, config):
		self.docker = docker
		self.config = config

		self.service = None

		self.state_path = os.path.join(Path.home(), '.vci')
		self.config_path = None
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
		self.config_path = os.path.join(
			self.state_path,
			'tapestry',
			'config',
			'data.json'
		)

		if os.path.isfile(self.config_path):
			with open(self.config_path, 'r', encoding='utf8') as _file:
				tapestry_config = json.load(_file)
		else:
			# Use sane defaults if no config is set
			tapestry_config = {
				'backgroundColor': [38, 36, 54, 0],
				'colorMap': 'reverseSpectral',
				'imageSize': [1024, 1024],
				'opacityAttenuation': 0.5,
				'outputImageFilename': 'temp.png',
				'samplesPerPixel': 4
			}

		# Set dataset-specific Tapestry configuration
		tapestry_config['filename'] = f'/data/{os.path.split(self.data_path)[1]}'
		tapestry_config['dimensions'] = self.config['data']['dimensions']
		tapestry_config['cameraPosition'] = [
			0,
			0,
			tapestry_config['dimensions'][-1] * 2
		]

		# Save the config so it can be changed by the user
		os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
		with open(self.config_path, 'w', encoding='utf8') as _file:
			json.dump(tapestry_config, _file)

	def start(self):
		# TODO: use replicas
		port = self.config['cluster']['port']
		self.service = self.docker.services.create(
			'seelabutk/tapestry',
			endpoint_spec=EndpointSpec(ports={port: (9010, 'tcp')}),
			mounts=[
				f'{os.path.dirname(self.config_path)}:/config:ro',
				f'{os.path.dirname(self.data_path)}:/data:ro'
			],
			name='tapestry'
		)

	def stop(self):
		self.service.remove()
