import os
import cv2
import typing
import pymongo
import numpy as np
import face_recognition
from datetime import datetime


class DatabaseAPI:
    "Class to interact with database and generate frames"

    def __init__(self, camera: cv2.VideoCapture,
                 known_face_names: typing.List[np.ndarray],
                 known_face_encodings: typing.List[np.ndarray],
                 mongo_db_url: str, database_name: str,
                 employee_database_name: str,
                 img_folder_path: typing.Union[str, bytes, os.PathLike]):
        """Instantiate the DatabaseAPI object

        Parameters
        -----------
           - `camera` (cv2.VideoCapture): cv2 camera object.
           - `known_face_names` (List[numpy.ndarray]): list of known face names.
           - `known_face_encodings` (List[numpy.ndarray]): list of known face encodings.
           - `mongo_db_url` (str): mongodb connection url
           - `database_name` (str): Attendance database name of MongoDB
           - `img_folder_path` (str, bytes, os.PathLike): Image folder path for recognition.

        Raises
        -------
            `Exception`: Connection issue with Database from MongoDB.
        """
        self.camera = camera
        self.known_face_names = known_face_names
        self.known_face_encodings = known_face_encodings
        self.img_folder_path = img_folder_path
        try:
            # database name check and initialization
            client = pymongo.MongoClient(mongo_db_url)
            DBlist = client.list_database_names()
            if database_name in DBlist:
                print(f"DB: '{database_name}' exists")
            else:
                print(
                    f"DB: '{database_name}' not yet present OR no collection is present in the DB"
                )
            self.database = client[database_name]
            self.emp_database = client[employee_database_name]
        except pymongo.errors.ConnectionFailure as e:
            print("Exception occurred while making connection")
            raise Exception(e)  #raise an error if connection fails

    def make_database_collection(self, collection_name: str = None):
        """Creates a collection in the MongoDB database. If the 
           name of the collection is not specified, 'Attendance_<current_date>' is used as the collection name.

        Parameters
        -----------
            - `collection_name` (str, optional): Name of the collection to create in the MongoDB database. Defaults to None.
        """
        if not collection_name:
            date = datetime.now().date()
            collection_name = "Attendance_" + str(date)
        collection_list = self.database.list_collection_names()
        if collection_name in collection_list:
            print(f"Collection:'{collection_name}' exists in Database")

        else:
            print(
                f"Collection:'{collection_name}' does not exist in Database OR no documents are present in the collection"
            )
        self.collection = self.database[collection_name]

    def check_in(self, name: str, email: str, save_image: bool = True):
        """Function to check-in an employee into the organization.

        Parameters
        -----------
            - `name` (str): Name of the employee.
            - `save_image` (bool, optional): Whether to take a Snapshot of an employee during check-in or not. Defaults to True.

        Returns
        --------
            - `True` or `False` (bool): It tells whether the employee checked out or not
            - `checkin_status` (str): Status of employee.
        """

        if not self.collection.find_one({"Name": name}):
            time_now = datetime.now()
            tStr = time_now.strftime("%H:%M:%S")
            dStr = time_now.strftime("%d/%m/%Y")
            cin = 1
            record = {
                "Name": name,
                "Email": email,
                "Time": tStr,
                "Date": dStr,
                "Check In": cin,
                "Check Out": None,
                "Check Out Time": None
            }
            emp_record = {
                'Name': name,
                'Email': email,
                'Date': dStr,
                'Total_Time': "00:00:00",
                'Idle_Time': "00:00:00"
            }
            self.collection.insert_one(record)
            self.emp_database[email].insert_one(emp_record)
            self.capture_frame(email,
                               check_status="check_in",
                               save_image=save_image)
            checkin_status = (
                "You Successfully Checked In at " +
                str(time_now.strftime("%H:%M:%S")) +
                ". Welcome to the Company . Have a Great Day at Work ")
            return True, checkin_status

        else:

            if self.collection.find_one({"Name": name, "Check Out": 1}):
                checkin_status = ("You Already Checked Out at " + str(
                    self.collection.find_one({"Name": name})["Check Out Time"])
                                  + " ! See You Tomorrow :)")
                return False, checkin_status
            elif self.collection.find_one({"Name": name, "Check In": 1}):
                checkin_status = (
                    "You Already Checked in at " +
                    str(self.collection.find_one({"Name": name})["Time"]) +
                    " ! You can now Check Out Only :)")
                return True, checkin_status

    def check_out(self, email: str, save_image: bool = True):
        """Function to check-out an employee into the organization.

        Parameters
        -----------
            - `email` (str): Email of the employee.
            - `save_image` (bool, optional): Whether to take a Snapshot of an employee during check-in or not. Defaults to True.

        Returns
        --------
            `checkout_status` (str): Status of employee.
        """
        if not self.collection.find_one({"Email": email}):
            checkout_status = "You Have not Checked In Yet"

        else:
            if self.collection.find_one({"Email": email, "Check Out": 1}):
                checkout_status = "You Already Checked Out at " + str(
                    self.collection.find_one({"Email": email
                                              })["Check Out Time"])
            else:
                time_now = datetime.now()
                self.collection.update_one(
                    self.collection.find_one({"Email": email}), {
                        "$set": {
                            "Check Out": 1,
                            "Check Out Time": time_now.strftime("%H:%M:%S")
                        }
                    })

                self.capture_frame(email,
                                   check_status="check_out",
                                   save_image=save_image)
                checkout_status = "Successfully Checked Out at " + str(
                    self.collection.find_one({"Email": email
                                              })["Check Out Time"])

        return checkout_status

    def capture_frame(self,
                      email: str,
                      check_status: str,
                      save_image: bool = True) -> None:
        """Function to capture Snapshots of Employees.
        
        Parameters
        -----------
            - `name` (str): Name of the employee.
            - `check_status` (str): Check-in or Check-out status of Employees.
            - `save_image` (bool, optional): Whether to save the snapshot of an employee or not. Defaults to True.
        
        """
        if self.img_folder_path and save_image:
            success, frame = self.camera.read()
            punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
            name = email.split("@")[0]
            for s in name:
                if s in punc:
                    name = name.replace(s, "")

            path = f"{self.img_folder_path}//{name}"
            if name not in os.listdir(self.img_folder_path):
                os.mkdir(path)
            img_path = f"{path}//{name}_{str(datetime.now().date())}_time-{str(datetime.now().time().strftime('%H-%M-%S'))}_{check_status}.jpg"
            check = cv2.imwrite(img_path, frame)
            if check:
                print("Image Saved Successfully")

    def gen_frames(self):
        "Function to Generate Frames and Recognize Faces."
        while True:
            success, frame = self.camera.read()  # read the camera frame
            name = "Unknown"

            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, face_encoding)

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]

                face_names.append(name)

            # Display the results
            for (top, right, bottom,
                 left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255),
                              2)

                # Draw a label with a name below the face
                cv2.rectangle(
                    frame,
                    (left, bottom - 35),
                    (right, bottom),
                    (0, 0, 255),
                    cv2.FILLED,
                )
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(
                    frame,
                    name,
                    (left + 6, bottom - 6),
                    font,
                    1.0,
                    (255, 255, 255),
                    1,
                )

            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    def gen_name(self) -> str:
        "Function to generate name after Recognition."
        while True:
            success, frame = self.camera.read()  # read the camera frame
            name = "Unknown"  # changed
            if not success:
                break
            else:
                # Resize frame of video to 1/4 size for faster face recognition processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                rgb_small_frame = small_frame[:, :, ::-1]

                # Only process every other frame of video to save time

                # Find all the faces and face encodings in the current frame of video
                face_locations = face_recognition.face_locations(
                    rgb_small_frame)
                face_encodings = face_recognition.face_encodings(
                    rgb_small_frame, face_locations)
                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(
                        self.known_face_encodings, face_encoding)
                    # Or instead, use the known face with the smallest distance to the new face
                    face_distances = face_recognition.face_distance(
                        self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]

                return name