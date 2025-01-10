
import functions_framework
import os
#from google.cloud import pubsub
from google.cloud import storage

storage_client = storage.Client()
PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "imageasy-processed-") + storage_client.project

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def examUploadHandle(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    print("BUCKET ID")
    origin_bucket_name = cloud_event.data["message"]["attributes"]["bucketId"]
    print(origin_bucket_name)
    print("OBJECT ID")
    object_name = cloud_event.data["message"]["attributes"]["objectId"]
    print(object_name)
    move_object(origin_bucket_name, PROCESSED_BUCKET, object_name)


def move_object(origin_bucket_name, dest_bucket_name, object_name):
    origin_bucket = storage_client.bucket(origin_bucket_name)
    dest_bucket = storage_client.bucket(dest_bucket_name)
    blob = origin_bucket.blob(object_name)
    # Copiar o blob para o bucket de destino
    new_blob = origin_bucket.copy_blob(blob, dest_bucket, object_name)
    # Excluir o blob antigo do bucket de origem
    #blob.delete()
