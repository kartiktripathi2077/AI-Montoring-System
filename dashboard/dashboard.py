from flask import render_template, request, session, redirect, url_for, Blueprint, jsonify
import json
import bcrypt
import pymongo
import calendar
# from datetime import timedelta
from itertools import groupby

#custom package import
from dashboard.generate_reports.reports import Graph_Plotly
from email_oauth.email_using_oauth import Send_Email

#instantiating the app
dashboard_app = Blueprint("dashboard_app",
                          __name__,
                          static_folder="static",
                          template_folder="dashboard_templates",
                          url_prefix="/dash")
dashboard_app.secret_key = "secret!"  #secret key

#loading config.json file for configurations
with open('dashboard\config.json') as f:
    config = json.load(f)

#* mongodb connection
mongodb_url = config["mongodb_url"]
client = pymongo.MongoClient(mongodb_url)

#* attendance database
attendance_database = client[config["attendance_database_name"]]

#* login database
login_database = client[config["login_database_name"]]
login_collection_name = config[
    "login_collection_name"]  #collection name from config
login_collection = login_database[login_collection_name]

#* employee database
employee_database = client[config["employee_database_name"]]

#email object
mail = Send_Email()

data, dates = None, None  #using global scope variables
month_name, month_data = None, None  #using global scope variables


############################# Login #############################
@dashboard_app.route('/')
def dashboard_index():
    "Index Page of the application"
    global login_collection  #using the global scope variables
    login_collection = login_database[
        login_collection_name]  #fetching data from database
    if 'dash_username' in session:
        return redirect(url_for('dashboard_app.dashboard'))

    return render_template('login/login-dashboard.html', alert=False)


@dashboard_app.route('/login', methods=['POST'])
def dashboard_login():
    if request.method == "POST":
        if request.form:
            login_user = login_collection.find_one(
                {'Email':
                 request.form['email'].lower()})  #find user in database
            if login_user:
                if login_user[
                        "Role"] == 'Admin':  #only admin users can access the database
                    if bcrypt.checkpw(request.form['password'].encode('utf8'),
                                      login_user['Password']):
                        session['dash_username'] = login_user['Name']
                        session['dash_email'] = login_user['Email']
                        # session.permanent = True
                        return redirect(
                            url_for('dashboard_app.dashboard_index'))
                else:
                    return render_template('login/login-dashboard.html',
                                           alert=True,
                                           alert_msg="Access Not Available!!")

            return render_template(
                'login/login-dashboard.html',
                alert=True,
                alert_msg="Invalid username/password combination")
    else:
        return "Invalid Request"


@dashboard_app.route('/change_password', methods=['POST'])
def dashboard_change_password():
    if request.method == 'POST':
        if request.form:
            global login_collection
            user_details = login_collection.find_one(
                {'Email': session["dash_email"]})
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
                    return redirect(url_for('dashboard_app.dashboard_logout'))

                else:
                    return redirect(url_for('dashboard_app.dashboard_index'))

            else:
                return redirect(url_for('dashboard_app.dashboard_index'))

    return redirect(url_for('dashboard_app.dashboard'))


@dashboard_app.route('/logout')
def dashboard_logout():
    if 'dash_username' in session:
        try:
            session.pop("dash_username", None)
            session.pop("dash_email", None)
            return redirect(url_for('dashboard_app.dashboard_index'))
        except KeyError:
            return redirect(url_for('dashboard_app.dashboard_index'))
    else:
        return redirect(url_for('dashboard_app.dashboard_index'))


############################# Dashboard #############################


