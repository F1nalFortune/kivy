import requests
import json
from kivy.app import App

class MyFirebase():

  wak = "AIzaSyDwRYIDcSZTaFcKSOsFn1bi0abpX3TDCC8"
  def sign_up(self, email, password):
    app = App.get_running_app()
    print("Signup!!")
    #Send Email and Password to firebase
    #Firebase sends localId, authtoken, refreshToken
    signup_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key=" + self.wak
    signup_payload = {"email": email, "password": password, "returnSecureToken": True}
    sign_up_request = requests.post(signup_url, data=signup_payload)
    sign_up_data = json.loads(sign_up_request.content.decode())
    print(sign_up_request.ok)
    print(sign_up_data)
    if sign_up_request.ok == True:
      refresh_token = sign_up_data['refreshToken']
      localId = sign_up_data['localId']
      idToken = sign_up_data['idToken']
      print(f"Refresh Token: {refresh_token}")
      print(f"Local Id: {localId}")
      print(f"Id Token: {idToken}")
      # Save refresh token to a file
      with open("refreshToken.txt", "w") as f:
        f.write(refresh_token)

      # Save tokens to variables within Main App class
      app.local_id = localId
      app.id_token = idToken

      # Create new key in database from localId
      my_data = '{"email":""}'
      post_request = requests.patch(f"https://blacklister-b7bc8.firebaseio.com/{localId}.json?auth={idToken}", data=my_data)
      print(post_request.ok)
      print(post_request.content.decode())
      # app.change_screen("home_screen")
    if sign_up_request.ok == False:
        console.log("ERROR SIGN UP REQUEST")
        error_data = json.loads(sign_up_request.content.decode())
        error_message = error_data["error"]['message']
        app.root.ids['login_screen'].ids['login_message'].text = error_message.replace("_", " ")
    pass
  def sign_in(self, email, password):
    pass
