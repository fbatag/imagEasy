import os
from flask import send_file, request
from vertexai.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models
from google.cloud import storage

EXAM_SUPPORTED_TYPES=["text/plain,application/pdf,image/jpeg,image/png"]
storage_client = storage.Client()

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0.5,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

def processFile(blob_exam, prompt, model_name):
    print("METHOD: processFile -> " + blob_exam.name)
    model = GenerativeModel(model_name, generation_config=generation_config, safety_settings=safety_settings)
    parts = [prompt]
    parts.append(Part.from_uri(uri=getBlobUri(blob_exam), mime_type=getBlobType(blob_exam)))
    generatedFiles = model.generate_content(parts)
    return generatedFiles.text

def move_object(origin_bucket_name, dest_bucket_name, object_name):
    dest_bucket_name += storage_client.project
    print("METHOD: move_object -> origin_bucket: " + origin_bucket_name + ", dest_bucket: " + dest_bucket_name)
    origin_bucket = storage_client.bucket(origin_bucket_name)
    dest_bucket = storage_client.bucket(dest_bucket_name)
    blob = origin_bucket.blob(object_name)
    # Copiar o blob para o bucket de destino
    new_blob = origin_bucket.copy_blob(blob, dest_bucket, object_name)
    # Excluir o blob antigo do bucket de origem
    #blob.delete()

def getBlobType(blob):
    if blob.content_type in EXAM_SUPPORTED_TYPES:
        return blob.content_type
    return "text/plain"

def getBlobUri(blob):
    return "gs://" + CODE_BUCKET_NAME + "/" + blob.name