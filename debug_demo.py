"""
Student report: a small script with four intentional bugs, for practising debugging.

    python debug_demo.py                  run the fixed versions (plus regression checks)
    python debug_demo.py --buggy          run the buggy versions
    python debug_demo.py --buggy --no-catch
                                          let the first crash escape, so that
                                          `python -m pdb` stops at it (post-mortem)

Each bug is marked "# BUG n:". The buggy line runs only with --buggy; the fix
sits next to it, with the original buggy line kept as a comment.
Logs go to debug.log (next to this file), so app.log from task1.py is left alone.
"""

import bdb
import logging
import os
import sys

from exceptions import ConversionError
from task1 import LOG_FORMAT, RESULTS, check, strict_int

logger = logging.getLogger("debug_demo")

BUGGY = "--buggy" in sys.argv
NO_CATCH = "--no-catch" in sys.argv

STUDENTS = [
    {"name": "Ali", "age": 21, "scores": ["85", "92", "78"]},
    {"name": "Sara", "age": 22, "scores": ["90", "88", "n/a"]},   # "n/a" is a bad score
    {"name": "Omar", "age": 20, "scores": ["70", "65", "80"]},
]


def student_label(record):
    """'Ali (age 21)'"""
    if BUGGY:
        age = record["agee"]           # BUG 1: misspelt key -> KeyError
    else:
        # BUG 1 fixed. Original buggy line:
        # age = record["agee"]
        age = record["age"]
    return f"{record['name']} (age {age})"


def find_student(students, name):
    """Return the student called `name`, or None if there isn't one."""
    for student in students:
        if student["name"] == name:
            return student
    return None


def report_card(students, name):
    """Call 1 of 3: look the student up and build their report."""
    student = find_student(students, name)
    if BUGGY:
        return build_report(student)   # BUG 2: student may be None, and nobody checks
    # BUG 2 fixed: check for None here, where it appears, instead of letting it
    # travel down two more calls and crash far away from the real cause.
    # Original buggy line:
    # return build_report(student)
    if student is None:
        logger.warning("report_card: no student named %r", name)
        return f"No student named {name!r}"
    return build_report(student)


def build_report(student):
    """Call 2 of 3."""
    return "Report: " + format_scores(student)


def format_scores(student):
    """Call 3 of 3: this is where a None student finally crashes."""
    raw_scores = student["scores"]
    scores = convert_scores(raw_scores)
    return f"{student['name']}: scores {scores}, average {average(scores)}"


def average(scores):
    """Mean of a list of numbers, rounded to 2 places."""
    total = 0
    if BUGGY:
        for i in range(1, len(scores)):    # BUG 3: starts at 1, so scores[0] is skipped
            total += scores[i]
    else:
        # BUG 3 fixed. Original buggy line:
        # for i in range(1, len(scores)):
        for i in range(len(scores)):
            total += scores[i]
    return round(total / len(scores), 2)


def convert_scores(raw_scores):
    """Turn score strings into ints. Bad scores are skipped."""
    scores = []
    for raw in raw_scores:
        if BUGGY:
            try:
                scores.append(int(raw))
            except Exception:          # BUG 4: hides the failed conversion completely
                pass
        else:
            # BUG 4 fixed. Original buggy lines:
            # except Exception:
            #     pass
            # Catch only the error we expect, and log it, so a bad score is visible.
            try:
                score = strict_int(raw)
            except ConversionError as e:
                logger.warning("convert_scores: skipping bad score %r (%s)", raw, e)
            else:
                scores.append(score)
    return scores


def run_step(title, func, *args):
    """Run one demo step. A crash is logged with its full traceback, and the
    next steps still run (unless --no-catch is given)."""
    print(f"\n--- {title} ---")
    try:
        result = func(*args)
    except bdb.BdbQuit:
        # Typing `q` in pdb raises BdbQuit, which is an Exception too.
        # It isn't a crash, so let it through instead of logging it below.
        raise
    except Exception:
        logger.exception("%s crashed", title)
        if NO_CATCH:
            raise                      # let python -m pdb stop at the crash
        print("  CRASHED (the full stack trace is in debug.log)")
    else:
        print(f"  {result}")


def run_regression_checks():
    """One check per bug, reusing task1's check() so the output looks the same."""
    print("\n=== Regression checks ===")
    check("BUG 1: student_label uses the right key", student_label(STUDENTS[0]), "Ali (age 21)")
    check("BUG 2: unknown name gives a message, not a crash",
          report_card(STUDENTS, "Zara"), "No student named 'Zara'")
    check("BUG 3: average counts the first score", average([85, 92, 78]), 85.0)
    records = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = ListHandler()
    logger.addHandler(handler)
    try:
        scores = convert_scores(["90", "88", "n/a"])
    finally:
        logger.removeHandler(handler)
    check("BUG 4: good scores are kept", scores, [90, 88])
    check("BUG 4: the bad score is logged as a WARNING",
          [r.levelname for r in records], ["WARNING"])
    total = RESULTS["passed"] + RESULTS["failed"]
    print(f"\n=== Regression checks: {RESULTS['passed']}/{total} passed ===")
    return RESULTS["failed"] == 0


def setup_logging():
    """Everything goes to debug.log; WARNING and above also go to the console."""
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT,
                        handlers=[file_handler, console_handler])


def main():
    setup_logging()
    mode = "BUGGY" if BUGGY else "FIXED"
    logger.info("debug_demo started in %s mode", mode)
    print(f"=== Student report ({mode} versions) ===")
    run_step("Bug 1: label for Ali", student_label, STUDENTS[0])
    run_step("Bug 2: report card for 'Zara' (a typo for Sara)", report_card, STUDENTS, "Zara")
    run_step("Bug 3: average([85, 92, 78]), expected 85.0", average, [85, 92, 78])
    run_step("Bug 4: convert Sara's scores ['90', '88', 'n/a']", convert_scores, STUDENTS[1]["scores"])
    ok = True
    if not BUGGY:
        ok = run_regression_checks()
    logger.info("debug_demo finished")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
