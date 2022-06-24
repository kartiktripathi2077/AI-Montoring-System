from flask import Flask, render_template, Response, request, session, redirect, url_for
import os
import cv2
import json
import bcrypt
import pymongo
from datetime import timedelta, datetime, time
from email_oauth.email_using_oauth import Send_Email

# custom package imports
from data_ingestion.data_import_and_preprocessing import DataImport, Preprocessing
from database_api_functions.db_api_functions import DatabaseAPI

#dashboard app
from dashboard.dashboard import dashboard_app

# instantiate flask app
app = Flask(__name__, template_folder="templates")

#registering the dashboard app
app.register_blueprint(dashboard_app)
#secret key
app.secret_key = "secret!"
# app.config["SESSION_PERMANENT"] = True

#for setting the session time
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# making objects
camera = cv2.VideoCapture(0)  # change this if camera not working
data_import = DataImport()
preprocessing = Preprocessing()

# loading config.json
with open("config.json") as f:
    config_file = json.load(f)

# making all the folders
data_import.make_folders(config_file["saved_image_folder"],
                         config_file["attendance_folder_path"],
                         config_file["image_path"])

# calling important functions
images, known_face_names = data_import.read_images(
    image_path=config_file["image_path"])
known_face_encodings = preprocessing.faceEncodings(images)

# creating database object
database = DatabaseAPI(camera, known_face_names, known_face_encodings,
                       config_file["mongo_db_connection_url"],
                       config_file["attendance_database_name"],
                       config_file["employee_database_name"],
                       config_file["saved_image_folder"])

# creating collection
database.make_database_collection()

#mongodb connection
mongodb_url = config_file["mongo_db_connection_url"]
client = pymongo.MongoClient(mongodb_url)


#* login database
login_collection_name = config_file[
    "login_collection_name"]  #collection name from config
login_database = client[config_file["login_database_name"]]
login_collection = login_database[login_collection_name]

#* employee database
employee_database = client[config_file["employee_database_name"]]

#* Monitoring
total_time = datetime(100, 1, 1, hour=0, minute=0, second=0)
idle_time = datetime(100, 1, 1, hour=0, minute=0, second=0)
temp_idle_time = datetime(100, 1, 1, hour=0, minute=0, second=0)

#email object
mail = Send_Email()


############################# Login #############################
@app.route('/')
def index():
    global login_collection  #using the global scope variables
    login_collection = login_database[
        login_collection_name]  #fetching data from database
    if 'username' in session:
        return redirect(url_for('home'))

    return render_template('login/login.html', alert=False)


@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        if request.form:
            login_user = login_collection.find_one(
                {'Email':
                 request.form['email'].lower()})  #find user in database
            if login_user:
                if bcrypt.checkpw(request.form['password'].encode('utf8'),
                                  login_user['Password']):
                    session['username'] = login_user['Name']
                    session['email'] = login_user['Email']
                    return redirect(url_for('index'))

            return render_template(
                'login/login.html',
                alert=True,
                alert_msg="Invalid username/password combination")
    else:
        return "Invalid Request"


@app.route('/change_password', methods=['POST'])
def change_password():
    if request.method == 'POST':
        if request.form:
            global login_collection
            user_details = login_collection.find_one(
                {'Email': session["email"]})
            if request.form["new_password"] == request.form[
                    "confirm_new_password"]:
                if bcrypt.checkpw(
                        request.form['current_password'].encode('utf8'),
                        user_details['Password']):
                    new_password = bcrypt.hashpw(
                        request.form['new_password'].encode('utf-8'),
                        bcrypt.gensalt())
                    login_collection.update_one(
                        user_details, {"$set": {
                            "Password": new_password
                        }})
                    return redirect(url_for('logout'))
                else:
                    return "Current password does not match!!"

            else:
                return "New Password and Confirm New Password does not match"

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    if 'username' in session:
        try:
            session.pop('username', None)
            session.pop('email', None)
            return redirect(url_for('index'))
        except KeyError:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


##############################Main App#####################################
@app.route("/home")
def home():
    if "username" in session:
        database.make_database_collection()
        return render_template("attendance-templates//index.html")

    return redirect(url_for('index'))


