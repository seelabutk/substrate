import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
from aws_cdk.core import Stack


class SubstrateStack(Stack):
	def __init__(self, scope, _id, **kwargs):  # pylint-disable: too-many-locals
		self.config = kwargs.pop('config').get('aws')

		super().__init__(scope, _id, **kwargs)

		self.vpc = ec2.Vpc(
			self,
			_id,
			nat_gateways=0,
			subnet_configuration=[
				ec2.SubnetConfiguration(name='public', subnet_type=ec2.SubnetType.PUBLIC),
				ec2.SubnetConfiguration(
					name='isolated',
					subnet_type=ec2.SubnetType.ISOLATED
				)
			]
		)

		ami_string = self.config.get('ami', None)
		if ami_string:
			self.ami = ec2.MachineImage.generic_linux({
				self.config.get('region', 'us-east-1'): 'ami-048ff3da02834afdc'
			})
		else:
			self.ami = ec2.MachineImage.latest_amazon_linux()

		role_arn = self.config.get('role_arn', None)
		if role_arn:
			self.role = iam.Role.from_role_arn(self, 'john', role_arn, mutable=False)
		else:
			self.role = None

		self.provision_ec2()
		self.provision_efs()

	def provision_ec2(self):
		managers = self.config.get('managers', {})
		workers = self.config.get('workers', {})

		self.nodes = []
		for _type in managers:
			count = managers.get(_type, 0)
			for index in range(count):
				self.nodes.append(ec2.Instance(
					self,
					f'substrate-manager-{_type}-{index}',
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=self.ami,
					role=self.role,
					vpc=self.vpc,
					vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
				))

		for _type in workers:
			count = workers.get(_type, 0)
			for index in range(count):
				self.nodes.append(ec2.Instance(
					self,
					f'substrate-worker-{_type}-{index}',
					instance_type=ec2.InstanceType(instance_type_identifier=_type),
					machine_image=self.ami,
					role=self.role,
					vpc=self.vpc,
					vpc_subnets=ec2.SubnetSelection(
						subnet_type=ec2.SubnetType.ISOLATED
					)
				))

		for node in self.nodes:
			if self.role:
				node.instance.iam_instance_profile = None
				node.node.try_remove_child('InstanceProfile')

			node.connections.allow_from_any_ipv4(
				ec2.Port.all_traffic(),
				'General Purpose'
			)

	def provision_efs(self):
		pass
