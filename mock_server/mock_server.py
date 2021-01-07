from flask import Flask, jsonify
from data_version import version_generator


app = Flask(__name__)


@app.route("/version", methods=["GET", "POST"])
def get_version():
    return jsonify(version_generator())


if __name__ == "__main__":
    app.run(port=5000)
