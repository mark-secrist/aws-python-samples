import boto3
from botocore.config import Config

# Create a session with 'app-user' profile
session = boto3.Session(profile_name='app-user')

# From the session, get the s3 resource.
s3 = session.client('s3')

bucketName="mark-test-9702144567"
# create an s3 bucket using the variable bucketName
s3.create_bucket(Bucket=bucketName)

# Print a list of all the buckets in your account
response = s3.list_buckets()
for bucket in response['Buckets']:
    print(f'  {bucket["Name"]}')

# Delete bucket 'mark-test-9702144567'
s3.delete_bucket(Bucket=bucketName)

