import os

import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_efs as efs
import aws_cdk.aws_iam as iam
from aws_cdk.core import RemovalPolicy, Stack


class SubstrateStack(Stack):  # pylint: disable=too-many-instance-attributes
	def __init__(self, scope, _id, tool, config, data_urls, **kwargs):
		self.tool = tool
		self.config = config
		self.data_urls = data_urls
		self.leader_name = ''

		self.tool.upload_to_s3()

		super().__init__(scope, _id, **kwargs)

		self.vpc = ec2.Vpc(
			self,
			_id,
			max_azs=1,
			nat_gateways=0,
			subnet_configuration=[
				ec2.SubnetConfiguration(name='public', subnet_type=ec2.SubnetType.PUBLIC)
			]
		)

		ami_string = self.config['aws'].get('ami', None)
		if ami_string:
			self.ami = ec2.MachineImage.generic_linux({
				self.config['aws'].get('region', 'us-east-1'): 'ami-048ff3da02834afdc'
			})
		else:
			self.ami = ec2.MachineImage.latest_amazon_linux()

		role_arn = self.config['aws'].get('role_arn', None)
		if role_arn:
			self.role = iam.Role.from_role_arn(self, 'john', role_arn, mutable=False)
		else:
			self.role = None

		scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
		udata_file = os.path.join(scripts_dir, 'node.sh')
		with open(udata_file, 'r', encoding='utf-8') as commands:
			self.global_commands = commands.read()

		file_system = self.provision_fs()
		self.provision_ec2(file_system)

	def get_udata(self, _type):
		udata = ec2.UserData.for_linux()
		# TODO: Is there a better way to give access to each node to use AWS CLI?
		udata.add_commands(
			f'export AWS_DEFAULT_REGION={self.config["aws"].get("region", "us-east-1")}'
		)
		udata.add_commands(
			f'export AWS_ACCESS_KEY_ID={os.environ.get("AWS_ACCESS_KEY_ID")}'
		)
		udata.add_commands(
			f'export AWS_SECRET_ACCESS_KEY={os.environ.get("AWS_SECRET_ACCESS_KEY")}'
		)
		udata.add_commands(
			f'export AWS_SESSION_TOKEN={os.environ.get("AWS_SESSION_TOKEN", "")}'
		)
		udata.add_commands(self.global_commands)

		if _type == 'leader':
			udata.add_commands(
				f'aws s3 sync s3://{self.config["aws"]["bucket"]} /mnt/efs'
			)
			udata.add_commands('cd /data')
			for data_url in self.data_urls:
				udata.add_commands(f'curl -O {data_url}')
			udata.add_commands('cd -')
			udata.add_commands('mkdir /mnt/efs/swarm')
			udata.add_commands('docker swarm init')
			udata.add_commands(
				'docker swarm join-token worker | grep "docker" > /mnt/efs/swarm/worker'
			)
			udata.add_commands(
				'docker swarm join-token manager | grep "docker" > /mnt/efs/swarm/manager'
			)
			udata.add_commands(self.tool.service_command)
		elif _type == 'manager':
			udata.add_commands('until [ -f /mnt/efs/swarm/manager ]; do sleep 1; done')
			udata.add_commands('$(cat /mnt/efs/swarm/manager)')
		elif _type == 'worker':
			udata.add_commands('until [ -f /mnt/efs/swarm/worker ]; do sleep 1; done')
			udata.add_commands('$(cat /mnt/efs/swarm/worker)')

		return udata

	def provision_ec2(self, file_system):
		managers = self.config['aws'].get('managers', {})
		workers = self.config['aws'].get('workers', {})

		nodes = []
		for index, _type in enumerate(managers):
			count = managers.get(_type, 1)
			for index2 in range(count):
				if index == 0 and index2 == 0:
					instance_name = 'substrate-leader'
					udata = self.get_udata('leader')
				else:
					instance_name = f'substrate-manager-{_type}-{index}'
					udata = self.get_udata('manager')

				nodes.append(ec2.Instance(
					self,
					instance_name,
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=self.ami,
					role=self.role,
					user_data=udata,
					vpc=self.vpc,
					vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
				))

		for _type in workers:
			udata = self.get_udata('worker')

			count = workers.get(_type, 1)
			for index in range(count):
				nodes.append(ec2.Instance(
					self,
					f'substrate-worker-{_type}-{index}',
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=self.ami,
					role=self.role,
					user_data=udata,
					vpc=self.vpc,
					vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
				))

		for node in nodes:
			node.node.add_dependency(file_system.mount_targets_available)

			if self.role:
				node.instance.iam_instance_profile = None
				node.node.try_remove_child('InstanceProfile')

			# TODO: fix
			node.connections.allow_from_any_ipv4(
				ec2.Port.all_traffic(),
				'General Purpose'
			)

	def provision_fs(self):
		efs_sg = ec2.SecurityGroup(self, 'substrate-efs-sg', vpc=self.vpc)
		efs_sg.add_ingress_rule(
			peer=ec2.Peer.any_ipv4(),  # TODO: fix
			connection=ec2.Port.tcp(2049)
		)

		return efs.FileSystem(
			self,
			'substrate-efs',
			removal_policy=RemovalPolicy.DESTROY,
			security_group=efs_sg,
			vpc=self.vpc
		)
