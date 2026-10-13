"""
Week 1 - Python Syntax, Data Types and Functions
================================================

Covers:
  * Built-in data types: int, float, str, bool, None, list, tuple, set, dict
  * Functions that process lists, dictionaries and strings
  * Safe type conversion with error handling
  * Executed test cases with multiple inputs (run: python week1_python_basics.py)

Version 3: bug fixes from review, each with a regression test (see run_tests):
  1. unique_preserve_order handles unhashable items (lists, dicts)
  2. invert_dict handles unhashable values (lists, dicts, sets)
  3. safe_int returns default instead of raising OverflowError ("1e309")
  4. caesar_cipher shifts only ASCII A-Z / a-z
  Earlier review items, also fixed:
  5. Booleans are not treated as numbers (safe_int, safe_float, clean_numbers, merge_dicts)
  6. to_snake_case splits acronyms ("HTTPRequest" -> "http_request")
  7. normalize_record catches TypeError as well as ValueError
  Other edge cases found while testing:
  8. safe_float rejects NaN/infinity and misplaced commas ("1,2,3")
  9. parse_key_value_string no longer crashes on "1,000", "--5" or "²"
 10. word_frequency keeps contractions together ("don't")
 11. flatten detects a list that contains itself
 12. chunk checks its size and accepts generators
 13. String functions raise a clear TypeError for non-string input
"""

import math
import re
from collections import Counter


# ---------------------------------------------------------------------------
# 1. Data-type review
# ---------------------------------------------------------------------------

def describe_types():
    """Return one example of each built-in type with its type name."""
    samples = [
        42,                      # int
        3.14,                    # float
        2 + 3j,                  # complex
        "hello",                 # str
        True,                    # bool
        None,                    # NoneType
        [1, 2, 3],               # list    (mutable, ordered)
        (1, 2, 3),               # tuple   (immutable, ordered)
        {1, 2, 3},               # set     (mutable, unordered, unique)
        frozenset({1, 2}),       # frozenset (immutable set)
        {"a": 1},                # dict    (key -> value mapping)
        b"bytes",                # bytes
    ]
    return [(repr(s), type(s).__name__) for s in samples]


# ---------------------------------------------------------------------------
# 2. Type conversion helpers
# ---------------------------------------------------------------------------

def safe_int(value, default=None):
    """Convert value to int. Handles '12', '12.7', 12.7, ' 7 '.
    Returns `default` if conversion is impossible, including for
    booleans (True is not a number here), NaN and infinity."""
    if isinstance(value, bool):
        return default                 # fix 5: True/False are not numbers
    # fix 3: both blocks catch OverflowError. int(float('inf')) raises it, and
    # "1e309" becomes float('inf') in the second attempt.
    try:
        return int(value)
    except (ValueError, TypeError, OverflowError):
        try:
            return int(float(value))   # e.g. "12.7" -> 12
        except (ValueError, TypeError, OverflowError):
            return default


def safe_float(value, default=None):
    """Convert value to float, accepting strings with commas like '1,234.5'.
    Returns `default` for booleans, NaN, infinity and values that are not numbers."""
    if isinstance(value, bool):
        return default                 # fix 5: True/False are not numbers
    if isinstance(value, str):
        value = value.strip()
        if "," in value:
            # fix 8: commas only as thousands separators: "1,234.5" yes, "1,2,3" no
            if not re.fullmatch(r"[+-]?\d{1,3}(,\d{3})+(\.\d+)?", value):
                return default
            value = value.replace(",", "")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return default                 # OverflowError: a huge int such as 10**400
    if math.isnan(result) or math.isinf(result):
        return default                 # fix 8: "nan", "inf" and "1e309" are not usable numbers
    return result


