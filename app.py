from flask import Flask, render_template, request, jsonify
from checker import GraduationChecker

app = Flask(__name__)

checker = GraduationChecker("graduation_data.json")



@app.route("/")
def index():

    majors = checker.get_major_list()

    return render_template(
        "index.html",
        majors=majors
    )


@app.route("/courses/<major>")
def get_courses(major):

    courses = checker.get_courses_by_major(major)

    return jsonify(courses)


@app.route("/check", methods=["POST"])
def check():

    data = request.get_json()

    major = data.get("major", "")
    completed_courses = data.get("courses", [])

    total_credits = float(
        data.get("total_credits", 0)
    )

    foreign_lang_cert = data.get(
        "foreign_lang_cert",
        False
    )

    info_cert = data.get(
        "info_cert",
        False
    )

    result = checker.check(
        major=major,
        completed_courses=completed_courses,
        total_credits=total_credits,
        foreign_lang_cert=foreign_lang_cert,
        info_cert=info_cert
    )

    return jsonify(result)


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True
    )

