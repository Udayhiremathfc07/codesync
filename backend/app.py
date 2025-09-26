from flask import Flask
from flask_cors import CORS   # 👈 import

app = Flask(__name__)
CORS(app)   # 👈 enable CORS

@app.route('/')
def hello():
    return 'Uday'

if __name__ == '__main__':
    app.run(debug=True)
