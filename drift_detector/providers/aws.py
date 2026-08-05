from __future__ import annotations

from importlib import import_module, util
from typing import Any

from drift_detector.models.resource import ResourceModel
from drift_detector.providers.base import CloudProvider


class AWSProvider(CloudProvider):
    """AWS provider adapter that fetches live AWS resources for Terraform state entries."""

    name = "aws"
    supported_resource_types = {
        "aws_instance",
        "aws_security_group",
        "aws_s3_bucket",
        "aws_iam_role",
        "aws_lambda_function",
    }

    def __init__(self, profile: str | None = None, regions: list[str] | None = None, session: Any | None = None) -> None:
        self.profile = profile
        self.regions = regions or []
        self.session = session or self._build_session()

    def fetch_resources(self, expected_resources: list[ResourceModel]) -> list[ResourceModel]:
        resources: list[ResourceModel] = []
        expected_by_type = self._group_expected(expected_resources)
        regions = self.regions or self._regions_from_expected(expected_resources) or [self.session.region_name or "us-east-1"]

        if "aws_instance" in expected_by_type:
            for region in regions:
                resources.extend(self._fetch_instances(region))
        if "aws_security_group" in expected_by_type:
            for region in regions:
                resources.extend(self._fetch_security_groups(region))
        if "aws_s3_bucket" in expected_by_type:
            resources.extend(self._fetch_s3_buckets())
        if "aws_iam_role" in expected_by_type:
            resources.extend(self._fetch_iam_roles())
        if "aws_lambda_function" in expected_by_type:
            for region in regions:
                resources.extend(self._fetch_lambda_functions(region))
        return resources

    def _build_session(self) -> Any:
        if util.find_spec("boto3") is None:
            raise RuntimeError("Live AWS scans require boto3. Install it with: pip install -e '.[aws]' or pip install boto3")
        boto3 = import_module("boto3")
        return boto3.Session(profile_name=self.profile) if self.profile else boto3.Session()

    @staticmethod
    def _group_expected(expected_resources: list[ResourceModel]) -> dict[str, list[ResourceModel]]:
        grouped: dict[str, list[ResourceModel]] = {}
        for resource in expected_resources:
            grouped.setdefault(resource.type, []).append(resource)
        return grouped

    @staticmethod
    def _regions_from_expected(expected_resources: list[ResourceModel]) -> list[str]:
        regions = []
        for resource in expected_resources:
            if resource.region:
                # Terraform often stores availability zones for EC2 instances; trim trailing AZ letter.
                region = resource.region[:-1] if resource.region[-1:].isalpha() and resource.region[-2:-1].isdigit() else resource.region
                if region not in regions:
                    regions.append(region)
        return regions

    @staticmethod
    def _tags_from_aws(tag_list: list[dict[str, str]] | None) -> dict[str, str]:
        return {tag["Key"]: tag["Value"] for tag in tag_list or [] if "Key" in tag and "Value" in tag}

    def _client(self, service: str, region: str | None = None) -> Any:
        return self.session.client(service, region_name=region) if region else self.session.client(service)

    def _fetch_instances(self, region: str) -> list[ResourceModel]:
        client = self._client("ec2", region)
        paginator = client.get_paginator("describe_instances")
        resources: list[ResourceModel] = []
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]
                    resources.append(ResourceModel(provider="aws", type="aws_instance", id=instance_id, name=self._tags_from_aws(instance.get("Tags")).get("Name"), region=region, attributes={"id": instance_id, "instance_type": instance.get("InstanceType"), "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"), "state": instance.get("State", {}).get("Name"), "private_ip": instance.get("PrivateIpAddress"), "public_ip": instance.get("PublicIpAddress")}, tags=self._tags_from_aws(instance.get("Tags")), raw=instance))
        return resources

    def _fetch_security_groups(self, region: str) -> list[ResourceModel]:
        client = self._client("ec2", region)
        paginator = client.get_paginator("describe_security_groups")
        resources: list[ResourceModel] = []
        for page in paginator.paginate():
            for group in page.get("SecurityGroups", []):
                group_id = group["GroupId"]
                resources.append(ResourceModel(provider="aws", type="aws_security_group", id=group_id, name=group.get("GroupName"), region=region, attributes={"id": group_id, "name": group.get("GroupName"), "description": group.get("Description"), "vpc_id": group.get("VpcId")}, tags=self._tags_from_aws(group.get("Tags")), raw=group))
        return resources

    def _fetch_s3_buckets(self) -> list[ResourceModel]:
        client = self._client("s3")
        resources: list[ResourceModel] = []
        for bucket in client.list_buckets().get("Buckets", []):
            name = bucket["Name"]
            tags = self._fetch_s3_bucket_tags(client, name)
            resources.append(ResourceModel(provider="aws", type="aws_s3_bucket", id=name, name=name, attributes={"id": name, "bucket": name}, tags=tags, raw=bucket))
        return resources

    def _fetch_s3_bucket_tags(self, client: Any, bucket_name: str) -> dict[str, str]:
        try:
            return self._tags_from_aws(client.get_bucket_tagging(Bucket=bucket_name).get("TagSet"))
        except Exception as exc:
            if self._aws_error_code(exc) == "NoSuchTagSet":
                return {}
            raise

    @staticmethod
    def _aws_error_code(exc: Exception) -> str | None:
        response = getattr(exc, "response", None)
        if not isinstance(response, dict):
            return None
        error = response.get("Error", {})
        return error.get("Code")

    def _fetch_iam_roles(self) -> list[ResourceModel]:
        client = self._client("iam")
        paginator = client.get_paginator("list_roles")
        resources: list[ResourceModel] = []
        for page in paginator.paginate():
            for role in page.get("Roles", []):
                role_name = role["RoleName"]
                tag_page = client.list_role_tags(RoleName=role_name)
                tags = {tag["Key"]: tag["Value"] for tag in tag_page.get("Tags", [])}
                resources.append(ResourceModel(provider="aws", type="aws_iam_role", id=role_name, name=role_name, attributes={"id": role_name, "name": role_name, "arn": role.get("Arn"), "path": role.get("Path")}, tags=tags, raw=role))
        return resources

    def _fetch_lambda_functions(self, region: str) -> list[ResourceModel]:
        client = self._client("lambda", region)
        paginator = client.get_paginator("list_functions")
        resources: list[ResourceModel] = []
        for page in paginator.paginate():
            for function in page.get("Functions", []):
                arn = function["FunctionArn"]
                tags = client.list_tags(Resource=arn).get("Tags", {})
                name = function["FunctionName"]
                resources.append(ResourceModel(provider="aws", type="aws_lambda_function", id=name, name=name, region=region, attributes={"id": name, "function_name": name, "runtime": function.get("Runtime"), "handler": function.get("Handler"), "role": function.get("Role"), "memory_size": function.get("MemorySize"), "timeout": function.get("Timeout")}, tags=tags, raw=function))
        return resources
