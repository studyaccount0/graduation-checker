import json


class GraduationChecker:

    def __init__(self, data_path="graduation_data.json"):
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.majors = self.data["전공목록"]

    def get_major_list(self):
        return list(self.majors.keys())

    def get_tracks_by_major(self, major):
        if major not in self.majors:
            return {}
        return self.majors[major].get("트랙목록", {})

    def get_courses_by_major(self, major):
        if major not in self.majors:
            return {
                "major_required": [],
                "liberal_required": [],
                "major_electives": [],
                "tracks": {}
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

        elective_courses = []
        for course in req.get("전공선택", []):
            elective_courses.append({
                "name": course,
                "credit": self.data["학점단위"]["전공선택과목당"]
            })

        tracks = {}
        for track_name, track_data in req.get("트랙목록", {}).items():
            tracks[track_name] = {
                "설명": track_data.get("설명", ""),
                "트랙필수": [{"name": c, "credit": 3} for c in track_data["트랙필수"]],
                "트랙선택": [{"name": c, "credit": 3} for c in track_data["트랙선택"]],
                "최소이수학점": track_data["최소이수학점"],
                "필수학점": track_data["필수학점"]
            }

        return {
            "major_required": major_courses,
            "liberal_required": liberal_courses,
            "major_electives": elective_courses,
            "tracks": tracks
        }

    def get_minimum_route(self, major, completed_courses, selected_track=None):
        if major not in self.majors:
            return {"error": "존재하지 않는 전공입니다."}

        req = self.majors[major]
        route = []

        for course in req["전공필수"]:
            if course not in completed_courses:
                route.append({
                    "과목명": course,
                    "학점": self.data["학점단위"]["전공필수과목당"],
                    "구분": "전공필수"
                })

        for course in req["교양기초필수"]:
            if course not in completed_courses:
                credit = self.data["학점단위"]["채플"] if course == "채플" else self.data["학점단위"]["교양과목당"]
                route.append({
                    "과목명": course,
                    "학점": credit,
                    "구분": "교양기초필수"
                })

        if selected_track:
            track_list = req.get("트랙목록", {})
            if selected_track in track_list:
                for course in track_list[selected_track]["트랙필수"]:
                    if course not in completed_courses:
                        if not any(r["과목명"] == course for r in route):
                            route.append({
                                "과목명": course,
                                "학점": 3,
                                "구분": f"트랙필수({selected_track})"
                            })

                t_data = track_list[selected_track]
                t_min = t_data["최소이수학점"]
                t_req_courses = t_data["트랙필수"]
                t_elec_courses = t_data["트랙선택"]

                done_req = [c for c in t_req_courses if c in completed_courses]
                done_elec = [c for c in t_elec_courses if c in completed_courses]
                done_credits = (len(done_req) + len(done_elec)) * 3

                added_req = [r["과목명"] for r in route if "트랙필수" in r["구분"]]
                projected_credits = done_credits + len(added_req) * 3

                remaining = t_min - projected_credits
                if remaining > 0:
                    missing_elec = [c for c in t_elec_courses if c not in completed_courses]
                    needed_count = -(-remaining // 3)
                    for course in missing_elec[:needed_count]:
                        route.append({
                            "과목명": course,
                            "학점": 3,
                            "구분": f"트랙선택({selected_track})",
                            "비고": "학점 충족용 (여러 과목 중 선택 가능)"
                        })

        total_courses = len(route)
        total_credits = sum(r["학점"] for r in route)

        grouped = {}
        for r in route:
            key = r["구분"]
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)

        return {
            "총과목수": total_courses,
            "총학점": total_credits,
            "선택트랙": selected_track,
            "grouped": grouped,
            "route": route
        }

    def recommend_tracks(self, major, completed_courses):
        if major not in self.majors:
            return {"error": "존재하지 않는 전공입니다."}

        track_list = self.majors[major].get("트랙목록", {})

        if not track_list:
            return {"tracks": [], "message": "해당 전공에는 트랙이 없습니다."}

        results = []

        for track_name, track_data in track_list.items():
            t_required = track_data["트랙필수"]
            t_elective = track_data["트랙선택"]
            t_min = track_data["최소이수학점"]

            completed_req = [c for c in t_required if c in completed_courses]
            missing_req = [c for c in t_required if c not in completed_courses]
            completed_elec = [c for c in t_elective if c in completed_courses]
            missing_elec = [c for c in t_elective if c not in completed_courses]

            done_credits = (len(completed_req) + len(completed_elec)) * 3
            remaining_credits = max(0, t_min - done_credits)
            pct = min(100, round((done_credits / t_min) * 100))
            req_done = len(missing_req) == 0

            results.append({
                "트랙명": track_name,
                "설명": track_data.get("설명", ""),
                "달성률": pct,
                "이수학점": done_credits,
                "필요학점": t_min,
                "잔여학점": remaining_credits,
                "트랙필수_완료": completed_req,
                "트랙필수_미이수": missing_req,
                "트랙선택_완료": completed_elec,
                "트랙선택_미이수": missing_elec,
                "필수충족": req_done,
                "이수완료": req_done and done_credits >= t_min
            })

        results.sort(key=lambda x: (-x["달성률"], -x["이수학점"]))

        return {"tracks": results}

    def check(
        self,
        major,
        completed_courses,
        total_credits,
        foreign_lang_cert,
        info_cert,
        selected_track=None
    ):
        if major not in self.majors:
            return {"error": "존재하지 않는 전공입니다."}

        req = self.majors[major]
        result = {}

        needed_credits = req["총이수학점"]
        result["총이수학점"] = {
            "필요": needed_credits,
            "현재": total_credits,
            "충족": total_credits >= needed_credits,
            "부족": max(0, needed_credits - total_credits)
        }

        required_courses = req["전공필수"]
        completed_required = [c for c in required_courses if c in completed_courses]
        missing_required = [c for c in required_courses if c not in completed_courses]
        result["전공필수"] = {
            "전체": required_courses,
            "이수완료": completed_required,
            "미이수": missing_required,
            "충족": len(missing_required) == 0
        }

        liberal_courses = req["교양기초필수"]
        completed_liberal = [c for c in liberal_courses if c in completed_courses]
        missing_liberal = [c for c in liberal_courses if c not in completed_courses]
        result["교양기초"] = {
            "전체": liberal_courses,
            "이수완료": completed_liberal,
            "미이수": missing_liberal,
            "충족": len(missing_liberal) == 0
        }

        elective_courses = req.get("전공선택", [])
        completed_elective = [c for c in elective_courses if c in completed_courses]
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

        track_result = None
        track_satisfied = True

        if selected_track:
            track_list = req.get("트랙목록", {})
            if selected_track in track_list:
                track_data = track_list[selected_track]
                t_required = track_data["트랙필수"]
                t_elective = track_data["트랙선택"]
                t_min = track_data["최소이수학점"]

                completed_t_req = [c for c in t_required if c in completed_courses]
                missing_t_req = [c for c in t_required if c not in completed_courses]
                completed_t_elec = [c for c in t_elective if c in completed_courses]

                t_req_credits_done = len(completed_t_req) * 3
                t_elec_credits_done = len(completed_t_elec) * 3
                t_total_credits_done = t_req_credits_done + t_elec_credits_done

                req_satisfied = len(missing_t_req) == 0
                min_satisfied = t_total_credits_done >= t_min
                track_satisfied = req_satisfied and min_satisfied

                track_result = {
                    "선택트랙": selected_track,
                    "설명": track_data.get("설명", ""),
                    "트랙필수": {
                        "전체": t_required,
                        "이수완료": completed_t_req,
                        "미이수": missing_t_req,
                        "충족": req_satisfied
                    },
                    "트랙선택": {
                        "전체": t_elective,
                        "이수완료": completed_t_elec,
                        "이수학점": t_elec_credits_done
                    },
                    "총이수학점": t_total_credits_done,
                    "필요최소학점": t_min,
                    "충족": track_satisfied
                }

        result["트랙"] = track_result

        result["졸업인증"] = {
            "외국어인증": {"취득": foreign_lang_cert, "충족": foreign_lang_cert},
            "정보/산업실무역량인증": {"취득": info_cert, "충족": info_cert},
            "충족": foreign_lang_cert and info_cert
        }

        checks = [
            result["총이수학점"]["충족"],
            result["전공필수"]["충족"],
            result["교양기초"]["충족"],
            result["전공선택"]["충족"],
            result["졸업인증"]["충족"]
        ]

        if selected_track and track_result:
            checks.append(track_satisfied)

        fulfilled = sum(checks)
        result["전체달성률"] = round((fulfilled / len(checks)) * 100)
        result["졸업가능"] = all(checks)

        return result
