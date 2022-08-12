import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("notion-cms-devto-firebase-adminsdk-86xvp-a449708b08.json")
firebase_admin.initialize_app(cred)


db = firestore.client()