def to_bool(value):
    """Interpret common truthy/falsy representations."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "y", "1", "on"}:
            return True
        if v in {"false", "no", "n", "0", "off", ""}:
            return False
        raise ValueError(f"Cannot interpret {value!r} as bool")
    return bool(value)


# ---------------------------------------------------------------------------
# 3. List processing
# ---------------------------------------------------------------------------

def clean_numbers(items):
    """Convert a mixed list to floats, skipping anything non-numeric.
    ['1', 2, '3.5', 'abc', None, True] -> [1.0, 2.0, 3.5]
    Booleans, NaN and infinity are skipped (safe_float rejects them)."""
    result = []
    for item in items:
        num = safe_float(item)
        if num is not None:
            result.append(num)
    return result


def list_stats(items):
    """Return count, sum, min, max and mean of the numeric values in items."""
    nums = clean_numbers(items)
    if not nums:
        return {"count": 0, "sum": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": round(sum(nums) / len(nums), 2),
    }


def flatten(nested, _path=None):
    """Flatten arbitrarily nested lists/tuples: [1, [2, (3, [4])]] -> [1, 2, 3, 4].
    Raises ValueError if a list contains itself (it would otherwise recurse forever)."""
    if _path is None:
        _path = set()                  # ids of the lists we are currently inside
    if id(nested) in _path:
        raise ValueError("flatten: a list contains itself")   # fix 11
    _path.add(id(nested))
    flat = []
    for item in nested:
        if isinstance(item, (list, tuple)):
            flat.extend(flatten(item, _path))
        else:
            flat.append(item)
    _path.remove(id(nested))           # leaving this list, so the same list may appear again later
    return flat


def dedup_key(value):
    """Build a hashable key so that two values get equal keys exactly when value1 == value2.

    Unlike make_hashable, each container is labelled with its type, and dict
    order is ignored, because that is how == behaves:
      [[1, 2]] != [(1, 2)]                       -> ('list', ...) vs ('tuple', ...)
      {"a": 1} != [("a", 1)]                     -> ('dict', ...) vs ('list', ...)
      {"a": 1, "b": 2} == {"b": 2, "a": 1}       -> a frozenset, so order doesn't matter
      {1} == frozenset({1})                      -> both ('set', ...)
    Raises TypeError for other unhashable types (e.g. bytearray)."""
    if isinstance(value, list):
        return ("list", tuple(dedup_key(v) for v in value))
    if isinstance(value, tuple):
        return ("tuple", tuple(dedup_key(v) for v in value))
    if isinstance(value, dict):
        return ("dict", frozenset((k, dedup_key(v)) for k, v in value.items()))
    if isinstance(value, (set, frozenset)):
        return ("set", frozenset(value))
    hash(value)                        # TypeError here if value can't be hashed
    return value


def unique_preserve_order(items):
    """Remove duplicates while keeping first-seen order.

    Every item is turned into a dedup_key and the keys go in a set, so each
    lookup is fast (O(1) on average) even for lists and dicts (fix 1).
    For ints and strings the key is the item itself, so their behaviour is unchanged.
    """
    seen_keys = set()
    result = []
    for x in items:
        try:
            key = dedup_key(x)
        except (TypeError, RecursionError):
            if not any(x == kept for kept in result):     # slow fallback, O(n)
                result.append(x)
            continue
        if key not in seen_keys:
            seen_keys.add(key)
            result.append(x)
    return result


def chunk(items, size):
    """Split a list into chunks of `size`. The last chunk may be shorter."""
    if isinstance(size, bool) or not isinstance(size, int):
        raise TypeError("size must be an int")          # fix 12: e.g. 1.5 or "2"
    if size <= 0:
        raise ValueError("size must be positive")
    if not isinstance(items, (list, tuple, str)):
        items = list(items)            # fix 12: generators and ranges have no slicing
    return [items[i:i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# 4. Dictionary processing
# ---------------------------------------------------------------------------

def make_hashable(value):
    """Turn an unhashable value into an equivalent hashable one:
    list -> tuple, set -> frozenset, dict -> tuple of (key, value) pairs.
    Works on nested values too. Hashable values are returned unchanged."""
    if isinstance(value, (list, tuple)):
        return tuple(make_hashable(v) for v in value)
    if isinstance(value, set):
        return frozenset(make_hashable(v) for v in value)
    if isinstance(value, dict):
        return tuple((k, make_hashable(v)) for k, v in value.items())
    return value


def invert_dict(d):
    """Swap keys and values; duplicate values collect their keys in a list.

    Fix 2: a dict key must be hashable, so an unhashable value (list, dict,
    set) is converted with make_hashable before being used as a key:
    {"a": [1, 2]} -> {(1, 2): "a"}. Equal lists still group together."""
    inverted = {}
    for key, value in d.items():
        inverted.setdefault(make_hashable(value), []).append(key)
    return {k: v[0] if len(v) == 1 else v for k, v in inverted.items()}


def is_number(value):
    """True for int and float, but not for bool (True is technically an int)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def merge_dicts(*dicts):
    """Merge dicts; numeric values on shared keys are added, others overwritten.
    Booleans are not numbers, so True + True is not added (fix 5)."""
    merged = {}
    for d in dicts:
        for key, value in d.items():
            if key in merged and is_number(value) and is_number(merged[key]):
                try:
                    merged[key] += value
                except OverflowError:  # e.g. 1.5 + 10**400 is too big for a float
                    merged[key] = value
            else:
                merged[key] = value
    return merged