@app.route("/video_feed")
def video_feed():
    return Response(database.gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/checkin", methods=["POST"])
def checkin():
    if "username" in session:
        name = session["username"]
        email = session["email"]
        check, status = database.check_in(name, email, save_image=True)
        if check:
            return render_template(
                "attendance-templates//after_check_in.html",
                status="Checked In Status For {} : {} ".format(name, status))
        else:
            return render_template(
                "attendance-templates//result.html",
                status="Checked In Status For {} : {} ".format(name, status))

    return redirect(url_for('index'))


@app.route("/checkout", methods=["POST"])
def checkout():
    if "username" in session:
        name = session["username"]
        email = session["email"]
        status = database.check_out(email, save_image=True)
        return render_template("attendance-templates//result.html",
                               status="Checked Out Status {} : {} ".format(
                                   name, status))

    return redirect(url_for('index'))


@app.route("/confirm", methods=["POST"])
def confirm():
    if "username" in session:
        name = database.gen_name()
        if name != session["username"]:
            return render_template(
                "attendance-templates//unknown.html",
                status="You are not " + session["username"] +
                "!! If you think this is a mistake contact the administrator")
        return render_template(
            "attendance-templates//mid.html",
            status="Hello {}!! , Please Check In".format(name),
            name=name)

    return redirect(url_for('index'))


# calculation of employee time spent
@app.route('/total_time/<string:email>')
def total_time_route(email):
    def generate():
        global total_time, idle_time
        date = datetime.now().strftime("%d/%m/%Y")
        correct_email = email.replace("%40", "@")
        current_data = employee_database[correct_email].find_one(
            {"Date": date})
        database_total_time = datetime.strptime(current_data["Total_Time"],
                                                "%H:%M:%S")
        database_idle_time = datetime.strptime(current_data["Idle_Time"],
                                               "%H:%M:%S")
        if total_time <= database_total_time:
            total_time = database_total_time
        if idle_time <= database_idle_time:
            idle_time = database_idle_time
        total_time += timedelta(seconds=1)
        with open("monitoring_settings.json") as f:
            monitoring_config = json.load(f)

        if ((total_time.second) + (total_time.minute * 60) +
            (total_time.hour * 3600)) % int(
                monitoring_config["time_for_saving"]) == 0:
            new_data = {
                "$set": {
                    "Total_Time": total_time.strftime("%H:%M:%S"),
                    "Idle_Time": idle_time.strftime("%H:%M:%S")
                }
            }
            employee_database[correct_email].update_one(current_data, new_data)
        yield total_time.strftime("%H:%M:%S")

    return Response(generate(), mimetype="text")


@app.route('/idle_time')
def idle_time_route():
    def generate():
        global temp_idle_time, idle_time
        name = database.gen_name()
        if name != "Unknown":
            temp_idle_time = datetime(100, 1, 1, hour=0, minute=0, second=0)
        else:
            temp_idle_time += timedelta(seconds=1)
            
            #loading monitoring_settings.json
            with open("monitoring_settings.json") as f:
                monitoring_config = json.load(f)

            temp_idle_time_seconds = ((temp_idle_time.second) +
                                      (temp_idle_time.minute * 60) +
                                      (temp_idle_time.hour * 3600))
            if temp_idle_time_seconds >= int(monitoring_config["idle_time"]):
                idle_time += timedelta(seconds=1)

        yield idle_time.strftime("%H:%M:%S")

    return Response(generate(), mimetype="text")

#end of calculation

@app.route('/update')
def update():
    if "username" in session:
        try:
            return render_template('attendance-templates//update.html',
                                   alert=False)
        except Exception as e:
            print(e)
    return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload():
    if "username" in session:
        try:
            global database, images, known_face_names, known_face_encodings
            if request.files:
                if "image" in request.files["image"].content_type:
                    image = request.files["image"]
                    img_ext = os.path.splitext(image.filename)[1]
                    punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                    email = session["email"].split("@")[0]
                    for s in email:
                        if s in punc:
                            email = email.replace(s, "")

                    name = session["username"] + "_" + email
                    path = os.path.join(config_file["image_path"],
                                        name + img_ext)
                    #deleting previous image
                    images_list = os.listdir(config_file["image_path"])
                    for img in images_list:
                        if name == os.path.splitext(img)[0]:
                            os.remove(
                                os.path.join(config_file["image_path"], img))
                    #saving new image
                    image.save(path)

                else:
                    return render_template("attendance-templates//update.html",
                                           wrong_type=True)

            if request.form:
                punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                email = session["email"].split("@")[0]
                for s in email:
                    if s in punc:
                        email = email.replace(s, "")

                name = session["username"] + "_" + email
                path = os.path.join(config_file["image_path"], name + ".jpg")
                #deleting previous image
                images_list = os.listdir(config_file["image_path"])
                for img in images_list:
                    if name == os.path.splitext(img)[0]:
                        os.remove(os.path.join(config_file["image_path"], img))

                #moving new image
                src = os.path.join("static", "temp",
                                   "{}.jpg".format(session["username"]))
                os.rename(src, path)

            #re-reading the images and re-creating the new encodings
            images, known_face_names = data_import.read_images(
                config_file["image_path"])
            known_face_encodings = preprocessing.faceEncodings(images)
            database = DatabaseAPI(camera, known_face_names,
                                   known_face_encodings,
                                   config_file["mongo_db_connection_url"],
                                   config_file["attendance_database_name"],
                                   config_file["employee_database_name"],
                                   config_file["saved_image_folder"])
            return render_template("attendance-templates//update.html",
                                   alert=True)

        except Exception as e:
            print(e)
    else:
        return redirect(url_for('index'))


@app.route("/take_snapshot", methods=["POST"])
def take_snapshot():
    snapshot()
    return render_template("attendance-templates//confirm_snapshot.html")


def snapshot():
    print("entered function snapshot")
    success, frame = camera.read()
    if success:
        print("Taking Snapshot")
        path = os.path.join("static", "temp",
                            "{}.jpg".format(session["username"]))
        if cv2.imwrite(path, frame):
            print("Saved the temporary snapshot")
            return path
        else:
            print("Failed to save the temporary snapshot")


@app.route("/leave_application", methods=["POST", "GET"])
def leave_application():
    if "username" in session:
        if request.method == "GET":
            return render_template(
                "attendance-templates//leave_application.html")
        elif request.method == "POST":
            if request.form:
                form_data = dict(request.form)
                admin_details = login_collection.find({"Role": "Admin"})
                admin_emails = []
                for details in admin_details:
                    admin_emails.append(details["Email"])
                mail.leave_email(admin_emails=admin_emails,
                                 emp_email=session["email"],
                                 form_data=form_data)
                return render_template(
                    "attendance-templates//leave_application.html", alert=True)
    else:
        return redirect(url_for('index'))


if __name__ == "__main__":
    try:
        app.app_context().push()
        app.run(debug=True)

    except Exception:
        print("Stopping the Program!!!!")

    finally:
        camera.release()
        cv2.destroyAllWindows()