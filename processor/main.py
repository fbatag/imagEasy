
import functions_framework
import os
#from google.cloud import pubsub
from proclib.utils import move_object, processFile


PROCESSED_BUCKET_NAME = os.environ.get("PROCESSED_BUCKET", "imageasy-processed-")
MODEL_NAME = "gemini-1.5-flash-002"
PROMPT = "Extraia os pedidos de exames escritos nesse documento, colocando um em cada linnha e escrevendo por extenso os que estiverem abreviados para melhor compreensão."

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def examUploadHandle(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    origin_bucket_name = cloud_event.data["message"]["attributes"]["bucketId"]
    object_name = cloud_event.data["message"]["attributes"]["objectId"]
    result = processFile(origin_bucket_name, object_name, MODEL_NAME, PROMPT)
    print(result)
    move_object(origin_bucket_name, PROCESSED_BUCKET_NAME, object_name)

