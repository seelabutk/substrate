class Tool():
	def __init__(self, config, data_path):  # pylint: disable=unused-argument
		# Define the Docker CLI command to create this service on AWS.
		self.service_command = ''

	# Start a local Docker swarm service
	def start(self):
		pass

	# Stop the service created by Tool.start().
	def stop(self):
		pass

	# Upload files needed to run your service to S3.
	# Upload them to mirror the directory structure you want on EFS.
	def upload_to_s3(self):
		pass