@dashboard_app.route('/reports')
@dashboard_app.route('/reports/<string:months_name>')
@dashboard_app.route('/dashboard')
@dashboard_app.route('/dashboard/<string:months_name>')
def dashboard(months_name=None):
    if 'dash_username' in session:
        global data, dates, month_name, month_data
        data = sorted(attendance_database.list_collection_names(),
                      reverse=True)
        dates = [file.split('_')[1] for file in data]
        month_name, month_data = [], []
        #making two list
        for month, date in groupby(dates, key=lambda x: x.split('-')[1]):
            month_name.append(calendar.month_name[int(month)])
            month_data.append([calendar.month_name[int(month)], list(date)])

        # for specific urls
        if "dashboard" in request.url_rule.rule:
            if months_name:
                for month, dates in month_data:
                    if month == months_name:
                        data = [f"Attendance_{file}" for file in dates]

                        return render_template('dashboard/index.html',
                                               dates=enumerate(zip(
                                                   dates, data)),
                                               month=False)
            return render_template('dashboard/index.html',
                                   dates=enumerate(month_name),
                                   month=True)
        # for reports
        else:
            if months_name:
                graph = Graph_Plotly(database=attendance_database)
                graph.create_graph(months_name)
                return render_template("dashboard/report.html")

            return render_template('dashboard/monthly_reports.html',
                                   dates=enumerate(month_name))

    else:
        return redirect(url_for('dashboard_app.dashboard_index'))


@dashboard_app.route('/employee/<string:collection_name>')
def employee(collection_name):
    if 'dash_username' in session:
        collection = attendance_database[collection_name]
        content = collection.find()
        return render_template('dashboard/employee.html',
                               content=enumerate(content))
    else:
        return redirect(url_for('dashboard_app.dashboard_index'))


#monitoring function
@dashboard_app.route('/monitoring_settings', methods=['POST'])
def monitoring_settings():
    if 'dash_username' in session:
        if request.method == "POST":
            if request.form:
                monitoring_settings_config = {
                    "idle_time": request.form["idletime"],
                    "time_for_saving": request.form["time_for_saving"]
                    # "minattendance": request.form["minattendance"]
                }
                json_object = json.dumps(monitoring_settings_config, indent=4)
                with open('monitoring_settings.json', 'w') as f:
                    f.write(json_object)

            return redirect(url_for('dashboard_app.dashboard'))
    else:
        return redirect(url_for('dashboard_app.dashboard_index'))


@dashboard_app.route('/monitoring_config')
def monitoring_config():
    with open('monitoring_settings.json', 'r') as f:
        monitoring_config = json.loads(f.read())
    return jsonify(monitoring_config)


#* employee settings
# ? add employee
@dashboard_app.route('/add_employee')
def add_employee():
    if 'dash_username' in session:
        return render_template("dashboard/add-employee.html")
    else:
        return redirect(url_for('dashboard_app.dashboard_index'))


@dashboard_app.route('/add_into_data', methods=["POST"])
def add_into_data():
    if request.method == "POST":
        if request.form:
            data = dict(request.form)
            global login_collection
            existing_user = login_collection.find_one(
                {'Email': request.form['Email']})

            if not existing_user:
                data['Password'] = bcrypt.hashpw(
                    data['Password'].encode('utf-8'), bcrypt.gensalt())
                punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                name = data['Name']
                for s in name:
                    if s in punc:
                        name = name.replace(s, "")
                data["Name"] = name
                login_collection.insert_one(data)
                login_collection = login_database[login_collection_name]

                _ = employee_database[data['Email']]

                mail.new_employee_email(emp_data=data)
                return render_template("dashboard/add-employee.html",
                                       employee_add=True)

            return render_template("dashboard/add-employee.html",
                                   email_present=True)


# !end of add employee


# * All employees, change employee password and remove employee
@dashboard_app.route('/change_employee_password_html')
@dashboard_app.route('/remove_employee_html')
@dashboard_app.route('/all_employees')
def render_all_employees_change_password_and_remove_html():
    if 'dash_username' in session:
        global login_collection
        login_collection = login_database[login_collection_name]
        content = login_collection.find()
        if "change_employee_password_html" in request.url_rule.rule:
            return render_template('dashboard/all_employee.html',
                                   content=enumerate(content),
                                   change_password=True)
        elif "remove_employee_html" in request.url_rule.rule:
            return render_template('dashboard/all_employee.html',
                                   content=enumerate(content),
                                   remove=True)
        else:
            return render_template('dashboard/all_employee.html',
                                   content=enumerate(content))
    else:
        return redirect(url_for('dashboard_app.dashboard_index'))


