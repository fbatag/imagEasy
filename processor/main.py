import sys
import base64
import json
import functions_framework
#from google.cloud import pubsub

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def hello_pubsub(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"])
    print("pubsub_message:" + pubsub_message)
    json_pubsub_message = json.loads(pubsub_message)
    bucket_name = json_pubsub_message["bucket"]
    obj_bame = json_pubsub_message["name"]
    print("bucket_name:" + bucket_name)
    print("obj_bame:" + obj_bame)

test_message = {
    "attributes": {
        "specversion": "1.0",
        "id": "13500356927496703",
        "source": " //pubsub.googleapis.com/projects/dasa-gem-app/topics/imag-easy-upload-topic",
        "type": "google.cloud.pubsub.topic.v1.messagePublished",
        "datacontenttype": "application/json",
        "time": "2025-01-08T17:56:07.108Z"
    },
    "data": {
        "message": {
            "attributes": {
                "bucketId": "imag-easy-upload-dasa-gem-app",
                "eventTime": "2025-01-08T17:56:06.952527Z",
                "eventType": "OBJECT_FINALIZE",
                "notificationConfig": "projects/_/buckets/imag-easy-upload-dasa-gem-app/notificationConfigs/6",
                "objectGeneration": "1736358966947877",
                "objectId": "None/Care Plus - acesso dois cartões (dental e médico).pdf",
                "payloadFormat": "JSON_API_V1"
            },
            "data": "ewogICJraW5kIjogInN0b3JhZ2Ujb2JqZWN0IiwKICAiaWQiOiAiaW1hZy1lYXN5LXVwbG9hZC1kYXNhLWdlbS1hcHAvTm9uZS9DYXJlIFBsdXMgLSBhY2Vzc28gZG9pcyBjYXJ0b8yDZXMgKGRlbnRhbCBlIG1lzIFkaWNvKS5wZGYvMTczNjM1ODk2Njk0Nzg3NyIsCiAgInNlbGZMaW5rIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3N0b3JhZ2UvdjEvYi9pbWFnLWVhc3ktdXBsb2FkLWRhc2EtZ2VtLWFwcC9vL05vbmUlMkZDYXJlJTIwUGx1cyUyMC0lMjBhY2Vzc28lMjBkb2lzJTIwY2FydG8lQ0MlODNlcyUyMChkZW50YWwlMjBlJTIwbWUlQ0MlODFkaWNvKS5wZGYiLAogICJuYW1lIjogIk5vbmUvQ2FyZSBQbHVzIC0gYWNlc3NvIGRvaXMgY2FydG/Mg2VzIChkZW50YWwgZSBtZcyBZGljbykucGRmIiwKICAiYnVja2V0IjogImltYWctZWFzeS11cGxvYWQtZGFzYS1nZW0tYXBwIiwKICAiZ2VuZXJhdGlvbiI6ICIxNzM2MzU4OTY2OTQ3ODc3IiwKICAibWV0YWdlbmVyYXRpb24iOiAiMSIsCiAgImNvbnRlbnRUeXBlIjogImFwcGxpY2F0aW9uL3BkZiIsCiAgInRpbWVDcmVhdGVkIjogIjIwMjUtMDEtMDhUMTc6NTY6MDYuOTUyWiIsCiAgInVwZGF0ZWQiOiAiMjAyNS0wMS0wOFQxNzo1NjowNi45NTJaIiwKICAic3RvcmFnZUNsYXNzIjogIlNUQU5EQVJEIiwKICAidGltZVN0b3JhZ2VDbGFzc1VwZGF0ZWQiOiAiMjAyNS0wMS0wOFQxNzo1NjowNi45NTJaIiwKICAic2l6ZSI6ICIxMDI4ODE4IiwKICAibWQ1SGFzaCI6ICJBTXIxN2NVOEM2N1cySlhlait5c2N3PT0iLAogICJtZWRpYUxpbmsiOiAiaHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL2Rvd25sb2FkL3N0b3JhZ2UvdjEvYi9pbWFnLWVhc3ktdXBsb2FkLWRhc2EtZ2VtLWFwcC9vL05vbmUlMkZDYXJlJTIwUGx1cyUyMC0lMjBhY2Vzc28lMjBkb2lzJTIwY2FydG8lQ0MlODNlcyUyMChkZW50YWwlMjBlJTIwbWUlQ0MlODFkaWNvKS5wZGY/Z2VuZXJhdGlvbj0xNzM2MzU4OTY2OTQ3ODc3JmFsdD1tZWRpYSIsCiAgImNyYzMyYyI6ICJuYWlMd0E9PSIsCiAgImV0YWciOiAiQ0tYZ3Radlo1b29ERUFFPSIKfQo=",
            "messageId": "13500356927496703",
            "message_id": "13500356927496703",
            "publishTime": "2025-01-08T17:56:07.108Z",
            "publish_time": "2025-01-08T17:56:07.108Z"
        },
        "subscription": "projects/dasa-gem-app/subscriptions/eventarc-southamerica-east1-trigger-vxgfox2z-sub-738"
    }
}

if __name__ == "__main__":
    hello_pubsub(test_message)