def filter_dict(d, predicate):
    """Keep only items where predicate(key, value) is True."""
    return {k: v for k, v in d.items() if predicate(k, v)}


def normalize_record(record, schema):
    """Convert a dict of raw (often string) values to the types in schema.
    schema maps key -> type (int, float, bool, str). Bad values become None."""
    converters = {int: safe_int, float: safe_float, bool: to_bool, str: str}
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    out = {}
    for key, target in schema.items():
        if target not in converters:
            raise TypeError(f"unsupported schema type for {key!r}: {target}")
        raw = record.get(key)
        if raw is None:
            out[key] = None
            continue
        try:
            out[key] = converters[target](raw)
        except (ValueError, TypeError, OverflowError):   # fix 7: TypeError too
            out[key] = None
    return out


def group_by(items, key_func):
    """Group a list into a dict of lists using key_func."""
    groups = {}
    for item in items:
        groups.setdefault(key_func(item), []).append(item)
    return groups


# ---------------------------------------------------------------------------
# 5. String processing
# ---------------------------------------------------------------------------

def check_str(text):
    """Raise a clear error instead of a confusing one when text isn't a string (fix 13)."""
    if not isinstance(text, str):
        raise TypeError(f"expected a str, got {type(text).__name__}")


def word_frequency(text, top_n=None):
    """Count words (case-insensitive, punctuation stripped).
    An apostrophe inside a word is kept, so "don't" is one word (fix 10)."""
    check_str(text)
    words = re.findall(r"[^\W_]+(?:'[^\W_]+)*", text.lower())   # letters/digits, with inner '
    counts = Counter(words)
    return dict(counts.most_common(top_n))


def is_palindrome(text):
    """True if text reads the same backwards, ignoring case/spaces/punctuation."""
    check_str(text)
    chars = [c.lower() for c in text if c.isalnum()]
    return chars == chars[::-1]


def to_snake_case(text):
    """'HelloWorld Example-text' -> 'hello_world_example_text'
    Acronyms are kept together: 'HTTPRequest' -> 'http_request' (fix 6)."""
    check_str(text)
    s = re.sub(r"[^A-Za-z0-9]+", "_", text)            # spaces, '-', '.' etc. -> _
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)    # 'HTTPRequest' -> 'HTTP_Request'
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)       # 'userID' -> 'user_ID'
    s = re.sub(r"_+", "_", s)                           # no double underscores
    return s.strip("_").lower()


def parse_key_value_string(s, pair_sep=";", kv_sep="="):
    """'name=Ali; age=21; gpa=3.6' -> {'name': 'Ali', 'age': 21, 'gpa': 3.6}
    Values are auto-converted to int/float/bool where possible.

    Spaces around keys and values are trimmed: 'age = 21 ' -> {'age': 21}.
    To keep spaces, or to stop conversion, put the value in quotes:
    'name=" John "' -> {'name': ' John '}, 'id="007"' -> {'id': '007'}.
    (pair_sep inside quotes still splits the pair; this is a simple parser.)"""
    check_str(s)
    result = {}
    for pair in s.split(pair_sep):
        if kv_sep not in pair:
            continue
        key, value = (part.strip() for part in pair.split(kv_sep, 1))
        if not key:
            continue                                   # "=5" has no key, skip it
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            result[key] = value[1:-1]                  # quoted: keep exactly as written
            continue
        number = safe_float(value)
        # fix 9: only plain ASCII digits become int. The old isdigit() check also
        # passed "²", and lstrip("-") passed "--5", and then int() crashed on both.
        if re.fullmatch(r"-?[0-9]+", value):
            result[key] = int(value)
        elif number is not None:
            result[key] = number                       # fix 9: "1,000" -> 1000.0 (old float() crashed)
        elif value.lower() in {"true", "false"}:
            result[key] = value.lower() == "true"
        else:
            result[key] = value
    return result


