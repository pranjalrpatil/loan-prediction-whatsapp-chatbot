from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sklearn
import pandas as pd
import joblib
import math

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

def generatePredictionData(msg,fields):
    intFields = ["Dependents","ApplicantIncome"]
    floatFields = ["CoapplicantIncome", "LoanAmount", "Loan_Amount_Term", "Credit_History"]
    removedFields = ["Gender", "Married", "Dependents", "Education", "Self_Employed", "Property_Area"]
    content = msg.split('\n')
    d = {}
    for i in range(len(content)):
        if fields[i] in intFields:
            d[fields[i]] = int(content[i].split(': ')[1])
        elif fields[i] in floatFields:
            d[fields[i]] = float(content[i].split(': ')[1])
        else:
            d[fields[i]] = content[i].split(': ')[1]
    d["LoanAmount_log"] = math.log(d["LoanAmount"])
    d["Gender_Male"] = 1 if d["Gender"].lower() == "male" else 0
    d["Gender_Female"] = 0 if d["Gender"].lower() == "male" else 1

    d["Married_No"] = 1 if d["Married"].lower() == "no" else 0
    d["Married_Yes"] = 0 if d["Married"].lower() == "no" else 1

    for i in range(4):
        d[f"Dependents_{i}"] = 1 if d["Dependents"] == i else 0

    d["Education_Graduate"] = 1 if d["Education"].lower() == "graduate" else 0
    d["Education_Not Graduate"] = 0 if d["Education"].lower() == "graduate" else 1

    d["Self_Employed_No"] = 0 if d["Self_Employed"].lower() == "yes" else 1
    d["Self_Employed_Yes"] = 1 if d["Self_Employed"].lower() == "yes" else 0

    for p in ["Rural","Urban","Semiurban"]:
        d[f"Property_Area_{p}"] = 1 if d["Property_Area"].lower() == p.lower() else 0

    for k in removedFields:
        del d[k]

    print(d)
    return d

def predict(d):
    l=[]
    li = ["ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term", "Credit_History", "LoanAmount_log",
          "Gender_Female", "Gender_Male", "Married_No", "Married_Yes", "Dependents_3", "Dependents_0", "Dependents_1",
          "Dependents_2", "Education_Graduate", "Education_Not Graduate", "Self_Employed_No", "Self_Employed_Yes",
          "Property_Area_Rural", "Property_Area_Semiurban", "Property_Area_Urban"]
    for f in li:
        l.append(d[f])

    LoadedModel = joblib.load('TestModel.pkl')
    df = pd.DataFrame([l], columns=li)
    prediction = LoadedModel[0].predict(df)
    print('\nprediction:', prediction)
    return prediction[0]

@app.route("/sms", methods=['POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    fields = ["Gender", "Married", "Dependents", "Education", "Self_Employed", "ApplicantIncome"
        , "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term", "Credit_History", "Property_Area"]
    msg = request.form.get('Body')
    # Create reply
    resp = MessagingResponse()
    initial_messages = ["hi","hello","hey","sup"]
    if msg.lower() in initial_messages:
        resp.message("Hey!! 💸Welcome to forecastLoan💸 \n 🔹In order to know if your loan is approved or not, please fill all the details below👇🏻")
        s=""
        for f in fields:
            s += f+":\n"
        resp.message(s)
    else:
        d = generatePredictionData(msg, fields)
        pred = predict(d)
        if pred == 1:
            resp.message("Loan will be approved!")
        else:
            resp.message("Loan will not be approved!")
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
