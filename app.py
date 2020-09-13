import http.client
import json
import mysql.connector
from flask import Flask, request, jsonify
from mysql.connector import errorcode

app = Flask(__name__)

config = {
    'host': 'covidgurad.mysql.database.azure.com',
    'user': 'a1763100@covidgurad',
    'port': 3306,
    'password': 'harshu5797@CSE',
    'database': 'covidguard'
}

resp = {'Details': '', 'Status': ''}


@app.route('/', methods=['GET'])
def home():
    return '''<h1>OTP API</h1>
    <p>APIs to send OTP to a specific phone number and verify the OTP</p>'''


@app.errorhandler(404)
def page_not_found():
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route('/api/v1/otpgen', methods=['GET'])
def api_otp_gen():
    try:
        conn = mysql.connector.connect(**config)
        print("Connection established")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with the user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        query_parameters = request.args
        phone = query_parameters.get('phone')

        if len(phone) < 10 or phone.isdigit() is False:
            resp['Status'] = 'Error'
            resp['Details'] = 'Improper phone number'
            return jsonify(resp)

        http_conn = http.client.HTTPConnection("2factor.in")
        payload = ""
        headers = {'content-type': "application/x-www-form-urlencoded"}
        request_path = "/API/V1/9d2cacdb-f4de-11ea-9fa5-0200cd936042/SMS/" + phone + "/AUTOGEN"
        http_conn.request("GET", request_path, payload, headers)
        res = http_conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode('utf-8'))

        status = json_data['Status']
        cur = conn.cursor()
        if status == 'Success':
            session_id = json_data['Details']
            _query = "INSERT INTO SessionID VALUES({0},'{1}')"
            # print(_query.format(phone,session_id))
            cur.execute(_query.format(phone, session_id))
            del json_data['Details']
            conn.commit()
            cur.close()
            conn.close()
            return json_data
        else:
            conn.commit()
            cur.close()
            conn.close()
            return json_data


@app.route('/api/v1/otpverify', methods=['GET'])
def api_otp_verify():
    try:
        conn = mysql.connector.connect(**config)
        print("Connection established")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with the user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        query_parameters = request.args
        phone = query_parameters.get('phone')
        otp = query_parameters.get('otp')
        _query = "SELECT session_id from SessionID WHERE phone_number = {0}"
        cur = conn.cursor()
        cur.execute(_query.format(phone))
        db_output = cur.fetchall()

        if len(db_output) == 0:
            resp['Status'] = 'Error'
            resp['Details'] = 'Invalid Phone number'
            return jsonify(resp)
        else:
            session_id = db_output[0][0]

        http_conn = http.client.HTTPConnection("2factor.in")
        payload = ""
        headers = {'content-type': "application/x-www-form-urlencoded"}
        request_path = "/API/V1/9d2cacdb-f4de-11ea-9fa5-0200cd936042/SMS/VERIFY/" + session_id + "/" + otp
        http_conn.request("GET", request_path, payload, headers)
        res = http_conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode('utf-8'))

        status = json_data['Status']

        if status == 'Success':
            session_id = json_data['Details']
            _query = "DELETE FROM SessionID WHERE phone_number = {0}"
            cur = conn.cursor()
            print(_query.format(phone, session_id))
            cur.execute(_query.format(phone))
            conn.commit()
            cur.close()
            return json_data
        else:
            conn.commit()
            cur.close()
            conn.close()
            return json_data


@app.route('/create', methods=['POST'])
def create_id():
    try:
        conn = mysql.connector.connect(**config)
        cur = conn.cursor()
        _json = request.json
        print(_json)
        _ID = (_json['ID'])
        _Identifier = _json['Identifier']
        _UUID = _json['UUID']
        _Major = _json['Major']
        _Minor = _json['Minor']
        sql_query = "Insert INTO venue_data(ID,Identifier,UUID,Major,Minor) values(%s,%s,%s,%s,%s)"
        if _ID and _Identifier and _UUID and _Major and _Minor and request.method == 'POST':
            # insert record in database
            data = (_ID, _Identifier, _UUID, _Major, _Minor)
            cur.execute(sql_query, data)
            conn.commit()
            res = jsonify('Record created successfully.')
            res.status_code = 200
            cur.close()
            conn.close()
            return res
        else:
            cur.close()
            conn.close()
            return not_found()

    except Exception as e:
        print(e)


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found:' + request.url,
    }
    response_msg = jsonify(message)
    response_msg.status_code = 404
    return response_msg


@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        conn = mysql.connector.connect(**config)
        cur = conn.cursor()
        _json = request.json
        print(_json)
        for obj in _json:
            print(obj["ID"])
            print(obj["Identifier"])
            print(obj["Time_Entered"])
            print(obj["Time_Exited"])

            cur.execute("Insert INTO log_data(ID,Identifier,Time_Entered,Time_Exited) values(%s,%s,%s,%s)",
                        (obj["ID"], obj["Identifier"], obj["Time_Entered"], obj["Time_Exited"]))

        conn.commit()
        cur.close()
        conn.close()
        res = jsonify('Record created successfully.')
        res.status_code = 200
        return res
    except Exception as e:
        print(e)


if __name__ == '__main__':
    app.run()