def caesar_cipher(text, shift):
    """Shift English letters A-Z / a-z by `shift`, preserving case.
    Everything else (digits, punctuation, é, ñ, α, Ж ...) is left unchanged (fix 4)."""
    check_str(text)
    if isinstance(shift, bool) or not isinstance(shift, int):
        raise TypeError("shift must be an int")
    out = []
    for ch in text:
        if "a" <= ch <= "z":                    # fix 4: ASCII only, not ch.isalpha()
            out.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        else:
            out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# 6. Test harness
# ---------------------------------------------------------------------------

RESULTS = {"passed": 0, "failed": 0}


def check(description, actual, expected):
    ok = actual == expected
    RESULTS["passed" if ok else "failed"] += 1
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {description}")
    print(f"         got:      {actual!r}")
    if not ok:
        print(f"         expected: {expected!r}")


def check_raises(description, func, exc_type):
    """Pass if func() raises exc_type (or a subclass of it).
    Fail if it raises a different exception, or no exception at all.
    A wrong exception is reported instead of crashing the whole test run.
    Returns True for a pass and False for a fail."""
    try:
        result = func()
    except exc_type as e:
        RESULTS["passed"] += 1
        print(f"  [PASS] {description}  -> raised {exc_type.__name__}: {e}")
        return True
    except Exception as e:             # any other error type: report it as a failure
        RESULTS["failed"] += 1
        print(f"  [FAIL] {description}  -> wrong exception type")
        print(f"         expected: {exc_type.__name__}")
        print(f"         got:      {type(e).__name__}: {e}")
        return False
    RESULTS["failed"] += 1             # func() finished without raising anything
    print(f"  [FAIL] {description}  -> no {exc_type.__name__} raised")
    print(f"         returned: {result!r}")
    return False


def self_test_check_raises():
    """Check that check_raises itself works, covering all three outcomes.

    Two of these cases are meant to FAIL, so RESULTS is saved first and
    restored afterwards. That way the assignment summary only counts the
    real program tests. Returns True if check_raises behaved correctly."""
    saved = dict(RESULTS)              # copy of the real counts

    def raises_value_error():
        raise ValueError("bad value")

    def raises_type_error():
        raise TypeError("wrong type")

    def returns_normally():
        return 42

    print("  (the [FAIL] lines below are expected; they check how failures are reported)")
    cases = [
        # (what the case checks, function to call, expected return, passed change, failed change)
        ("correct exception -> PASS", raises_value_error, True, 1, 0),
        ("wrong exception type -> FAIL, no crash", raises_type_error, False, 0, 1),
        ("no exception -> FAIL", returns_normally, False, 0, 1),
    ]
    all_ok = True
    for name, func, expected_return, passed_change, failed_change in cases:
        before = dict(RESULTS)
        try:
            returned = check_raises(f"self-test: {name}", func, ValueError)
        except Exception as e:         # check_raises must never crash
            print(f"  [SELF-TEST BROKEN] {name}: check_raises crashed with {type(e).__name__}: {e}")
            all_ok = False
            continue
        counted_ok = (RESULTS["passed"] - before["passed"] == passed_change
                      and RESULTS["failed"] - before["failed"] == failed_change)
        if returned == expected_return and counted_ok:
            print(f"  [SELF-TEST OK] {name}")
        else:
            print(f"  [SELF-TEST BROKEN] {name}: returned {returned!r}, counts {before} -> {RESULTS}")
            all_ok = False

    RESULTS.clear()
    RESULTS.update(saved)              # put the real counts back
    return all_ok


def section(title):
    print(f"\n=== {title} ===")


