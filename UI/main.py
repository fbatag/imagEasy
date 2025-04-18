import  os
import datetime
from flask import Flask, request, render_template
from imageasylib.utils import get_project_Id, get_iap_user, get_user_folder, get_user_files, getSignedUrlParam

UPLOAD_BUCKET_NAME = os.environ.get("UPLOAD_BUCKET_NAME", "imageasy-upload-") + get_project_Id()
PROCESSED_BUCKET_NAME = os.environ.get("PROCESSED_BUCKET_NAME", "imageasy-processed-") + get_project_Id()

print("(RE)LOADING APPLICATION")

app = Flask(__name__)
timezone = None

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
    if timezone == None:
        return set_timezone()
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
                           processsing_exams = loadUserExams(UPLOAD_BUCKET_NAME),
                           processsed_exams = loadUserExams(PROCESSED_BUCKET_NAME)
                           )
    
def loadUserExams(bucket_name):
    print("METHOD: loadUserExams:" + bucket_name)
    exams_blobs = get_user_files(bucket_name)
    exams = []
    print(exams_blobs)
    for blob in exams_blobs:
        parts = blob.name.split('/')
        createDatetime = blob.time_created - datetime.timedelta(minutes=timezone)
        exams.append((createDatetime.strftime("%Y-%m-%d %H:%M:%S"), parts[-1]))
    return exams

#@app.route('/set_timezone', methods=['GET'])
def set_timezone():
    timezoneOffset = request.form.get('timezoneOffset', "NOT_FOUND")
    if timezoneOffset == "NOT_FOUND":
        return render_template("init.html")
    print("METHOD: set_timezone: " + timezoneOffset)
    global timezone
    timezone = int(timezoneOffset)
    return renderIndex()

if __name__ == "__main__":
    app.run(debug=True)

