
import functions_framework
#from google.cloud import pubsub

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def examUploadHandle(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    print("BUCKET ID")
    print(cloud_event.data["message"]["attributes"]["bucketId"])
    print("OBJECT ID")
    print(cloud_event.data["message"]["attributes"]["objectId"])

