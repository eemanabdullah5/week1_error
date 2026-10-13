# Debugging Notes: Exception Handling and Debugging (Week 1)

`debug_demo.py` is a small student-report script with four intentional bugs.
Each one is marked `# BUG n:` in the code. The buggy line runs only with `--buggy`,
and the fix sits next to it with the original line kept as a comment.
Every transcript quoted below is saved in full in `evidence/`.

---

## Bug 1: KeyError from a misspelt dict key

**Symptom:** `student_label()` crashes as soon as it runs.

**Stack trace (shortened)** (`evidence/buggy_run.txt`, `evidence/buggy_debug.log`):
```text
File "debug_demo.py", line 123, in run_step
    result = func(*args)
File "debug_demo.py", line 38, in student_label
    age = record["agee"]           # BUG 1: misspelt key -> KeyError
KeyError: 'agee'
```

**Breakpoint used:** a post-mortem session (`evidence/pdb_postmortem_bug1.txt`).
`python -m pdb debug_demo.py --buggy --no-catch` lets the crash escape, so pdb stops
on the exact line that failed (line 38), with every variable still available.
```text
(Pdb) p record
{'name': 'Ali', 'age': 21, 'scores': ['85', '92', '78']}
(Pdb) p list(record)
['name', 'age', 'scores']
```

**Root cause:** The code asks for `"agee"`, but the dict's key is `"age"`. `p list(record)` shows the real keys.

**Fix:** `age = record["age"]`

**Regression test:** `BUG 1: student_label uses the right key` checks that it returns `'Ali (age 21)'`.

---

## Bug 2: None passed down 3 function calls

**Symptom:** `report_card(STUDENTS, "Zara")` crashes with a `TypeError` inside
`format_scores()`, two calls away from the real mistake.

**Stack trace (shortened):**
```text
File "debug_demo.py", line 58, in report_card
    return build_report(student)   # BUG 2: student may be None, and nobody checks
File "debug_demo.py", line 71, in build_report
    return "Report: " + format_scores(student)
File "debug_demo.py", line 76, in format_scores
    raw_scores = student["scores"]
TypeError: 'NoneType' object is not subscriptable
```

**Breakpoint used:** `b 76` (the crashing line). Full session in `evidence/pdb_bug2.txt`.
```text
(Pdb) p student
None
(Pdb) w          # shows report_card -> build_report -> format_scores
(Pdb) up
(Pdb) up         # now inside report_card, where the None came from
(Pdb) p name
'Zara'
(Pdb) p find_student(students, name)
None
```

**Root cause:** `find_student()` returns `None` for a name that doesn't exist ("Zara" is a typo for "Sara").
`report_card()` never checks for that. It passes the `None` down to `build_report()` and then
`format_scores()`, which only crashes when it finally tries `None["scores"]`.
The crash line isn't where the bug is. Going `up` the stack finds where the `None` came from.

**Fix:** `report_card()` checks `if student is None:` right after the lookup. It logs a
WARNING and returns `"No student named 'Zara'"`.

**Regression test:** `BUG 2: unknown name gives a message, not a crash`.

---

## Bug 3: Off-by-one loop gives a wrong average (no crash)

**Symptom:** `average([85, 92, 78])` returns **56.67** instead of **85.0**.
Nothing crashes, so there's no stack trace. The only clue is the wrong number in
`evidence/buggy_run.txt`.

**Breakpoint used:** `b 86` (inside the loop). Full session in `evidence/pdb_bug3.txt`.
```text
(Pdb) p i, scores[i], total
(1, 92, 0)            # first time round, i is already 1, so 85 was never added
(Pdb) p list(range(1, len(scores)))
[1, 2]                # index 0 is missing
(Pdb) c
(Pdb) p i, scores[i], total
(2, 78, 92)
```

**Root cause:** `range(1, len(scores))` starts at 1, but list indexes start at 0, so
the first score is skipped. The total is still divided by 3, so the result is (92 + 78) / 3 = 56.67.

**Fix:** `for i in range(len(scores)):`

**Regression test:** `BUG 3: average counts the first score` checks that `average([85, 92, 78]) == 85.0`.

**Also debugged in VS Code:** `evidence/vscode_bug2.png` (paused on line 76, `student = None`,
full call stack) and `evidence/vscode_bug3.png` (paused on line 86, `i = 1` on the first pass).

---

## Bug 4: `except Exception: pass` silently hides a failed conversion

**Symptom:** Sara's scores `['90', '88', 'n/a']` become `[90, 88]` with no message at all.
The bad score just disappears, and nobody would know it was ever there.
There's no crash and no stack trace, because the error is caught and thrown away.

**Breakpoint used:** a conditional breakpoint, `b 101, raw == "n/a"`, that only stops on
the bad value. Full session in `evidence/pdb_bug4.txt` (an extra file, not in the original list).
```text
(Pdb) p raw, scores
('n/a', [90, 88])
(Pdb) n
ValueError: invalid literal for int() with base 10: 'n/a'    # the error IS raised...
(Pdb) n
-> except Exception:          # BUG 4 ...                    # ...and swallowed here
(Pdb) p scores
[90, 88]
```

**Root cause:** `except Exception: pass` catches *every* error and does nothing with it.
Problems like this are the hardest to find, because nothing looks wrong.

