import json


class GraduationChecker:

    def __init__(self, data_path="graduation_data.json"):

        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.majors = self.data["전공목록"]

    def get_major_list(self):

        return list(self.majors.keys())

    def get_courses_by_major(self, major):

        if major not in self.majors:

            return {
                "major_required": [],
                "liberal_required": []
            }

        req = self.majors[major]

        major_courses = []

        for course in req["전공필수"]:

            major_courses.append({
                "name": course,
                "credit": self.data["학점단위"]["전공필수과목당"]
            })

        liberal_courses = []

        for course in req["교양기초필수"]:

            if course == "채플":
                credit = self.data["학점단위"]["채플"]
            else:
                credit = self.data["학점단위"]["교양과목당"]

            liberal_courses.append({
                "name": course,
                "credit": credit
            })

        # 전공선택 목록도 반환
        elective_courses = []

        for course in req.get("전공선택", []):

            elective_courses.append({
                "name": course,
                "credit": self.data["학점단위"]["전공선택과목당"]
            })

        return {
            "major_required": major_courses,
            "liberal_required": liberal_courses,
            "major_electives": elective_courses
        }

    def check(
        self,
        major,
        completed_courses,
        total_credits,
        foreign_lang_cert,
        info_cert
    ):

        if major not in self.majors:

            return {
                "error": "존재하지 않는 전공입니다."
            }

        req = self.majors[major]

        result = {}

        needed_credits = req["총이수학점"]

        result["총이수학점"] = {
            "필요": needed_credits,
            "현재": total_credits,
            "충족": total_credits >= needed_credits,
            "부족": max(
                0,
                needed_credits - total_credits
            )
        }

        required_courses = req["전공필수"]

        completed_required = [
            c for c in required_courses
            if c in completed_courses
        ]

        missing_required = [
            c for c in required_courses
            if c not in completed_courses
        ]

        result["전공필수"] = {
            "전체": required_courses,
            "이수완료": completed_required,
            "미이수": missing_required,
            "충족": len(missing_required) == 0
        }

        liberal_courses = req["교양기초필수"]

        completed_liberal = [
            c for c in liberal_courses
            if c in completed_courses
        ]

        missing_liberal = [
            c for c in liberal_courses
            if c not in completed_courses
        ]

        result["교양기초"] = {
            "전체": liberal_courses,
            "이수완료": completed_liberal,
            "미이수": missing_liberal,
            "충족": len(missing_liberal) == 0
        }

        # 전공선택(학점 기준) 검사
        elective_courses = req.get("전공선택", [])

        completed_elective = [
            c for c in elective_courses
            if c in completed_courses
        ]

        elective_credit_per = self.data["학점단위"]["전공선택과목당"]

        completed_elective_credits = len(completed_elective) * elective_credit_per

        needed_major_elective_credits = req.get("전공최소학점", 0)

        result["전공선택"] = {
            "전체": elective_courses,
            "이수완료": completed_elective,
            "이수학점": completed_elective_credits,
            "필요학점": needed_major_elective_credits,
            "충족": completed_elective_credits >= needed_major_elective_credits,
            "부족": max(0, needed_major_elective_credits - completed_elective_credits)
        }

        result["졸업인증"] = {

            "외국어인증": {
                "취득": foreign_lang_cert,
                "충족": foreign_lang_cert
            },

            "정보/산업실무역량인증": {
                "취득": info_cert,
                "충족": info_cert
            },

            "충족":
            foreign_lang_cert and info_cert
        }

        checks = [

            result["총이수학점"]["충족"],
            result["전공필수"]["충족"],
            result["교양기초"]["충족"],
            result["전공선택"]["충족"],
            result["졸업인증"]["충족"]

        ]

        fulfilled = sum(checks)

        result["전체달성률"] = round(
            (fulfilled / len(checks)) * 100
        )

        result["졸업가능"] = all(checks)

        return result

