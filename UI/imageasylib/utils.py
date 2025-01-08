import datetime
from flask import request
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from google import auth
from google.oauth2 import service_account
from google.cloud import storage

storage_client = storage.Client()

generation_config_flash = {
    "max_output_tokens": 8192,
    "temperature": 0.5,
    "top_p": 0.95,
}

generation_config_pro = {
    "max_output_tokens": 8192, # o modelo responde 32768, mas tanto a doc quanto a execução não aceita esse valor
    "temperature": 0.5,
    "top_p": 0.95,
}
safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# ATENÇÃO: Os parãmetros abaixo somente funcionam com prompt texto. Se um arquivo é incluido, dai erro "400 Request contains an invalid argument." 
#safety_settings_none = {
 #   #generative_models.HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
 #   generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
 #   generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
 #   generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
 #   generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
#}
def getGenerativeModel(model_name):
    if model_name == "gemini-1.5-flash-002":
        generation_config = generation_config_flash
    else:
        generation_config = generation_config_pro
    return GenerativeModel(model_name, generation_config=generation_config, safety_settings=safety_settings)

def get_project_Id():
    return storage_client.project

def get_iap_user():
    print("METHOD: get_iap_user")
    user = request.headers.get('X-Goog-Authenticated-User-Email', "None")
    if user != "None":
        user = user.replace("accounts.google.com:","")
    return user

def get_user_folder():
    print("METHOD: get_user_folder")
    user = get_iap_user()
    temp_user_dir = user.replace("@", "_").replace(".", "_")
    return temp_user_dir

def get_user_files(bucket_name):
    print("METHOD: get_user_files -> ")
    bucket = storage_client.bucket(bucket_name)
    return bucket.list_blobs(prefix=get_user_folder())

def getSignedUrlParam(dest_bucket_name, dest_object, filetype):
    credentials, project_id = auth.default()
    dest_bucket = storage_client.bucket(dest_bucket_name)
    blob = dest_bucket.blob(dest_object)
    expiration=datetime.timedelta(minutes=15)

    print('Content-Type: '+  filetype)
    if request.url_root == 'http://127.0.0.1:5000/':
        print("RUNNING LOCAL")
        signeUrl = blob.generate_signed_url(method='PUT', version="v4", expiration=expiration, content_type=filetype, 
                                    credentials=service_account.Credentials.from_service_account_file("../sa.json"),
                                    headers={"X-Goog-Content-Length-Range": "1,5000000000", 'Content-Type': filetype})
    else:
        print("CREDENTIALS")
        print(credentials.service_account_email)
        #if credentials.token is None:
        credentials.refresh(auth.transport.requests.Request())
        print(credentials.token)
        signeUrl = blob.generate_signed_url(method='PUT', version="v4", expiration=expiration, content_type=filetype, 
                                    service_account_email=credentials.service_account_email, access_token=credentials.token,
                                    headers={"X-Goog-Content-Length-Range": "1,5000000000", 'Content-Type': filetype})
        #except Exception as e:
        #    print(e)
    #print(signeUrl)
    return signeUrl

