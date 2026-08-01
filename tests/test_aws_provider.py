from drift_detector.models.resource import ResourceModel
from drift_detector.providers.aws import AWSProvider


class FakePaginator:
    def __init__(self, pages):
        self.pages = pages

    def paginate(self):
        return self.pages


class FakeEC2Client:
    def get_paginator(self, operation):
        assert operation == "describe_instances"
        return FakePaginator([
            {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-1234567890",
                                "InstanceType": "t3.small",
                                "Placement": {"AvailabilityZone": "us-east-1a"},
                                "State": {"Name": "running"},
                                "PrivateIpAddress": "10.0.0.10",
                                "Tags": [
                                    {"Key": "Name", "Value": "web"},
                                    {"Key": "Environment", "Value": "stage"},
                                ],
                            }
                        ]
                    }
                ]
            }
        ])


class FakeSession:
    region_name = "us-east-1"

    def client(self, service, region_name=None):
        assert service == "ec2"
        assert region_name == "us-east-1"
        return FakeEC2Client()


def test_fetches_live_ec2_instances_from_session():
    provider = AWSProvider(regions=["us-east-1"], session=FakeSession())
    expected = [ResourceModel(provider="aws", type="aws_instance", id="i-1234567890")]

    resources = provider.fetch_resources(expected)

    assert len(resources) == 1
    assert resources[0].identity == "aws:aws_instance:i-1234567890"
    assert resources[0].attributes["instance_type"] == "t3.small"
    assert resources[0].tags["Environment"] == "stage"


class FakeNoSuchTagSetError(Exception):
    response = {"Error": {"Code": "NoSuchTagSet", "Message": "The TagSet does not exist"}}


class FakeS3ClientWithoutTags:
    def list_buckets(self):
        return {"Buckets": [{"Name": "untagged-bucket"}]}

    def get_bucket_tagging(self, Bucket):
        assert Bucket == "untagged-bucket"
        raise FakeNoSuchTagSetError()


class FakeS3Session:
    region_name = "us-east-1"

    def client(self, service, region_name=None):
        assert service == "s3"
        assert region_name is None
        return FakeS3ClientWithoutTags()


def test_fetches_s3_bucket_without_tags_when_aws_returns_no_such_tag_set():
    provider = AWSProvider(session=FakeS3Session())
    expected = [ResourceModel(provider="aws", type="aws_s3_bucket", id="untagged-bucket")]

    resources = provider.fetch_resources(expected)

    assert len(resources) == 1
    assert resources[0].identity == "aws:aws_s3_bucket:untagged-bucket"
    assert resources[0].tags == {}