@dashboard_app.route('/change_employee_password/<string:emp_email>',
                     methods=['POST', 'GET'])
@dashboard_app.route('/remove_employee/<string:emp_email>',
                     methods=['POST', 'GET'])
def change_employee_password_and_remove(emp_email):
    if request.method == 'GET':
        if 'dash_username' in session:
            emp_details = login_collection.find_one({'Email': emp_email})
            if "change_employee_password" in request.url_rule.rule:
                return render_template(
                    'dashboard/change_employee_password.html',
                    emp_details=emp_details,
                    change_password=True)
            else:
                return render_template(
                    'dashboard/change_employee_password.html',
                    emp_details=emp_details,
                    remove=True)
        else:
            return redirect(url_for('dashboard_app.dashboard_index'))

    elif request.method == 'POST':
        if request.form:
            emp_details = login_collection.find_one(
                {'Email': request.form['employee_email']})
            if emp_details:
                if "change_employee_password" in request.url_rule.rule:
                    if request.form['new_password'] == request.form[
                            'confirm_new_password']:
                        new_password = bcrypt.hashpw(
                            request.form['new_password'].encode('utf-8'),
                            bcrypt.gensalt())
                        login_collection.update_one(
                            emp_details, {"$set": {
                                "Password": new_password
                            }})
                        return render_template(
                            'dashboard/change_employee_password.html',
                            emp_details=emp_details,
                            change_password=True,
                            success=True,
                            success_message=
                            f"Password of {emp_details['Name']} Changed Successfully!"
                        )
                    else:
                        return render_template(
                            'dashboard/change_employee_password.html',
                            emp_details=emp_details,
                            change_password=True,
                            error=True,
                            error_message="Password do not Match!")
                else:
                    login_collection.delete_one(emp_details)
                    return render_template(
                        'dashboard/change_employee_password.html',
                        emp_details=emp_details,
                        remove=True,
                        success=True,
                        success_message=
                        f"Employee {emp_details['Name']} has been Removed Successfully!!"
                    )
            else:
                emp_details = login_collection.find_one({'Email': emp_email})
                return render_template(
                    'dashboard/change_employee_password.html',
                    emp_details=emp_details,
                    change_password=True,
                    error=True,
                    error_message=
                    "Employee does not exist, Check the entered Email Address!"
                )


# ! end of change password employee and remove employee


@dashboard_app.route('/emp_reports')
@dashboard_app.route('/emp_reports/<string:emp_email>')
@dashboard_app.route('/emp_reports/<string:emp_email>/<string:month_name>')
def emp_reports(emp_email=None, month_name=None):
    if not emp_email and not month_name:
        global login_collection
        login_collection = login_database[login_collection_name]
        content = login_collection.find()
        return render_template('dashboard/all_employee.html',
                               content=enumerate(content),
                               emp_reports=True)
    else:
        correct_email = emp_email.replace("%40", "@")
        emp_data = employee_database[correct_email]
        dates = [i["Date"] for i in emp_data.find({})]
        month_names_list = []
        if emp_email and not month_name:
            for month, data in groupby(
                    dates,
                    key=lambda x: calendar.month_name[int(x.split("/")[1])]):
                month_names_list.append(month)
            return render_template('dashboard/monthly_reports.html',
                                   dates=enumerate(month_names_list),
                                   emp_reports=True,
                                   emp_email=correct_email)
        else:
            graph = Graph_Plotly(database=employee_database)
            for month, data in groupby(
                    dates,
                    key=lambda x: calendar.month_name[int(x.split("/")[1])]):
                if month == month_name:
                    month_data = list(data)
                    # print(month_data)
            graph.create_employee_graph(correct_email, month_name, month_data)
            return render_template("dashboard/report.html")


if __name__ == "__main__":
    dashboard_app.run(debug=True, threaded=True)