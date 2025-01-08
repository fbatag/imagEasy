import  os
from flask import Flask, request, render_template
from imageasylib.utils import get_project_Id, get_iap_user, get_user_folder, get_user_files, getSignedUrlParam

UPLOAD_BUCKET_NAME = os.environ.get("UPLOAD_BUCKET_NAME", "imag-easy-upload-") + get_project_Id()

print("(RE)LOADING APPLICATION")
app = Flask(__name__)

def get_user_version_info():
    return "User: " + get_iap_user() + " -  Version: 1.0.0"

@app.route("/getSignedUrl", methods=["GET"])
def getSignedUrl():
    print("METHOD: getSignedUrl")
    print(request.args)
    dest_bucket_name = request.args.get("dest_bucket")
    dest_object = request.args.get("dest_object")
    filetype = request.args.get("filetype")
    return getSignedUrlParam(dest_bucket_name, dest_object, filetype)


@app.route("/", methods=["GET", "POST"])
def index():
    print("METHOD: index -> " + request.method)
    clicked_button = request.form.get('clicked_button', "NOT_FOUND")
    print("clicked_button: ", clicked_button)
    #if clicked_button == "update_exams_btn": 
    #    return proceed("load_exam")
    #elif clicked_button == "load_exam":
    return renderIndex()

def renderIndex(page="index.html"):
    print("METHOD: renderIndex -> ")
    activeTab = request.form.get("activeTab", "tabExamReqLoader")
    print("activeTab: ", activeTab)
    choosen_model_name = request.form.get("model_name", "gemini-1.5-flash-002")
    return render_template(page, user_version_info=get_user_version_info(), 
                           activeTab=activeTab, 
                           choosen_model_name=choosen_model_name,
                           dest_bucket=UPLOAD_BUCKET_NAME, 
                           dest_folder=get_user_folder(),
                           processsing_exams = loadUserProcessingExams(),
                           )
    

def loadUserProcessingExams():
    print("METHOD: loadUserProcessingExams")
    processsing_exams_blobs = get_user_files(UPLOAD_BUCKET_NAME)
    processsing_exams = []
    for blob in processsing_exams_blobs:
        processsing_exams.append((blob.name, blob.time_created))
    return processsing_exams


if __name__ == "__main__":
    app.run(debug=True)

#considerar o uso:
# https://ai.google.dev/gemini-api/docs/prompting_with_media?lang=python
# https://developers.google.com/drive/api/guides/ref-export-formats