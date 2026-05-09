from grader import grade_cv
from roaster import roast_cv


def run_pipeline(cv_text: str, industry: str) -> dict:
    grade = grade_cv(cv_text, industry)
    roast = roast_cv(cv_text, grade)

    return {
        "overall_score": grade["overall_score"],
        "section_scores": grade["section_scores"],
        "issues": grade["issues"],
        "priority_fixes": grade["priority_fixes"],
        "roast": roast,
    }
