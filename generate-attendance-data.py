import pymongo
import random
import datetime
import calendar

random.seed(15)

DEFAULT_CONNECTION_URL = "mongodb://localhost:27017/"
ATTENDACE_DB_NAME = "Attendance"
EMPLOYEE_DB_NAME = "Employee"
client = pymongo.MongoClient(DEFAULT_CONNECTION_URL)
db_names = client.list_database_names()
if ATTENDACE_DB_NAME in db_names:
    print("Deleting:", ATTENDACE_DB_NAME)
    client.drop_database(ATTENDACE_DB_NAME)

if EMPLOYEE_DB_NAME in db_names:
    print("Deleting:", EMPLOYEE_DB_NAME)
    client.drop_database(EMPLOYEE_DB_NAME)

attendance_database = client[ATTENDACE_DB_NAME]
employee_database = client[EMPLOYEE_DB_NAME]

month_number = [2, 3, 4, 5]
year = 2022

#* Employee names
all_employees = [
    "Rishabh", "Jaspreet", "Kartik", "Dheeraj", "Usha", "Sonia", "Ramesh",
    "Suresh", "Priyanka", "Pavani", "Harry", "Saniya", "Anjali", "Varun",
    "Himanshu", "Sneha", "Ranjit", "Richa", "Dhriti", "Hrithik", "Vipin",
    "Shakti"
]

#* employees present per month
employee_present_range = (len(all_employees) - 6, len(all_employees))

#* email of each employee
email = [f"{name.lower()}@attendance.com" for name in all_employees]
emp_with_email = dict(zip(all_employees, email))

#* creating collection of each employee
for i in range(len(email)):
    emp_collection = employee_database[email[i]]

for x in month_number:
    month = x
    days = calendar.monthrange(year, month)[1]  #no of days in a month

    for i in range(1, days + 1):
        date = datetime.date(year, month, i)
        coll_date = date.strftime("%Y-%m-%d")
        rand_num = random.randint(employee_present_range[0],
                                  employee_present_range[1])
        collection = attendance_database[f"Attendance_{coll_date}"]
        name_and_email = random.sample(list(emp_with_email.items()), rand_num)

        for j in range(rand_num):

            check_in_time = datetime.datetime(
                year, month, i, 9,
                0) + datetime.timedelta(minutes=random.randrange(60))

            total_time = datetime.datetime(100,
                                           1,
                                           1,
                                           hour=random.randrange(6, 8),
                                           minute=random.randrange(60),
                                           second=random.randrange(60))

            idle_time = datetime.datetime(100,
                                          1,
                                          1,
                                          hour=random.randrange(1, 2),
                                          minute=random.randrange(60),
                                          second=random.randrange(60))

            check_out_time = datetime.datetime(
                year, month, i, 7,
                0) + datetime.timedelta(minutes=random.randrange(60))
            record = {
                'Name': name_and_email[j][0],
                'Email': name_and_email[j][1],
                'Time': check_in_time.strftime("%H:%M:%S"),
                'Date': date.strftime("%d/%m/%Y"),
                "Check_In": 1,
                "Check Out": 1,
                "Check Out Time": check_out_time.strftime("%H:%M:%S")
            }
            emp_record = {
                'Name': name_and_email[j][0],
                'Email': name_and_email[j][1],
                'Date': date.strftime("%d/%m/%Y"),
                'Total_Time': total_time.strftime("%H:%M:%S"),
                'Idle_Time': idle_time.strftime("%H:%M:%S")
            }
            print("Attendance Record:", record)
            print("Employee Record:", emp_record)
            collection.insert_one(record)
            employee_database[name_and_email[j][1]].insert_one(emp_record)

        print(end="\n\n")

#! CUSTOM DATA (comment the previous code to use)
# start_day = 1
# no_of_days = 10
# month = 10
# year = 2022

# for i in range(start_day,no_of_days+1):
#     date = datetime.date(year,month,i)
#     coll_date = date.strftime("%Y-%m-%d")
#     rand_num = random.randint(employee_present_range[0],employee_present_range[1])
#     collection = attendance_database[f"Attendance_{coll_date}"]
#     name_and_email = random.sample(list(emp_with_email.items()),rand_num)

#     for j in range(rand_num):
#         check_in_time = datetime.datetime(year,month,i,9,0)+datetime.timedelta(minutes=random.randrange(60))
#         total_time = datetime.datetime(100, 1, 1, hour=random.randrange(6,8), minute=random.randrange(60), second=random.randrange(60))
#         idle_time = datetime.datetime(100, 1, 1, hour=random.randrange(1,2), minute=random.randrange(60), second=random.randrange(60))

#         #* to avoid check-out on last date
#         # if i != no_of_days:
#         check_out_time = datetime.datetime(year,month,i,7,0)+datetime.timedelta(minutes=random.randrange(60))
#         record = {
#             'Name': name_and_email[j][0],
#             'Email':name_and_email[j][1],
#             'Time': check_in_time.strftime("%H:%M:%S"),
#             'Date': date.strftime("%d/%m/%Y"),
#             "Check_In":1,
#             "Check Out":1,
#             "Check Out Time":check_out_time.strftime("%H:%M:%S")
#                 }
#         emp_record = {
#             'Name': name_and_email[j][0],
#             'Email':name_and_email[j][1],
#             'Date': date.strftime("%d/%m/%Y"),
#             'Total_Time': total_time.strftime("%H:%M:%S"),
#             'Idle_Time': idle_time.strftime("%H:%M:%S")
#         }
#         # else:
#         #     record = {
#         #         'Name': name_and_email[j][0],
#         #         'Email': name_and_email[j][1],
#         #         'Time': check_in_time.strftime("%H:%M:%S"),
#         #         'Date': date.strftime("%d/%m/%Y"),
#         #         "Check_In":1,
#         #         "Check Out":0,
#         #         "Check Out Time":None
#         #             }
#         #     emp_record = {
#         #         'Name': name_and_email[j][0],
#         #         'Email':name_and_email[j][1],
#         #         'Date': date.strftime("%d/%m/%Y"),
#         #         'Total_Time': None,
#         #         'Idle_Time': None
#         #     }
#         print("Attendance Record:",record)
#         print("Employee Record:",emp_record)
#         collection.insert_one(record)
#         employee_database[name_and_email[j][1]].insert_one(emp_record)

#     print(end = "\n\n")