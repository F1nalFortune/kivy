import kivy.core.text
from kivy.app import App
from kivy.base import EventLoop
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.camera import Camera
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from os.path import sep, expanduser, isdir, dirname
import datetime

from myfirebase import MyFirebase
import cv2
import face_recognition
import numpy as np
import os
import requests
import json
import pyrebase

config = {
    "apiKey": "AIzaSyDwRYIDcSZTaFcKSOsFn1bi0abpX3TDCC8",
    "authDomain": "blacklister-b7bc8.firebaseapp.com",
    "databaseURL": "https://blacklister-b7bc8.firebaseio.com",
    "projectId": "blacklister-b7bc8",
    "storageBucket": "blacklister-b7bc8.appspot.com",
    "messagingSenderId": "602245924486",
    "appId": "1:602245924486:web:9ea40d3ccb310ddfb7f307",
    "measurementId": "G-J5EBNVVJ7K"
}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()




class LoadDialog(FloatLayout):
    upload = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class DatabaseScreen(Screen):
    loadfile = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(upload=self.upload, cancel=self.dismiss_popup)
        self._popup = Popup(title="Upload folder", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def upload(self, path, company, localId, idToken):
        # with open(os.path.join(path, filename[0]), encoding='ISO-8859-1') as stream:
            # self.text_input.text = stream.read()
        print(f"Path: {path}")
        all_files = os.listdir(path)
        print(f"All Files: {all_files}")
        acceptable_formats = ['.png']
        acceptable_files = []


         # only grab acceptable file formats
        for file in all_files:
          if file[-4:] == '.png':
            acceptable_files.append(f"{file}")

         # upload each acceptable file
        for file in acceptable_files:
          path_on_cloud=f"{company}/{file}"
          path_local= f"{path}/{file}"
          response = storage.child(path_on_cloud).put(path_local)
          #response eg
          # {'name': "Toad's Place/craig_elkinz.png", 'bucket': 'blacklister-b7bc8.appspot.com', 'generation': '1578542328640757', 'metageneration': '1', 'contentType': 'image/png', 'timeCreated': '2020-01-09T03:58:48.640Z', 'updated': '2020-01-09T03:58:48.640Z', 'storageClass': 'STANDARD', 'size': '535352', 'md5Hash': '7SKntazlg5m7koUM9SSakg==', 'contentEncoding': 'identity', 'contentDisposition': "inline; filename*=utf-8''craig_elkinz.png", 'crc32c': 'cSr7xw==', 'etag': 'CPXpi7bQ9eYCEAE=', 'downloadTokens': '9f6d8e62-858b-4185-b052-4bf469f687a2'}
          name = file[:-4]
          my_data = '{"Date": "' + str(datetime.datetime.today().strftime('%Y-%m-%d')) + '"}'
          post_request = requests.put(f"https://blacklister-b7bc8.firebaseio.com/{company}/blacklisters/{name}.json?auth={idToken}", data=my_data)


        print(f"Acceptable Files: {acceptable_files}")

        self.dismiss_popup()

    def download(self, company, idToken):
      #grab list of names to gather
      request = requests.get(f"https://blacklister-b7bc8.firebaseio.com/{company}/blacklisters.json?auth={idToken}")
      request_data = request.content.decode()
      print(f"Data type: {type(request_data)}")
      print(request.content.decode())
      image_names = json.loads(request_data).keys()
      path_local = "./blacklist_names"
      for name in image_names:
        storage.child(f"{company}/{name}.png").download(f"./blacklist_names/{name}.png")

class HomeScreen(Screen):
    def init_main(self):
        pass

    def dostart(self, *largs):
        global capture
        capture = cv2.VideoCapture(0)
        fps = 30
        directory_in_str = './blacklist_names/'
        directory = os.fsencode(directory_in_str)

        #extract names from folder
        blacklist_names = []
        for file in os.listdir(directory):
          filename = os.fsdecode(file)
          if filename.endswith(".png"):
            blacklist_names.append(filename.replace(".png", ""))
          else:
            continue

        known_face_encodings = []
        known_face_names = []

        for name in blacklist_names:

          #loop over images
          #create face encodings
          image = face_recognition.load_image_file("{}{}.png".format(directory_in_str, name))
          face_encoding = face_recognition.face_encodings(image)[0]

          #save encodings
          #save names
          known_face_encodings.append(face_encoding)
          known_face_names.append(name)

        self.ids.qrcam.start(capture, fps, known_face_encodings, known_face_names)


    def doexit(self):
        global capture
        if capture != None:
            capture.release()
            capture = None
        EventLoop.close()

class LabelButton(ButtonBehavior, Label):
  pass

class LoginScreen(Screen):
  pass

class SettingsScreen(Screen):
  pass
class KivyCamera(Image):

    def __init__(self, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = None
        self.known_face_encodings = None
        self.known_face_names = None


    def start(self, capture, fps, known_face_encodings, known_face_names):
        self.capture = capture
        self.known_face_encodings = known_face_encodings
        self.known_face_names = known_face_names
        Clock.schedule_interval(self.update, 1.0/fps)

    def stop(self):
        Clock.unschedule_interval(self.update)
        self.capture = None

    def update(self, dt):
        # Grab a single frame of video
        ret, frame = self.capture.read()
        if ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
            # if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"

                # # If a match was found in self.known_face_encodings, just use the first one.
                # if True in matches:
                #     first_match_index = matches.index(True)
                #     name = known_face_names[first_match_index]

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]

                face_names.append(name)

            # process_this_frame = not process_this_frame


            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                if "Unknown" in name:
                    # Draw a box around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 189, 0), 2)

                    # Draw a label with a name below the face
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 189, 0), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

                else:
                    # Draw a box around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Draw a label with a name below the face
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # # Display the resulting image
            # cv2.imshow('Video', frame)
            #
            # # Hit 'q' on the keyboard to quit!
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

            # convert it to texture
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            # display image from the texture
            self.texture = image_texture
            self.canvas.ask_update()

capture = None
GUI = Builder.load_file("main.kv")

class mainApp(App):

    def build(self):
        self.my_firebase = MyFirebase()
        return GUI

    def on_start(self):
      #Get Database Data
      result = requests.get("https://blacklister-b7bc8.firebaseio.com/")
      #Populate Blacklisters
    def get(self):
      request = requests.get(f"https://blacklister-b7bc8.firebaseio.com/{self.local_id}.json?auth={self.id_token}")
      print(request.ok)
      print(request.content.decode())
    def on_stop(self):
        global capture
        if capture:
            capture.release()
            capture = None
    def change_screen(self, screen_name):
        screen_manager = self.root.ids['screen_manager']
        screen_manager.current = screen_name
mainApp().run()