def run_tests():
    section("Test harness self-check (not counted in the summary)")
    harness_ok = self_test_check_raises()

    section("Data types")
    for value, type_name in describe_types():
        print(f"  {value:<22} -> {type_name}")

    section("Type conversion")
    check("safe_int('42')", safe_int("42"), 42)
    check("safe_int(' 7 ')", safe_int(" 7 "), 7)
    check("safe_int('12.9') truncates", safe_int("12.9"), 12)
    check("safe_int(True) -> None (fix 5: bool is not a number)", safe_int(True), None)
    check("safe_int('abc', default=0)", safe_int("abc", default=0), 0)
    check("safe_int(None)", safe_int(None), None)
    check("safe_float('1,234.5')", safe_float("1,234.5"), 1234.5)
    check("safe_float('3e2')", safe_float("3e2"), 300.0)
    check("safe_float([1])", safe_float([1]), None)
    check("to_bool('Yes')", to_bool("Yes"), True)
    check("to_bool('off')", to_bool("off"), False)
    check("to_bool(0)", to_bool(0), False)
    check("to_bool([1])", to_bool([1]), True)
    check_raises("to_bool('maybe')", lambda: to_bool("maybe"), ValueError)

    section("List processing")
    check("clean_numbers mixed input (fix 5: True skipped)",
          clean_numbers(["1", 2, "3.5", "abc", None, True]), [1.0, 2.0, 3.5])
    check("list_stats basic", list_stats([10, "20", 30.0]),
          {"count": 3, "sum": 60.0, "min": 10.0, "max": 30.0, "mean": 20.0})
    check("list_stats empty", list_stats([]),
          {"count": 0, "sum": 0, "min": None, "max": None, "mean": None})
    check("list_stats all invalid", list_stats(["x", None])["count"], 0)
    check("flatten nested", flatten([1, [2, (3, [4, [5]])], 6]), [1, 2, 3, 4, 5, 6])
    check("flatten already flat", flatten([1, 2]), [1, 2])
    check("flatten empty", flatten([]), [])
    check("unique_preserve_order", unique_preserve_order([3, 1, 3, 2, 1]), [3, 1, 2])
    check("unique strings", unique_preserve_order(list("banana")), ["b", "a", "n"])
    check("chunk size 2", chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])
    check("chunk larger than list", chunk([1, 2], 5), [[1, 2]])
    check_raises("chunk size 0", lambda: chunk([1], 0), ValueError)

    section("Dictionary processing")
    check("invert_dict unique", invert_dict({"a": 1, "b": 2}), {1: "a", 2: "b"})
    check("invert_dict duplicates", invert_dict({"a": 1, "b": 1, "c": 2}),
          {1: ["a", "b"], 2: "c"})
    check("merge_dicts adds numbers",
          merge_dicts({"x": 1, "y": "a"}, {"x": 2, "y": "b", "z": 3}),
          {"x": 3, "y": "b", "z": 3})
    check("merge_dicts none", merge_dicts(), {})
    scores = {"Ali": 85, "Sara": 92, "Omar": 67}
    check("filter_dict scores >= 80", filter_dict(scores, lambda k, v: v >= 80),
          {"Ali": 85, "Sara": 92})
    check("filter_dict names starting with O",
          filter_dict(scores, lambda k, v: k.startswith("O")), {"Omar": 67})
    schema = {"name": str, "age": int, "gpa": float, "active": bool}
    check("normalize_record clean strings",
          normalize_record({"name": "Ali", "age": "21", "gpa": "3.6", "active": "yes"}, schema),
          {"name": "Ali", "age": 21, "gpa": 3.6, "active": True})
    check("normalize_record bad/missing values",
          normalize_record({"name": 123, "age": "n/a", "active": "maybe"}, schema),
          {"name": "123", "age": None, "gpa": None, "active": None})
    words = ["apple", "avocado", "banana", "cherry", "blueberry"]
    check("group_by first letter", group_by(words, lambda w: w[0]),
          {"a": ["apple", "avocado"], "b": ["banana", "blueberry"], "c": ["cherry"]})
    check("group_by even/odd", group_by(range(6), lambda n: "even" if n % 2 == 0 else "odd"),
          {"even": [0, 2, 4], "odd": [1, 3, 5]})

    section("String processing")
    check("word_frequency", word_frequency("The cat and the hat. THE end!"),
          {"the": 3, "cat": 1, "and": 1, "hat": 1, "end": 1})
    check("word_frequency top 1", word_frequency("a b a c a b", top_n=1), {"a": 3})
    check("word_frequency empty", word_frequency(""), {})
    check("is_palindrome sentence", is_palindrome("A man, a plan, a canal: Panama"), True)
    check("is_palindrome 'racecar'", is_palindrome("racecar"), True)
    check("is_palindrome 'python'", is_palindrome("python"), False)
    check("to_snake_case CamelCase", to_snake_case("HelloWorld"), "hello_world")
    check("to_snake_case mixed", to_snake_case("First Name-field"), "first_name_field")
    check("to_snake_case acronym", to_snake_case("userID"), "user_id")
    check("parse_key_value_string",
          parse_key_value_string("name=Ali; age=21; gpa=3.6; active=true"),
          {"name": "Ali", "age": 21, "gpa": 3.6, "active": True})
    check("parse_key_value_string custom seps",
          parse_key_value_string("x:-5,y:2.5,bad", pair_sep=",", kv_sep=":"),
          {"x": -5, "y": 2.5})
    check("caesar_cipher shift 3", caesar_cipher("Hello, World!", 3), "Khoor, Zruog!")
    check("caesar_cipher round trip",
          caesar_cipher(caesar_cipher("Python 3", 10), -10), "Python 3")
    check("caesar_cipher wraps", caesar_cipher("xyz", 3), "abc")

    section("Regression tests: fixes 1-4")
    # Fix 1 - unique_preserve_order with unhashable items
    check("fix 1: unique_preserve_order([[1], [1], [2]])",
          unique_preserve_order([[1], [1], [2]]), [[1], [2]])
    check("fix 1: unique dicts", unique_preserve_order([{"a": 1}, {"a": 1}, {"b": 2}]),
          [{"a": 1}, {"b": 2}])
    check("fix 1: mixed hashable and unhashable",
          unique_preserve_order([1, [1], "x", 1, [1], "x"]), [1, [1], "x"])
    check("fix 1: ints and strings unchanged", unique_preserve_order([2, "a", 2, "a", 3]), [2, "a", 3])
    # Fix 2 - invert_dict with unhashable values
    check("fix 2: invert_dict list values become tuples",
          invert_dict({"a": [1, 2], "b": [1, 2], "c": 3}), {(1, 2): ["a", "b"], 3: "c"})
    check("fix 2: invert_dict dict value",
          invert_dict({"a": {"x": 1}}), {(("x", 1),): "a"})
    check("fix 2: invert_dict nested list and set",
          invert_dict({"a": [1, [2]], "b": {5}}), {(1, (2,)): "a", frozenset({5}): "b"})
    check("fix 2: invert_dict empty", invert_dict({}), {})
    # Fix 3 - safe_int overflow
    check("fix 3: safe_int('1e309', default=0)", safe_int("1e309", default=0), 0)
    check("fix 3: safe_int(float('inf'))", safe_int(float("inf")), None)
    check("fix 3: safe_int('-1e400', default=-1)", safe_int("-1e400", default=-1), -1)
    check("fix 3: safe_int(float('nan'))", safe_int(float("nan")), None)
    check("fix 3: huge exact int still works", safe_int(10 ** 30), 10 ** 30)
    # Fix 4 - caesar_cipher only shifts ASCII letters
    check("fix 4: caesar_cipher('café', 3)", caesar_cipher("café", 3), "fdié")
    check("fix 4: non-English letters unchanged", caesar_cipher("ñ α Ж", 5), "ñ α Ж")
    check("fix 4: case kept and wraps", caesar_cipher("Zz Éé", 1), "Aa Éé")
    check("fix 4: shift 26 and negative shift", caesar_cipher("Abc", 26) + caesar_cipher("abc", -1), "Abczab")
    check_raises("fix 4: float shift raises", lambda: caesar_cipher("abc", 1.5), TypeError)

    section("Regression tests: reviewer inline comments")
    # Comment on safe_int (lines 49/52): OverflowError in both conversion attempts
    check("review: safe_int(float('inf')) -> default", safe_int(float("inf")), None)
    check("review: safe_int(float('inf'), default=0)", safe_int(float("inf"), default=0), 0)
    check("review: safe_int('1e309') -> default", safe_int("1e309"), None)
    check("review: safe_int('1e309', default=0)", safe_int("1e309", default=0), 0)
    check("review: safe_int(float('-inf'), default=-1)", safe_int(float("-inf"), default=-1), -1)
    # Comment on safe_float (line 62): 10**1000 returns the specified default
    check("review: safe_float(10**1000) -> None", safe_float(10 ** 1000), None)
    check("review: safe_float(10**1000, default=0.0)", safe_float(10 ** 1000, default=0.0), 0.0)
    check("review: safe_float(-10**1000, default=-1.0)", safe_float(-10 ** 1000, default=-1.0), -1.0)
    # Comment on parse_key_value_string (line 224): "--5" stays a string
    check("review: 'age=--5' stays text", parse_key_value_string("age=--5"), {"age": "--5"})
    check("review: 'age=-5' still an int", parse_key_value_string("age=-5"), {"age": -5})
    check("review: 'age=5-' stays text", parse_key_value_string("age=5-"), {"age": "5-"})
    # Comment on parse_key_value_string (line 227): reuse the safe_float() result
    check("review: 'price=1,234.5'", parse_key_value_string("price=1,234.5"), {"price": 1234.5})
    check("review: 'price=1,234.5; qty=2'",
          parse_key_value_string("price=1,234.5; qty=2"), {"price": 1234.5, "qty": 2})

    section("Regression tests: second review notes")
    # Note 1 - to_snake_case with digits (current behaviour is intended; tests lock it in)
    for raw, expected in [("version2Alpha", "version2_alpha"), ("base64Encode", "base64_encode"),
                          ("sha256", "sha256"), ("v2JSON", "v2_json"), ("SHA256Hash", "sha256_hash"),
                          ("utf8", "utf8"), ("getV2API", "get_v2_api")]:
        check(f"note 1: to_snake_case({raw!r})", to_snake_case(raw), expected)
    # Note 2 - whitespace in parse_key_value_string
    check("note 2: 'age = 21 ' trimmed to int", parse_key_value_string("age = 21 "), {"age": 21})
    check("note 2: 'name = John ' trimmed", parse_key_value_string("name = John "), {"name": "John"})
    check("note 2: quoted value keeps its spaces",
          parse_key_value_string('name = " John "'), {"name": " John "})
    check("note 2: single quotes work too", parse_key_value_string("name=' A '"), {"name": " A "})
    check("note 2: quoted number stays text", parse_key_value_string('id="007"; n="21"'),
          {"id": "007", "n": "21"})
    check("note 2: empty quotes -> empty string", parse_key_value_string('a=""'), {"a": ""})
    check("note 2: mismatched quotes are not stripped", parse_key_value_string("a=\"x'"), {"a": "\"x'"})
    check("note 2: a lone quote is kept", parse_key_value_string('a="'), {"a": '"'})
    # Note 3 - unique_preserve_order uses a set for unhashable items too
    check("note 3: list and tuple are different", unique_preserve_order([[1, 2], (1, 2), [1, 2]]),
          [[1, 2], (1, 2)])
    check("note 3: [[1, 2]] vs [(1, 2)] kept apart",
          unique_preserve_order([[[1, 2]], [(1, 2)]]), [[[1, 2]], [(1, 2)]])
    check("note 3: dict vs list of pairs kept apart",
          unique_preserve_order([{"a": 1}, [("a", 1)]]), [{"a": 1}, [("a", 1)]])
    check("note 3: dicts with different key order are duplicates",
          unique_preserve_order([{"a": 1, "b": 2}, {"b": 2, "a": 1}]), [{"a": 1, "b": 2}])
    check("note 3: set and equal frozenset are duplicates",
          unique_preserve_order([{1, 2}, frozenset({1, 2})]), [{1, 2}])
    check("note 3: nested unhashables",
          unique_preserve_order([{"k": [1, {2}]}, {"k": [1, {2}]}, {"k": [1, {3}]}]),
          [{"k": [1, {2}]}, {"k": [1, {3}]}])
    check("note 3: bytearray uses the == fallback",
          unique_preserve_order([bytearray(b"a"), bytearray(b"a"), bytearray(b"b")]),
          [bytearray(b"a"), bytearray(b"b")])
    looped = [1]
    looped.append(looped)
    check("note 3: self-containing list doesn't crash", len(unique_preserve_order([looped, 5])), 2)
    many = [[i % 1000, "x"] for i in range(20000)]
    check("note 3: 20,000 lists -> 1,000 unique, first-seen order",
          unique_preserve_order(many), [[i, "x"] for i in range(1000)])

    section("Regression tests: earlier review items and other edge cases")
    # Fix 5 - booleans
    check("fix 5: safe_float(True)", safe_float(True), None)
    check("fix 5: safe_int(False, default=0)", safe_int(False, default=0), 0)
    check("fix 5: merge_dicts does not add booleans", merge_dicts({"x": True}, {"x": True}), {"x": True})
    check("fix 5: merge_dicts number then bool overwrites", merge_dicts({"x": 1}, {"x": True}), {"x": True})
    check("fix 5: list_stats ignores booleans", list_stats([True, 4])["count"], 1)
    # Fix 6 - snake_case acronyms
    check("fix 6: to_snake_case('HTTPRequest')", to_snake_case("HTTPRequest"), "http_request")
    check("fix 6: to_snake_case('getHTTPResponse')", to_snake_case("getHTTPResponse"), "get_http_response")
    check("fix 6: to_snake_case('HTML5Parser')", to_snake_case("HTML5Parser"), "html5_parser")
    check("fix 6: to_snake_case('first.name')", to_snake_case("first.name"), "first_name")
    check("fix 6: to_snake_case('')", to_snake_case(""), "")
    # Fix 7 - normalize_record catches TypeError
    schema = {"age": int, "gpa": float, "active": bool}
    check("fix 7: list/dict values -> None",
          normalize_record({"age": [21], "gpa": {"v": 1}, "active": "maybe"}, schema),
          {"age": None, "gpa": None, "active": None})
    check("fix 7: huge and NaN values -> None",
          normalize_record({"age": "1e309", "gpa": "nan"}, schema),
          {"age": None, "gpa": None, "active": None})
    check_raises("fix 7: unsupported schema type", lambda: normalize_record({"a": 1}, {"a": list}), TypeError)
    check_raises("fix 7: record is None", lambda: normalize_record(None, schema), TypeError)
    # Fix 8 - safe_float
    check("fix 8: safe_float('nan')", safe_float("nan"), None)
    check("fix 8: safe_float('inf')", safe_float("inf"), None)
    check("fix 8: safe_float('1e309')", safe_float("1e309"), None)
    check("fix 8: safe_float('1,2,3')", safe_float("1,2,3"), None)
    check("fix 8: safe_float(10**400)", safe_float(10 ** 400), None)
    check("fix 8: list_stats ignores NaN", list_stats([1, "nan", 3])["mean"], 2.0)
    # Fix 9 - parse_key_value_string
    check("fix 9: '1,000' (used to crash)", parse_key_value_string("n=1,000"), {"n": 1000.0})
    check("fix 9: '--5' stays text (used to crash)", parse_key_value_string("n=--5"), {"n": "--5"})
    check("fix 9: '²' stays text (used to crash)", parse_key_value_string("n=²"), {"n": "²"})
    check("fix 9: 'nan' stays text", parse_key_value_string("n=nan"), {"n": "nan"})
    check("fix 9: empty key skipped", parse_key_value_string("=5;b=1"), {"b": 1})
    # Fix 10 - word_frequency
    check("fix 10: contractions kept", word_frequency("Don't stop, don't"), {"don't": 2, "stop": 1})
    # Fix 11 - flatten
    looped = [1]
    looped.append(looped)
    check_raises("fix 11: list containing itself", lambda: flatten(looped), ValueError)
    shared = [1, 2]
    check("fix 11: same list twice is fine", flatten([shared, shared]), [1, 2, 1, 2])
    # Fix 12 - chunk
    check("fix 12: chunk a generator", chunk((x for x in range(5)), 2), [[0, 1], [2, 3], [4]])
    check("fix 12: chunk a string", chunk("abcde", 2), ["ab", "cd", "e"])
    check_raises("fix 12: chunk size 1.5", lambda: chunk([1], 1.5), TypeError)
    check_raises("fix 12: chunk size '2'", lambda: chunk([1], "2"), TypeError)
    # Fix 13 - clear errors for non-strings
    check_raises("fix 13: word_frequency(None)", lambda: word_frequency(None), TypeError)
    check_raises("fix 13: is_palindrome(12321)", lambda: is_palindrome(12321), TypeError)
    check_raises("fix 13: caesar_cipher(123, 1)", lambda: caesar_cipher(123, 1), TypeError)

    total = RESULTS["passed"] + RESULTS["failed"]
    print(f"\n=== Summary: {RESULTS['passed']}/{total} passed, {RESULTS['failed']} failed ===")
    print(f"=== Test harness self-check: {'OK' if harness_ok else 'BROKEN'} ===")
    return RESULTS["failed"] == 0 and harness_ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)