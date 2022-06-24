import pymongo
import bcrypt

DEFAULT_CONNECTION_URL = "mongodb://localhost:27017/"
DB_NAME= "Login-Database"
client = pymongo.MongoClient(DEFAULT_CONNECTION_URL)
db_names = client.list_database_names()
if DB_NAME in db_names:
    print("Deleting:", DB_NAME)
    client.drop_database(DB_NAME)
dataBase = client[DB_NAME]

#* Names of the Employees
names = ["Rishabh","Jaspreet","Kartik","Dheeraj","Usha","Sonia","Ramesh","Suresh","Priyanka","Pavani","Harry","Saniya","Anjali","Varun","Himanshu","Sneha","Ranjit","Richa","Dhriti","Hrithik","Vipin","Shakti"]

email = [f"{name.lower()}@attendance.com" for name in names]
password = "1234" #change password
password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

#* Users to keep in admin
admin_users_list = ['Rishabh','Jaspreet','Kartik']

collection = dataBase["Login"]
for i in range(len(names)):
    if names[i] in admin_users_list:
        role = "Admin"
    else:
        role = "User"
    record = {"Name":names[i],"Email":email[i],"Password":password,"Role":role}
    print(record)
    collection.insert_one(record)