# library imports
import os
import cv2
import numpy
import typing
import pandas as pd
import face_recognition
from datetime import datetime


class DataImport:
    "This Class helps in Importing the data and Creating required Folders"

    def make_folders(
            self,
            saved_image_folder: typing.Union[str, bytes, os.PathLike] = None,
            attendance_folder_path: typing.Union[str, bytes,
                                                 os.PathLike] = None,
            image_folder: typing.Union[str, bytes,
                                       os.PathLike] = None) -> None:
        """Function to create folders 'saved_images, Attendance and images'

        Parameters
        -----------
            - `saved_image_folder` (str, bytes, os.PathLike, optional): Folder to save Snapshots of Check-in's and Check-out's of Employees. Defaults to None.
            
            - `attendance_folder_path` (str, bytes, os.PathLike, optional): Folder to save Attendance data in csv format (if used). Defaults to None.
            
            - `image_folder` (str, bytes, os.PathLike, optional): Folder to store images of employees for detection. Defaults to None.
        """

        if not saved_image_folder:
            if "saved_images" not in os.listdir(os.getcwd()):
                os.mkdir(os.path.join(os.getcwd(), "saved_images"))
        else:
            if saved_image_folder not in os.listdir(os.getcwd()):
                os.mkdir(os.path.join(os.getcwd(), saved_image_folder))

        if not attendance_folder_path:
            if "Attendance" not in os.listdir(os.getcwd()):
                os.mkdir(os.path.join(os.getcwd(), "Attendance"))
                self.attendance_folder_path = os.path.join(
                    os.getcwd(), "Attendance")
        else:
            if attendance_folder_path not in os.listdir(os.getcwd()):
                os.mkdir(os.path.join(os.getcwd(), attendance_folder_path))
            self.attendance_folder_path = os.path.join(os.getcwd(),
                                                       attendance_folder_path)

        if not image_folder:
            if "images" not in os.listdir(os.getcwd()):
                os.mkdir(os.path.join(os.getcwd(), "images"))
        else:
            if image_folder not in os.listdir(os.getcwd()):
                os.mkdir(os.path.join(os.getcwd(), image_folder))

    def make_csv_file(self) -> typing.Union[str, bytes, os.PathLike]:
        """Function to create a CSV file containing employee attendance of current date

        Returns:
            `Tuple(str, bytes, os.PathLike)` : Path where the CSV file will be saved.
        """
        date = datetime.now().date()
        attendance_file_path = os.path.join(self.attendance_folder_path,
                                            "Attendance_" + str(date) + ".csv")
        exists = os.path.isfile(attendance_file_path)
        if exists:
            print("Attendance File Present")
        else:
            try:
                with open(attendance_file_path, "a+"):
                    data = {
                        "Name": [],
                        "Time": [],
                        "Date": [],
                        "Check In": [],
                        "Check Out": [],
                        "Check Out Time": []
                    }
                    df = pd.DataFrame(data,
                                      columns=[
                                          "Name", "Time", "Date", "Check In",
                                          "Check Out", "Check Out Time"
                                      ])  # create DataFrame
                    df.set_index("Name", inplace=True)
                    df.to_csv(attendance_file_path, sep=",", header=True)
                    print("Attendance File Created")
            except Exception as e:
                print("ERROR IN CREATING Attendance File!!!")
                raise Exception(e)  #raise Exception if any
        return attendance_file_path

    def read_images(
        self,
        image_path: typing.Union[str, bytes, os.PathLike] = None
    ) -> typing.Tuple[typing.List[numpy.ndarray], typing.List[numpy.ndarray]]:
        """Function to read images from the given image path

        Parameters
        -----------
            - `image_path` (str, bytes, os.PathLike, optional): Path of the image folder. Defaults to None.

        Returns
        --------
            `Tuple[List[numpy.ndarray], List[numpy.ndarray]]`: Images and Known Face Names
        """

        if not image_path:
            image_path = "images"
        images = []  #list to store images
        known_face_names = []  #list to store face names
        image_list = os.listdir(
            image_path)  #Get all the images from the image path
        print(f"Images Present in {image_path} are: {image_list}")
        for img in image_list:
            current_Img = cv2.imread(os.path.join(image_path,
                                                  img))  #reading the images
            images.append(current_Img)

            img_name = os.path.splitext(img)[0].split("_")[0]
            known_face_names.append(img_name)
        print(f"Names Extracted from Images: {known_face_names}")

        return images, known_face_names


class Preprocessing:
    "Class to Preprocess the Images for Face Recognition"

    def faceEncodings(self, images: typing.List[numpy.ndarray]) -> typing.List:
        """Function to get face encodings from Images

        Parameters
        -----------
            - `images` (List[numpy.ndarray]): Images in the form of arrays

        Returns
        --------
            `List`: Encodings of Images
        """
        encodeList = []  #list of Encodings

        #looping through all the images
        for img in images:
            img = cv2.cvtColor(
                img, cv2.COLOR_BGR2RGB)  #converting the image from BGR to RGB
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList
