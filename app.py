from flask import Flask, render_template, request, jsonify
from checker import GraduationChecker

app = Flask(__name__)
checker = GraduationChecker("graduation_data.json")


@app.route("/")
def index():
    """메인 페이지"""
    majors = checker.get_major_list()
    return render_template("index.html", majors=majors)


@app.route("/check", methods=["POST"])
def check():
    """졸업요건 계산 API"""
    data = request.get_json()

    major = data.get("major", "")
    # 쉼표로 구분된 과목명을 리스트로 변환
    courses_raw = data.get("courses", "")
    completed_courses = [c.strip() for c in courses_raw.split(",") if c.strip()]
    total_credits = int(data.get("total_credits", 0))
    foreign_lang_cert = data.get("foreign_lang_cert", False)
    info_cert = data.get("info_cert", False)

    result = checker.check(
        major=major,
        completed_courses=completed_courses,
        total_credits=total_credits,
        foreign_lang_cert=foreign_lang_cert,
        info_cert=info_cert
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
