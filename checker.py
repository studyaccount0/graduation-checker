import json

# =============================================
# 졸업요건 체커 - checker.py
# 연세대 미래캠퍼스 졸업요건 자동 계산기
# =============================================

class GraduationChecker:
    def __init__(self, data_path="graduation_data.json"):
        """졸업요건 데이터 로드"""
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.majors = self.data["전공목록"]

    def get_major_list(self):
        """전공 목록 반환"""
        return list(self.majors.keys())

    def check(self, major: str, completed_courses: list, total_credits: int,
              foreign_lang_cert: bool, info_cert: bool) -> dict:
        """
        졸업요건 충족 여부 계산

        Args:
            major: 전공명 (예: "소프트웨어학부")
            completed_courses: 이수한 과목명 리스트
            total_credits: 총 이수학점
            foreign_lang_cert: 외국어인증 취득 여부
            info_cert: 정보인증 or 산업실무역량인증 취득 여부

        Returns:
            결과 딕셔너리
        """
        if major not in self.majors:
            return {"error": f"'{major}' 전공을 찾을 수 없습니다."}

        req = self.majors[major]
        result = {}

        # 1. 총 이수학점 확인
        needed_credits = req["총이수학점"]
        result["총이수학점"] = {
            "필요": needed_credits,
            "현재": total_credits,
            "충족": total_credits >= needed_credits,
            "부족": max(0, needed_credits - total_credits)
        }

        # 2. 전공필수 과목 확인
        required_courses = req["전공필수"]
        completed_required = [c for c in required_courses if c in completed_courses]
        missing_required = [c for c in required_courses if c not in completed_courses]

        result["전공필수"] = {
            "전체": required_courses,
            "이수완료": completed_required,
            "미이수": missing_required,
            "충족": len(missing_required) == 0
        }

        # 3. 교양기초 과목 확인
        lib_courses = req["교양기초필수"]
        completed_lib = [c for c in lib_courses if c in completed_courses]
        missing_lib = [c for c in lib_courses if c not in completed_courses]

        result["교양기초"] = {
            "전체": lib_courses,
            "이수완료": completed_lib,
            "미이수": missing_lib,
            "충족": len(missing_lib) == 0
        }

        # 4. 졸업인증 확인
        result["졸업인증"] = {
            "외국어인증": {
                "필요": True,
                "취득": foreign_lang_cert,
                "충족": foreign_lang_cert
            },
            "정보/산업실무역량인증": {
                "필요": True,
                "취득": info_cert,
                "충족": info_cert
            },
            "충족": foreign_lang_cert and info_cert
        }

        # 5. 전체 충족 여부 & 달성률 계산
        checks = [
            result["총이수학점"]["충족"],
            result["전공필수"]["충족"],
            result["교양기초"]["충족"],
            result["졸업인증"]["충족"]
        ]
        fulfilled = sum(checks)
        result["전체달성률"] = round((fulfilled / len(checks)) * 100)
        result["졸업가능"] = all(checks)

        return result


def print_result(major: str, result: dict):
    """결과를 보기 좋게 출력"""
    print("\n" + "=" * 50)
    print(f"  📋 {major} 졸업요건 확인 결과")
    print("=" * 50)

    if "error" in result:
        print(f"❌ 오류: {result['error']}")
        return

    # 총 이수학점
    r = result["총이수학점"]
    status = "✅" if r["충족"] else "❌"
    print(f"\n{status} 총 이수학점: {r['현재']} / {r['필요']}학점", end="")
    if not r["충족"]:
        print(f"  (부족: {r['부족']}학점)", end="")
    print()

    # 전공필수
    r = result["전공필수"]
    status = "✅" if r["충족"] else "❌"
    print(f"\n{status} 전공필수 과목")
    print(f"   이수완료: {', '.join(r['이수완료']) if r['이수완료'] else '없음'}")
    if r["미이수"]:
        print(f"   미이수:   {', '.join(r['미이수'])}")

    # 교양기초
    r = result["교양기초"]
    status = "✅" if r["충족"] else "❌"
    print(f"\n{status} 교양기초 과목")
    if r["미이수"]:
        print(f"   미이수: {', '.join(r['미이수'])}")
    else:
        print(f"   모두 이수 완료!")

    # 졸업인증
    r = result["졸업인증"]
    status = "✅" if r["충족"] else "❌"
    print(f"\n{status} 졸업인증")
    fl = "✅" if r["외국어인증"]["취득"] else "❌"
    ic = "✅" if r["정보/산업실무역량인증"]["취득"] else "❌"
    print(f"   외국어인증: {fl}")
    print(f"   정보/산업실무역량인증: {ic}")

    # 최종 결과
    print("\n" + "-" * 50)
    print(f"  🎓 전체 달성률: {result['전체달성률']}%")
    if result["졸업가능"]:
        print("  ✅ 졸업 가능합니다!")
    else:
        print("  ❌ 아직 충족하지 못한 요건이 있습니다.")
    print("=" * 50 + "\n")


# =============================================
# 테스트 실행
# =============================================
if __name__ == "__main__":
    checker = GraduationChecker("graduation_data.json")

    # 사용 예시: 소프트웨어학부 학생
    my_major = "소프트웨어학부"

    my_courses = [
        "컴퓨팅사고", "파이썬프로그래밍", "자료구조", "알고리즘",
        "채플", "기독교의이해", "글쓰기", "교양영어Ⅰ", "교양영어Ⅱ",
        "리더십개발", "리더십실습", "대학학문의세계", "진로지도", "경력개발"
    ]

    result = checker.check(
        major=my_major,
        completed_courses=my_courses,
        total_credits=85,
        foreign_lang_cert=True,
        info_cert=False
    )

    print_result(my_major, result)

    # 전공 목록 출력
    print("📚 지원 전공 목록:")
    for m in checker.get_major_list():
        print(f"  - {m}")
