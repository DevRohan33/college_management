import os
import django
import boto3
from django.conf import settings
import requests
from dotenv import load_dotenv
import mimetypes



# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_portal.settings')
# django.setup()



# def test_without_acl():
#     print("=== Testing Without ACL (Bucket Policy Only) ===")
    
#     s3 = boto3.client(
#         's3',
#         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         region_name=settings.AWS_S3_REGION_NAME
#     )
    
#     try:
#         # Upload WITHOUT ACL (rely on bucket policy)
#         s3.put_object(
#             Bucket=settings.AWS_STORAGE_BUCKET_NAME,
#             Key='test_no_acl.html',
#             Body=b'<h1>Test without ACL</h1>',
#             ContentType='text/html'
#             # NO ACL parameter - using bucket policy instead
#         )
#         print("✅ File uploaded (no ACL)")
        
#         # Generate URL
#         url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/test_no_acl.html"
#         print(f"Test URL: {url}")
        
#         # Test access
#         response = requests.get(url)
#         if response.status_code == 200:
#             print("🎉 SUCCESS! Bucket policy is working!")
#             print("Response:", response.text)
#         else:
#             print(f"❌ Still not accessible: HTTP {response.status_code}")
#             print("Please check bucket policy syntax")
            
#         # Clean up
#         s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key='test_no_acl.html')
        
#     except Exception as e:
#         print(f"❌ Error: {e}")


load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")


def upload_to_s3(file_path, bucket_name):
    s3 = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    file_name =os.path.basename(file_path)
    content_type,_=mimetypes.guess_type(file_path)

    if content_type is None:
        content_type= "application/octet-stream"
    with open (file_path, 'rb')as file:
        s3.upload_fileobj(file,bucket_name, file_name, ExtraArgs={
            "ContentType": content_type
        })
    bucket_location = s3.get_bucket_location(Bucket=bucket_name)
    region = bucket_location['LocationConstraint'] if bucket_location['LocationConstraint'] else 'ap-south-1'
    file_url =f"https://s.{region}.amazonaws.com/{bucket_name}/{file_name}"
    return file_url

def main():
    file_path ='myprofile.jpg'
    file_url = upload_to_s3(file_path,AWS_STORAGE_BUCKET_NAME)
    print(f"File upload in aws : {file_url}")


if __name__ == "__main__":
    # test_without_acl()
    main()