from flask import Flask
from flask_cors import CORS

app=Flask()
CORS(app,origins=["http://localhost:3000"])

@app.route("/",methods=["POST"])
def run():
    return "hi"

app.run(port=5000,debug=True)