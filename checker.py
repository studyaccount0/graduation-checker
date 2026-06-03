import json


class GraduationChecker:

    def __init__(self, data_path="graduation_data.json"):
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.majors = self.data["전공목록"]

    def get_major_list(self):
        return list(self.majors.keys())

    def _course_name(self, course):
        return course["name"] if isinstance(course, dict) else course

    def _course_credit(self, course, default=3):
        return course["credit"] if isinstance(course, dict) else default

    def _uses_module(self, major):
        return major == "간호학과"

    def _get_track_list(self, major):
        if major not in self.majors:
            return {}
        return self.majors[major].get("트랙목록", {})

    def _get_module_list(self, major):
        if major not in self.majors:
            return {}
        if self._uses_module(major):
            return self.majors[major].get("모듈목록", self.majors[major].get("트랙목록", {}))
        return {}

    def _normalize_module_course(self, course):
        if isinstance(course, dict):
            return course
        return {"name": course, "credit": 3}

    def _module_course_required(self, course):
        return course.get("required", False) if isinstance(course, dict) else False

    def _normalize_specialization_data(self, specialization_data, kind):
        required_key = f"{kind}필수"
        elective_key = f"{kind}선택"
        # support fallback keys: if kind-specific keys missing, use the alternate kind's keys
        alt_kind = "트랙" if kind == "모듈" else "모듈"
        alt_required_key = f"{alt_kind}필수"
        alt_elective_key = f"{alt_kind}선택"

        raw_required = specialization_data.get(required_key)
        if raw_required is None:
            raw_required = specialization_data.get(alt_required_key, [])
        raw_elective = specialization_data.get(elective_key)
        if raw_elective is None:
            raw_elective = specialization_data.get(alt_elective_key, [])

        required_courses = [
            self._normalize_module_course(c)
            for c in raw_required
        ]
        elective_courses = [
            self._normalize_module_course(c)
            for c in raw_elective
        ]

        if kind == "모듈":
            normalized_required = []
            normalized_elective = []
            for course in elective_courses:
                if self._module_course_required(course):
                    normalized_required.append(course)
                else:
                    normalized_elective.append(course)
            required_courses = required_courses + normalized_required
            elective_courses = normalized_elective

        return {
            "설명": specialization_data.get("설명", ""),
            required_key: required_courses,
            elective_key: elective_courses,
            "최소이수학점": specialization_data["최소이수학점"],
            "필수학점": specialization_data["필수학점"]
        }

    def _normalize_module_data(self, module_data):
        return self._normalize_specialization_data(module_data, "모듈")

    def _normalize_track_data(self, track_data):
        return self._normalize_specialization_data(track_data, "트랙")

    def get_modules_by_major(self, major):
        if major not in self.majors:
            return {}
        if not self._uses_module(major):
            return {}
        return {
            module_name: self._normalize_module_data(module_data)
            for module_name, module_data in self._get_module_list(major).items()
        }

    def get_tracks_by_major(self, major):
        if major not in self.majors:
            return {}
        if self._uses_module(major):
            return {}
        return {
            track_name: self._normalize_track_data(track_data)
            for track_name, track_data in self._get_track_list(major).items()
        }

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
            if isinstance(course, dict):
                major_courses.append(course)
            else:
                major_courses.append({
                    "name": course,
                    "credit": self.data["학점단위"]["전공필수과목당"]
                })
        # 전공기초 분리 반환
        major_basic = []
        for course in req.get("전공기초", []):
            if isinstance(course, dict):
                major_basic.append(course)
            else:
                major_basic.append({
                    "name": course,
                    "credit": self.data["학점단위"]["전공필수과목당"]
                })

        liberal_courses = []
        for course in req["교양기초필수"]:
            if isinstance(course, dict):
                liberal_courses.append(course)
            else:
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
            if isinstance(course, dict):
                elective_courses.append(course)
            else:
                elective_courses.append({
                    "name": course,
                    "credit": self.data["학점단위"]["전공선택과목당"]
                })

        exploration_required = []
        exploration_electives = []
        exploration_min_credits = 0
        if isinstance(req.get("전공탐색"), dict):
            for course in req["전공탐색"].get("필수", []):
                if isinstance(course, dict):
                    exploration_required.append(course)
                else:
                    exploration_required.append({
                        "name": course,
                        "credit": self.data["학점단위"]["전공선택과목당"]
                    })
            for course in req["전공탐색"].get("선택", []):
                if isinstance(course, dict):
                    exploration_electives.append(course)
                else:
                    exploration_electives.append({
                        "name": course,
                        "credit": self.data["학점단위"]["전공선택과목당"]
                    })
            exploration_min_credits = req["전공탐색"].get("선택최소학점", 0)

        univ_liberal_required = []
        for course in req.get("대학교양필수", []):
            if isinstance(course, dict):
                univ_liberal_required.append(course)
            else:
                univ_liberal_required.append({
                    "name": course,
                    "credit": self.data["학점단위"]["교양과목당"]
                })

        univ_liberal_electives = []
        for course in req.get("대학교양선택", []):
            if isinstance(course, dict):
                univ_liberal_electives.append(course)
            else:
                univ_liberal_electives.append({
                    "name": course,
                    "credit": self.data["학점단위"]["교양과목당"]
                })

        univ_liberal_distribution = req.get("대학교양선택분야", [])
        univ_liberal_dist_min_areas = req.get("대학교양선택최소영역", 0)

        modules = self.get_modules_by_major(major)
        tracks = self.get_tracks_by_major(major)

        return {
            "major_required": major_courses,
            "major_basic": major_basic,
            "liberal_required": liberal_courses,
            "univ_liberal_required": univ_liberal_required,
            "univ_liberal_electives": univ_liberal_electives,
            "univ_liberal_distribution": univ_liberal_distribution,
            "univ_liberal_dist_min_areas": univ_liberal_dist_min_areas,
            "univ_liberal_min_credits": req.get("대학교양선택최소학점", 0),
            "major_electives": elective_courses,
            "exploration_required": exploration_required,
            "exploration_electives": exploration_electives,
            "exploration_min_credits": exploration_min_credits,
            "modules": modules,
            "tracks": tracks
        }

    def get_minimum_route(self, major, completed_courses, selected_module=None, total_credits=0):
        if major not in self.majors:
            return {"error": "존재하지 않는 전공입니다."}

        req = self.majors[major]
        route = []

        for course in req["전공필수"]:
            if isinstance(course, dict):
                course_name = course["name"]
                credit = course["credit"]
            else:
                course_name = course
                credit = self.data["학점단위"]["전공필수과목당"]
            
            if course_name not in completed_courses:
                route.append({
                    "과목명": course_name,
                    "학점": credit,
                    "구분": "전공필수"
                })

        for course in req["교양기초필수"]:
            if isinstance(course, dict):
                course_name = course["name"]
                credit = course["credit"]
            else:
                course_name = course
                if course == "채플":
                    credit = self.data["학점단위"]["채플"]
                else:
                    credit = self.data["학점단위"]["교양과목당"]
            
            if course_name not in completed_courses:
                route.append({
                    "과목명": course_name,
                    "학점": credit,
                    "구분": "교양기초필수"
                })

        # 대학 교양 필수 처리
        univ_required_min = req.get("대학교양선택최소학점", 0)
        univ_elective_courses = req.get("대학교양선택", [])
        completed_univ_elective_credits = 0
        for course in req.get("대학교양필수", []):
            if isinstance(course, dict):
                course_name = course["name"]
                credit = course["credit"]
            else:
                course_name = course
                credit = self.data["학점단위"]["교양과목당"]

            if course_name not in completed_courses:
                route.append({
                    "과목명": course_name,
                    "학점": credit,
                    "구분": "대학교양필수"
                })

        for course in univ_elective_courses:
            course_name = course["name"] if isinstance(course, dict) else course
            credit = course["credit"] if isinstance(course, dict) else self.data["학점단위"]["교양과목당"]
            if course_name in completed_courses:
                completed_univ_elective_credits += credit

        remaining_univ_credits = max(0, univ_required_min - completed_univ_elective_credits)
        if remaining_univ_credits > 0:
            for course in univ_elective_courses:
                course_name = course["name"] if isinstance(course, dict) else course
                credit = course["credit"] if isinstance(course, dict) else self.data["학점단위"]["교양과목당"]
                if course_name not in completed_courses and not any(r["과목명"] == course_name for r in route):
                    route.append({
                        "과목명": course_name,
                        "학점": credit,
                        "구분": "대학교양선택"
                    })
                    remaining_univ_credits -= credit
                    if remaining_univ_credits <= 0:
                        break

        # 전공탐색 처리
        exploration = req.get("전공탐색", {})
        if isinstance(exploration, dict):
            exploration_required = exploration.get("필수", [])
            exploration_electives = exploration.get("선택", [])
            exploration_min = exploration.get("선택최소학점", 0)
            completed_exploration_credits = 0

            for course in exploration_required:
                if isinstance(course, dict):
                    course_name = course["name"]
                    credit = course["credit"]
                else:
                    course_name = course
                    credit = self.data["학점단위"]["전공선택과목당"]

                if course_name not in completed_courses:
                    route.append({
                        "과목명": course_name,
                        "학점": credit,
                        "구분": "전공탐색필수"
                    })

            for course in exploration_electives:
                course_name = course["name"] if isinstance(course, dict) else course
                credit = course["credit"] if isinstance(course, dict) else self.data["학점단위"]["전공선택과목당"]
                if course_name in completed_courses:
                    completed_exploration_credits += credit

            remaining_exploration_credits = max(0, exploration_min - completed_exploration_credits)
            if remaining_exploration_credits > 0:
                for course in exploration_electives:
                    course_name = course["name"] if isinstance(course, dict) else course
                    credit = course["credit"] if isinstance(course, dict) else self.data["학점단위"]["전공선택과목당"]
                    if course_name not in completed_courses and not any(r["과목명"] == course_name for r in route):
                        route.append({
                            "과목명": course_name,
                            "학점": credit,
                            "구분": "전공탐색선택"
                        })
                        remaining_exploration_credits -= credit
                        if remaining_exploration_credits <= 0:
                            break

        # 전공기초 처리
        for course in req.get("전공기초", []):
            if isinstance(course, dict):
                course_name = course["name"]
                credit = course["credit"]
            else:
                course_name = course
                credit = self.data["학점단위"]["전공필수과목당"]

            if course_name not in completed_courses:
                route.append({
                    "과목명": course_name,
                    "학점": credit,
                    "구분": "전공기초"
                })

        if selected_module:
            if self._uses_module(major):
                module_list = self._get_module_list(major)
                if selected_module in module_list:
                    selected_data = self._normalize_module_data(module_list[selected_module])
                    required_courses = selected_data["모듈필수"]
                    elective_courses = selected_data["모듈선택"]
                    min_credits = selected_data["최소이수학점"]
                    label_prefix = "모듈"
                    selected_label = "선택모듈"
            else:
                track_list = self._get_track_list(major)
                if selected_module in track_list:
                    selected_data = self._normalize_track_data(track_list[selected_module])
                    required_courses = selected_data["트랙필수"]
                    elective_courses = selected_data["트랙선택"]
                    min_credits = selected_data["최소이수학점"]
                    label_prefix = "트랙"
                    selected_label = "선택트랙"

            if selected_module in (module_list if self._uses_module(major) else track_list):
                completed_req_names = []
                done_req_credits = 0
                missing_required = []
                for course in required_courses:
                    course_name = course["name"]
                    course_credit = course["credit"]
                    if course_name in completed_courses:
                        completed_req_names.append(course_name)
                        done_req_credits += course_credit
                    else:
                        missing_required.append({"name": course_name, "credit": course_credit})

                added_required = []
                if self._uses_module(major):
                    needed_required_count = max(0, 3 - len(completed_req_names))
                else:
                    needed_required_count = len(missing_required)
                remaining_credits = max(0, 9 - done_req_credits) if self._uses_module(major) else max(0, min_credits - done_req_credits)
                for course in missing_required:
                    if len(added_required) >= needed_required_count and remaining_credits <= 0:
                        break
                    added_required.append(course)
                    remaining_credits -= course["credit"]

                for course in added_required:
                    if not any(r["과목명"] == course["name"] for r in route):
                        route.append({
                            "과목명": course["name"],
                            "학점": course["credit"],
                            "구분": f"{label_prefix}필수({selected_module})"
                        })

                if remaining_credits > 0:
                    for course in elective_courses:
                        course_name = course["name"]
                        course_credit = course["credit"]
                        if course_name not in completed_courses and not any(r["과목명"] == course_name for r in route):
                            route.append({
                                "과목명": course_name,
                                "학점": course_credit,
                                "구분": f"{label_prefix}선택({selected_module})",
                                "비고": "학점 충족용 (여러 과목 중 선택 가능)"
                            })
                            remaining_credits -= course_credit
                            if remaining_credits <= 0:
                                break

        total_courses = len(route)

        # 총이수학점 - 현재이수학점 = 남은학점
        needed_total = req["총이수학점"]
        remaining_total = max(0, needed_total - total_credits)

        grouped = {}
        for r in route:
            key = r["구분"]
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)

        return {
            "총과목수": total_courses,
            "총학점": remaining_total,
            "선택모듈": selected_module,
            "grouped": grouped,
            "route": route
        }

    def recommend_modules(self, major, completed_courses):
        if major not in self.majors:
            return {"error": "존재하지 않는 전공입니다."}

        if self._uses_module(major):
            specialization_list = self._get_module_list(major)
        else:
            specialization_list = self._get_track_list(major)

        if not specialization_list:
            return {"modules": [], "tracks": [], "message": "해당 전공에는 추천할 항목이 없습니다."}

        results = []

        kind = "모듈" if self._uses_module(major) else "트랙"
        for module_name, module_data in specialization_list.items():
            spec = self._normalize_specialization_data(module_data, kind)
            m_required = spec[f"{kind}필수"]
            m_elective = spec[f"{kind}선택"]
            m_min = spec["최소이수학점"]

            completed_req = []
            missing_req = []
            completed_elec = []
            missing_elec = []
            done_credits = 0

            for course in m_required:
                course_name = course["name"]
                course_credit = course["credit"]
                if course_name in completed_courses:
                    completed_req.append(course_name)
                    done_credits += course_credit
                else:
                    missing_req.append(course_name)

            for course in m_elective:
                course_name = course["name"]
                course_credit = course["credit"]
                if course_name in completed_courses:
                    completed_elec.append(course_name)
                    done_credits += course_credit
                else:
                    missing_elec.append(course_name)

            remaining_credits = max(0, m_min - done_credits)
            pct = min(100, round((done_credits / m_min) * 100)) if m_min > 0 else 100
            # 추천 기준: 모듈의 이수학점이 9학점 이상이면 필수충족으로 간주
            req_done = done_credits >= 9

            result_item = {
                f"{kind}명": module_name,
                "설명": module_data.get("설명", ""),
                "달성률": pct,
                "이수학점": done_credits,
                "필요학점": m_min,
                "잔여학점": remaining_credits,
                f"{kind}필수_완료": completed_req,
                f"{kind}필수_미이수": missing_req,
                f"{kind}선택_완료": completed_elec,
                f"{kind}선택_미이수": missing_elec,
                "필수충족": req_done,
                "이수완료": req_done
            }
            results.append(result_item)

        results.sort(key=lambda x: (-x["달성률"], -x["이수학점"]))

        if self._uses_module(major):
            return {"modules": results, "tracks": []}
        return {"modules": [], "tracks": results}

    def recommend_tracks(self, major, completed_courses):
        return self.recommend_modules(major, completed_courses)

    def check(
        self,
        major,
        completed_courses,
        total_credits,
        foreign_lang_cert,
        info_cert,
        selected_module=None,
        selected_track=None
    ):
        if major not in self.majors:
            return {"error": "존재하지 않는 전공입니다."}

        if not selected_module:
            selected_module = selected_track

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
        completed_required = [
            c["name"] if isinstance(c, dict) else c
            for c in required_courses
            if (c["name"] if isinstance(c, dict) else c) in completed_courses
        ]
        missing_required = [
            c["name"] if isinstance(c, dict) else c
            for c in required_courses
            if (c["name"] if isinstance(c, dict) else c) not in completed_courses
        ]
        result["전공필수"] = {
            "전체": required_courses,
            "이수완료": completed_required,
            "미이수": missing_required,
            "충족": len(missing_required) == 0
        }

        # 전공기초 처리
        basic_courses = req.get("전공기초", [])
        completed_basic = [
            c["name"] if isinstance(c, dict) else c
            for c in basic_courses
            if (c["name"] if isinstance(c, dict) else c) in completed_courses
        ]
        missing_basic = [
            c["name"] if isinstance(c, dict) else c
            for c in basic_courses
            if (c["name"] if isinstance(c, dict) else c) not in completed_courses
        ]
        result["전공기초"] = {
            "전체": basic_courses,
            "이수완료": completed_basic,
            "미이수": missing_basic,
            "충족": len(missing_basic) == 0
        }

        liberal_courses = req["교양기초필수"]
        completed_liberal = [
            c["name"] if isinstance(c, dict) else c
            for c in liberal_courses
            if (c["name"] if isinstance(c, dict) else c) in completed_courses
        ]
        missing_liberal = [
            c["name"] if isinstance(c, dict) else c
            for c in liberal_courses
            if (c["name"] if isinstance(c, dict) else c) not in completed_courses
        ]
        result["교양기초"] = {
            "전체": liberal_courses,
            "이수완료": completed_liberal,
            "미이수": missing_liberal,
            "충족": len(missing_liberal) == 0
        }

        # 대학 교양 처리
        univ_required_courses = req.get("대학교양필수", [])
        completed_univ_required = [
            c["name"] if isinstance(c, dict) else c
            for c in univ_required_courses
            if (c["name"] if isinstance(c, dict) else c) in completed_courses
        ]
        missing_univ_required = [
            c["name"] if isinstance(c, dict) else c
            for c in univ_required_courses
            if (c["name"] if isinstance(c, dict) else c) not in completed_courses
        ]

        univ_elective_courses = req.get("대학교양선택", [])
        completed_univ_elective = [
            c["name"] if isinstance(c, dict) else c
            for c in univ_elective_courses
            if (c["name"] if isinstance(c, dict) else c) in completed_courses
        ]
        completed_univ_elective_credits = sum(
            (c["credit"] if isinstance(c, dict) else self.data["학점단위"]["교양과목당"])
            for c in univ_elective_courses
            if (c["name"] if isinstance(c, dict) else c) in completed_courses
        )
        univ_min_credits = req.get("대학교양선택최소학점", 0)
        result["대학교양"] = {
            "필수": {
                "전체": univ_required_courses,
                "이수완료": completed_univ_required,
                "미이수": missing_univ_required,
                "충족": len(missing_univ_required) == 0
            },
            "선택": {
                "전체": univ_elective_courses,
                "이수완료": completed_univ_elective,
                "이수학점": completed_univ_elective_credits,
                "필요학점": univ_min_credits,
                "충족": completed_univ_elective_credits >= univ_min_credits,
                "부족": max(0, univ_min_credits - completed_univ_elective_credits)
            },
            "충족": len(missing_univ_required) == 0 and completed_univ_elective_credits >= univ_min_credits
        }

        exploration_data = req.get("전공탐색", {})
        if isinstance(exploration_data, dict):
            exploration_required_courses = exploration_data.get("필수", [])
            exploration_elective_courses = exploration_data.get("선택", [])
            exploration_min_credits = exploration_data.get("선택최소학점", 0)

            completed_exploration_required = [
                c["name"] if isinstance(c, dict) else c
                for c in exploration_required_courses
                if (c["name"] if isinstance(c, dict) else c) in completed_courses
            ]
            missing_exploration_required = [
                c["name"] if isinstance(c, dict) else c
                for c in exploration_required_courses
                if (c["name"] if isinstance(c, dict) else c) not in completed_courses
            ]
            completed_exploration_elective = [
                c["name"] if isinstance(c, dict) else c
                for c in exploration_elective_courses
                if (c["name"] if isinstance(c, dict) else c) in completed_courses
            ]
            completed_exploration_credits = sum(
                (c["credit"] if isinstance(c, dict) else self.data["학점단위"]["전공선택과목당"])
                for c in exploration_elective_courses
                if (c["name"] if isinstance(c, dict) else c) in completed_courses
            )
            result["전공탐색"] = {
                "필수": {
                    "전체": exploration_required_courses,
                    "이수완료": completed_exploration_required,
                    "미이수": missing_exploration_required,
                    "충족": len(missing_exploration_required) == 0
                },
                "선택": {
                    "전체": exploration_elective_courses,
                    "이수완료": completed_exploration_elective,
                    "이수학점": completed_exploration_credits,
                    "필요학점": exploration_min_credits,
                    "충족": completed_exploration_credits >= exploration_min_credits,
                    "부족": max(0, exploration_min_credits - completed_exploration_credits)
                },
                "충족": len(missing_exploration_required) == 0 and completed_exploration_credits >= exploration_min_credits
            }

        elective_courses = req.get("전공선택", [])
        elective_course_names = [
            c["name"] if isinstance(c, dict) else c
            for c in elective_courses
        ]
        completed_elective = [c for c in elective_course_names if c in completed_courses]
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

        module_result = None
        track_result = None
        module_satisfied = True
        track_satisfied = True

        if selected_module:
            # 간호학과는 모듈, 그 외는 트랙으로 처리
            if self._uses_module(major):
                module_list = self._get_module_list(major)
                if selected_module in module_list:
                    module_data = self._normalize_module_data(module_list[selected_module])
                    m_required = module_data["모듈필수"]
                    m_min = module_data["최소이수학점"]

                    completed_m_req = []
                    missing_m_req = []
                    completed_m_elec = []
                    missing_m_elec = []
                    m_req_credits_done = 0

                    for course in m_required:
                        course_name = course["name"]
                        course_credit = course["credit"]
                        if course_name in completed_courses:
                            completed_m_req.append(course_name)
                            m_req_credits_done += course_credit
                        else:
                            missing_m_req.append(course_name)

                    for course in module_data["모듈선택"]:
                        course_name = course["name"]
                        course_credit = course["credit"]
                        if course_name in completed_courses:
                            completed_m_elec.append(course_name)
                            m_req_credits_done += course_credit
                        else:
                            missing_m_elec.append(course_name)

                    # 간호 모듈 충족 기준: 모듈 총 누적 이수학점이 9학점 이상이면 충족
                    module_satisfied = m_req_credits_done >= 9

                    module_result = {
                        "선택모듈": selected_module,
                        "설명": module_data.get("설명", ""),
                        "모듈필수": {
                            "전체": m_required,
                            "이수완료": completed_m_req,
                            "미이수": missing_m_req,
                            "충족": module_satisfied
                        },
                        "모듈선택": {
                            "전체": module_data["모듈선택"],
                            "이수완료": completed_m_elec,
                            "미이수": missing_m_elec,
                            "충족": module_satisfied
                        },
                        "총이수학점": m_req_credits_done,
                        "필요최소학점": m_min,
                        "충족": module_satisfied
                    }
                    # 간호학과 모듈 특례: 이수요건 충족 여부로 이수증 발급 가능 표시
                    module_result["이수증발급가능"] = bool(module_satisfied)
                    module_result["이수증메시지"] = ("원주간호대학장 명의 이수증 발급 가능" if module_satisfied
                                                     else "원주간호대학장 명의 이수증 미발급: 모듈 이수요건 미충족")
            else:
                track_list = self._get_track_list(major)
                if selected_module in track_list:
                    track_data = self._normalize_track_data(track_list[selected_module])
                    t_required = track_data.get("트랙필수", [])
                    t_min = track_data.get("최소이수학점", 0)

                    completed_t_req = []
                    missing_t_req = []
                    t_credits_done = 0

                    for course in t_required:
                        course_name = course["name"]
                        course_credit = course["credit"]
                        if course_name in completed_courses:
                            completed_t_req.append(course_name)
                            t_credits_done += course_credit
                        else:
                            missing_t_req.append(course_name)

                    # 트랙 충족 여부: 필수과목 모두 완료 또는 최소 이수학점 충족
                    track_satisfied = (len(missing_t_req) == 0) or (t_credits_done >= track_data.get("필수학점", 0)) or (t_credits_done >= t_min)

                    track_result = {
                        "선택트랙": selected_module,
                        "설명": track_data.get("설명", ""),
                        "트랙필수": {
                            "전체": t_required,
                            "이수완료": completed_t_req,
                            "미이수": missing_t_req,
                            "충족": track_satisfied
                        },
                        "총이수학점": t_credits_done,
                        "필요최소학점": t_min,
                        "충족": track_satisfied
                    }

        result["모듈"] = module_result
        result["트랙"] = track_result

        # include major name for frontend conditional rendering
        result["전공명"] = major

        result["졸업인증"] = {
            "외국어인증": {"취득": foreign_lang_cert, "충족": foreign_lang_cert},
            "정보/산업실무역량인증": {"취득": info_cert, "충족": info_cert},
            "충족": foreign_lang_cert and info_cert
        }

        if self._uses_module(major) and "대학교양" in result:
            checks = [
                result["총이수학점"]["충족"],
                result["전공필수"]["충족"],
                result["전공기초"]["충족"],
                result["교양기초"]["충족"],
                result["대학교양"]["충족"],
                result["졸업인증"]["충족"]
            ]
        elif self._uses_module(major):
            checks = [
                result["총이수학점"]["충족"],
                result["전공필수"]["충족"],
                result["전공기초"]["충족"],
                result["교양기초"]["충족"],
                result["졸업인증"]["충족"]
            ]
        else:
            checks = [
                result["총이수학점"]["충족"],
                result["전공필수"]["충족"],
                result["전공기초"]["충족"],
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
