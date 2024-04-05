"""
Sample code to demonstrate how to perform common tasks on S3 using the Python library.
There are two types (or levels) of interfaces used here.
- The Client interface represents a lower level interface and will typically map more 1:1
  to the REST calls made under the covers to the AWS cloud resources
- The Resource interface is more object oriented and represents a higher-level interface
  Note: According to the documentation, the resource interface is no longer being maintained

Both are used in the code below, the purpose being:
1. To show how to use both
2. To simplify the code in some places

"""

import logging
import boto3
from botocore.exceptions import ClientError

def main():
   # Get a typical S3 Client, which will use the default profile and credentials
   # s3Client = boto3.client('s3')

   # Create a session with 'app-user' profile
   s3Session = boto3.Session(profile_name='app-user')
   # From the session, get the s3 resource.
   s3SessionClient = s3Session.client('s3')
   # Resource represents an object-oriented interface, which offers a higher-level
   # abstraction. This is used especially for the list bucket contents and delete bucket
   # operations.
   s3Resource = s3Session.resource('s3')

   # Assign a bucket name
   bucketName="mark-test-9702144567"

   # Verify the bucket doesn't already exist
   verifyBucketName(s3SessionClient, bucketName)

   createBucket(s3SessionClient, bucketName)

   listBuckets(s3SessionClient)

   # Upload a file
   metaData_key = "myVal2"
   metaData_value = "lab2-testing-upload"
   source_content_type = "text/csv"
   source_file_name="notes.csv"
   uploadFile(s3SessionClient,bucketName, source_file_name, source_file_name, source_content_type, {metaData_key: metaData_value})

   listBucketContents(s3Resource, bucketName)

   url=create_presigned_url(s3SessionClient, bucketName, source_file_name)
   print(f'Presigned url = {url}')

   # Delete the bucket, but first clear bucket contents
   deleteBucket(s3Resource, bucketName)

def createBucket(s3Client, bucket):
   """Create a bucket with the specified name

    :param s3Client: string
    :param bucket: string
    :return: none
    """
   # create an s3 bucket using the bucket name provided
   print("Creating bucket")
   s3Client.create_bucket(Bucket=bucket)

   # Wait for bucket to be created
   waiter = s3Client.get_waiter('bucket_exists')
   waiter.wait(Bucket=bucket) 

def deleteBucket(s3Resource, bucket):
   """Delete a bucket with the specified name using the Resource API

    :param s3Client: string
    :param bucket: string
    :return: none
    """
   print("Deleting bucket")
   clearBucketContents(s3Resource, bucket)
   my_bucket = s3Resource.Bucket(bucket)
   my_bucket.delete()


def verifyBucketName(s3Client, bucket):
    """Verify bucket doesn't exist before creating. This could likely be turned into
    a boolean function and made more general-purpose.

    :param s3Client: string
    :param bucket: string
    :return: none
    """
    try:
        # Attempt to get the bucket status - if bucket exists, should succeed
        s3Client.head_bucket(Bucket=bucket)

        # If the previous command is successful, the bucket is already in your account.
        raise SystemExit('This bucket has already been created in your account, exiting because there is nothing further to do!')
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
          ## If you receive a 404 error code, a bucket with that name
          ##  does not exist anywhere in AWS.
          print('Existing Bucket Not Found, ok to proceed')
        if error_code == 403:
          ## If you receive a 403 error code, a bucket exists with that
          ## in another AWS account.
          raise SystemExit('This bucket has already owned by another AWS Account, change the suffix and try a new name!')

def listBuckets(s3Client):
   """List buckets or account

    :param s3Client: string
    :return: none
    """
   # Print a list of all the buckets in your account
   response = s3Client.list_buckets()
   for bucket in response['Buckets']:
       print(f'  {bucket["Name"]}')

def listBucketContents(s3Resource, bucket):
   """List the contents of the specified bucket using the s3Resource, which is the
   Object oriented approach, offering a simpler implementation

    :param s3Resource: string
    :param bucket: string
    :return: none
    """
   my_bucket = s3Resource.Bucket(bucket)
   print(f'Contents of bucket {bucket} : ')

   for my_bucket_object in my_bucket.objects.all():
      print(f' - {my_bucket_object.key}')

def clearBucketContents(s3Resource, bucket):
   """Clear the contents of the specified bucket using the s3Resource, which is the
   Object oriented approach

    :param s3Resource: string
    :param bucket: string
    :return: none
    """
   my_bucket = s3Resource.Bucket(bucket)
   print(f'Deleting objects in bucket: {bucket}')
   my_bucket.objects.all().delete()
   # Potentially enable detailed logging for troubleshooting the method
   #boto3.set_stream_logger('')

# Upload a file 
def uploadFile(s3Client, bucket, source_file_name, key_name, content_type, metadata={}):
    """Upload a file from a local source file to s3 with the specified key name and also
    adding provided metadata

    :param s3Client: string
    :param bucket: string
    :param source_file_name: string
    :param key_name: string
    :param content_type: string
    :param metadata: string Optional metadata to associate
    :return: none
    """
    response = s3Client.upload_file(
        Bucket=bucket, 
        Key=key_name,
        Filename=source_file_name,
        ExtraArgs={
            'ContentType': content_type,
            'Metadata': metadata
            }
    ) 

def create_presigned_url(s3Client, bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param s3Client: string
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    # Generate a presigned URL for the S3 object
    try:
        response = s3Client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


# Global body - invoke the main function, which will in turn invoke all the others
main()