**Fix:** Use `strict_int(raw)` and catch only the error we expect, `ConversionError`.
Log a WARNING naming the bad value, then skip it on purpose:
```text
WARNING  convert_scores:112  convert_scores: skipping bad score 'n/a' (cannot convert 'n/a' to int)
```

**Regression tests:** `BUG 4: good scores are kept` and
`BUG 4: the bad score is logged as a WARNING`. The second one attaches a temporary
list-collecting handler and checks that exactly one WARNING was logged.

---

## A lesson found while capturing the evidence

The first pdb transcripts showed a fake crash: `bdb.BdbQuit` logged as `Bug 2 ... crashed`.
Typing `q` in pdb raises `BdbQuit`, and `BdbQuit` is an `Exception`, so the
`except Exception:` in `run_step()` caught it and logged it as a crash. That's a small version of
bug 4: a broad `except` catches things it was never meant to. Fix: an
`except bdb.BdbQuit: raise` before the broad `except` in `run_step()`.

---

## Logging levels used

| Level | Used for | Example |
|---|---|---|
| `DEBUG` | Normal fallbacks and internal details | `int('12.9') failed (...); trying int(float())` |
| `INFO` | Milestones | `tests started`, `parse_key_value_string: parsed 4 pair(s)`, `tests finished: 167 passed, 0 failed` |
| `WARNING` | Bad input handled safely | `safe_float: 'abc' is not a usable number; returning default None`, `parse_key_value_string: skipping 'bad' (no ':')` |
| `ERROR` | An operation failed | `test run failed: ...` in `run_tests()`, when a test fails |
| `logger.exception` | Inside `except` blocks, when the full traceback is wanted (logged at ERROR) | `test run crashed` in `run_tests()`; `Bug 1: label for Ali crashed` in `debug_demo.py` |

- `app.log` (from `task1.py`) and `debug.log` (from `debug_demo.py`) get DEBUG and above.
- During the test run (`task1.py`), the console only shows ERROR and above, so the test output
  stays clean. The warnings from tests that feed bad input on purpose go to `app.log`, and a small
  counting handler (`WarningCounter`) prints how many there were after the summary:
  `=== 42 warnings logged to app.log (expected: tests feed bad input on purpose) ===`.
- `debug_demo.py` still shows WARNING and above on the console, because there each warning
  is the point of the demo (for example, the skipped `'n/a'` score in bug 4).
- Logging is configured once, in each script's `if __name__ == "__main__":` code, so importing
  `task1` never changes the importer's logging setup.
- Messages use lazy `%` formatting (`logger.warning("bad value %r", value)`).
- Long values (such as `10**1000`) and long error messages are cut with `short_repr()` /
  `short_text()` from `exceptions.py`, so a log line never contains hundreds of digits.
- `app.log` has no ERROR lines in a passing run. That's expected: ERROR is only logged when tests fail
  or crash. The ERROR + traceback examples are in `evidence/buggy_debug.log`.

## Custom exceptions

All are in `exceptions.py`.

| Class | Parent classes | When raised |
|---|---|---|
| `DataProcessingError` | `Exception` | Never directly. It's the base class, so `except DataProcessingError` catches all of the classes below |
| `ConversionError` | `DataProcessingError`, `ValueError` | A value can't be converted: `strict_int("abc")`, `to_bool("maybe")`. Has `.value` and `.target`; `strict_int` chains the original error with `raise ... from e` |
| `SchemaError` | `DataProcessingError`, `TypeError` | `normalize_record()` is given a schema type it can't convert to, such as `list` |
| `ParseError` | `DataProcessingError`, `ValueError` | `parse_key_value_string(..., strict=True)` finds a pair with no separator or an empty key |

Each one also inherits from the built-in error that was raised before (`ValueError` / `TypeError`),
so all of the existing tests and `except` blocks that catch those still work.

## How to run

From inside `week1_errors/`:

```powershell
python task1.py                     # all tests (167); writes app.log
python debug_demo.py                # fixed versions + regression checks; writes debug.log
python debug_demo.py --buggy        # buggy versions; each crash is logged with its traceback
python -m pdb debug_demo.py --buggy --no-catch    # post-mortem: pdb stops at bug 1's crash
```

Piping pdb commands in Windows PowerShell 5.1, as used for the evidence files:

```powershell
$utf8 = New-Object Text.UTF8Encoding $false
[Console]::OutputEncoding = $utf8; [Console]::InputEncoding = $utf8; $OutputEncoding = $utf8
$env:PYTHONIOENCODING = 'utf-8'
@'
b 76
c
p student
w
q
'@ | python -m pdb debug_demo.py --buggy
```

Three Windows PowerShell 5.1 traps to know about:
- Without the BOM-less UTF-8 lines above, PowerShell puts an invisible BOM (`U+FEFF`) in front of
  the first piped command, and pdb rejects it as a `SyntaxError`.
- Redirected output (`python task1.py > out.txt`) uses the old Windows code page, which can't
  encode characters like `α`, so the original script crashed with `UnicodeEncodeError`.
  `task1.py` now calls `sys.stdout.reconfigure(encoding="utf-8")` in its `__main__` block, so
  redirecting works without `PYTHONIOENCODING`. (`debug_demo.py` prints only ASCII, so it
  doesn't need this.)
- `>` in a stock PowerShell 5.1 saves files as UTF-16.
  So the evidence files were written with `[IO.File]::WriteAllLines` instead, which gives UTF-8.
