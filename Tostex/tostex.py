#!/usr/bin/env python3
import os, sys, shutil, signal, subprocess, time
import argparse, glob, json, re
import tempfile
import tomllib
from dataclasses import dataclass

__version__ = "1.7.5"

DEFAULTS = {
    "binary": "./main",
    "oiejq": "oiejq",
    "time_limit": 1000,
    "in_dir": "in",
    "out_dir": "out",
    "problem": "",
    "generator": "./gen.py",
    "brute": "./brut",
    "stress_iters": 100,
    "stress_timeout": 10,
}

COMMANDS = ["init", "grade", "stress", "help", "version"]
FAIL_DIR = "stress_fail"

TEST_ID_RE = re.compile(r"([A-Za-z]{3})?(\d+)([A-Za-z])")
SUBDIR_RE = re.compile(r"sub(\d+)", re.I)
REPORT_RE = re.compile(
    r"^-{5,}\s*\n"
    r"Status:\s*(?P<status>\S+)\s*\n"
    r"Program exit code:\s*(?P<code>-?\d+)\s*\n"
    r"Time:\s*(?P<time>\d+)\s*ms",
    re.M,
)

SHOW_MAX_BYTES = 300
SHOW_MAX_LINES = 15

# ----------------------------- styling ----------------------------

ANSI = {
    "bold": "1", "dim": "2",
    "red": "31", "green": "32", "yellow": "33",
    "blue": "34", "magenta": "35", "cyan": "36", "gray": "90",
}
COLOR_MODE = "auto"  # auto | always | never
_PROGRESS_ACTIVE = False

_UNICODE = "utf" in (sys.stdout.encoding or "").lower()
SYM = (
    {"ok": "✔", "fail": "✘", "skip": "–", "arrow": "➜", "dot": "·",
     "full": "█", "empty": "░", "rule": "─"}
    if _UNICODE else
    {"ok": "+", "fail": "x", "skip": "-", "arrow": "=>", "dot": "-",
     "full": "#", "empty": ".", "rule": "-"}
)

VERDICT_STYLE = {
    "WA": ("red", "bold"),
    "RE": ("red", "bold"),
    "TLE": ("yellow", "bold"),
    "MISSING": ("magenta",),
    "ERR": ("magenta",),
}


def color_enabled(file):
    if COLOR_MODE == "always":
        return True
    if COLOR_MODE == "never":
        return False
    return (file.isatty() and "NO_COLOR" not in os.environ
            and os.environ.get("TERM") != "dumb")


def paint(text, *styles, file=None):
    file = file or sys.stdout
    if not styles or not color_enabled(file):
        return str(text)
    codes = ";".join(ANSI[s] for s in styles)
    return f"\033[{codes}m{text}\033[0m"


def die(msg, code=1):
    print(f"{paint('error:', 'red', 'bold', file=sys.stderr)} {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"{paint('warning:', 'yellow', 'bold', file=sys.stderr)} {msg}", file=sys.stderr)


def note(msg):
    print(paint(msg, "dim", file=sys.stderr), file=sys.stderr)


def state_style(f):
    """green = full score, yellow = partial, red = zero"""
    if f >= 1:
        return ("green",)
    if f > 0:
        return ("yellow",)
    return ("red",)


def clear_progress_line():
    """Clear a currently displayed in-place progress line on a terminal."""
    global _PROGRESS_ACTIVE
    if _PROGRESS_ACTIVE and sys.stdout.isatty():
        sys.stdout.write("\r\033[2K")
        sys.stdout.flush()
    _PROGRESS_ACTIVE = False


def print_progress_line(text):
    """Update one terminal line, but print normal lines when output is redirected."""
    global _PROGRESS_ACTIVE
    if sys.stdout.isatty():
        sys.stdout.write("\r\033[2K" + text)
        sys.stdout.flush()
        _PROGRESS_ACTIVE = True
    else:
        print(text)
        _PROGRESS_ACTIVE = False


def print_stopped_wa():
    clear_progress_line()
    print(f"\n  {paint('stopped', 'yellow', 'bold')} "
          f"{paint('on first WA (use -k to keep going)', 'dim')}")

def finish_progress_line():
    """Make the current in-place progress line permanent."""
    global _PROGRESS_ACTIVE
    if _PROGRESS_ACTIVE and sys.stdout.isatty():
        sys.stdout.write("\n")
        sys.stdout.flush()
    _PROGRESS_ACTIVE = False


def print_expected_got(exp, got, where):
    """Show EXPECTED / GOT if both are small, otherwise just the file name."""
    def small(b):
        return len(b) <= SHOW_MAX_BYTES and b.count(b"\n") < SHOW_MAX_LINES

    if not (small(exp) and small(got)):
        print(f"    {paint('too large to show:', 'dim')} {paint(where, 'magenta')}")
        return

    def block(label, data, style):
        print(f"    {paint(label, style, 'bold')}")
        text = data.decode(errors="replace").rstrip("\n")
        for line in (text.split("\n") if text else ["(empty)"]):
            print(f"      {line}")

    block("EXPECTED:", exp, "green")
    block("GOT:", got, "red")

# ----------------------------- help -------------------------------

def show_help(prog):
    def head(t): return paint(t, "bold", "yellow")
    def row(label, desc, *styles, width=18):
        return f"  {paint(label.ljust(width), *styles)}{desc}"
    def path(t): return paint(t, "magenta")

    L = []
    L.append(f"{paint(prog, 'bold')} {paint(__version__, 'green')}  "
             f"{paint('—', 'dim')}  subtask grader for competitive programming "
             f"{paint('(timing via oiejq)', 'dim')}")
    L.append("")
    L.append(head("USAGE"))
    L.append(f"  {paint(prog, 'bold')} {paint('[command]', 'green')} {paint('[options]', 'cyan')}")
    L.append("")
    L.append(head("COMMANDS"))
    L.append(row("init", "create problem.toml from the tests found in the input dir", "green", "bold"))
    L.append(row("grade", "run the tests and print the score", "green", "bold"))
    L.append(row("", paint("(default when the config file exists)", "dim")))
    L.append(row("stress", "compare the solution with a brute force on generated inputs", "green", "bold"))
    L.append(row("help", "show this help", "green", "bold"))
    L.append(row("version", "show the version", "green", "bold"))
    L.append("")
    L.append(head("OPTIONS"))
    L.append(row("-c FILE", f"path to the TOML config {paint('(default: problem.toml)', 'dim')}", "cyan"))
    L.append(row("-s BIN", "solution to test (overrides 'binary' in the config)", "cyan"))
    L.append(row("-i, --in-dir DIR", "directory with the inputs (overrides 'in_dir')", "cyan"))
    L.append(row("-o, --out-dir DIR", "directory with the expected outputs (overrides 'out_dir')", "cyan"))
    L.append(row("-k, --keep-going", "do not stop the whole run on the first WA", "cyan"))
    L.append(row("-q, --time-only", "score from runtime only; skip answer checking (grade and stress)", "cyan"))
    L.append(row("-p", f"with {paint('init', 'green')}: print the config instead of writing it", "cyan"))
    L.append(row("-b BIN", f"with {paint('stress', 'green')}: brute force (overrides 'brute')", "cyan"))
    L.append(row("-g BIN", f"with {paint('stress', 'green')}: generator (overrides 'generator')", "cyan"))
    L.append(row("-n COUNT", f"with {paint('stress', 'green')}: cases per subtask (overrides 'stress_iters')", "cyan"))
    L.append(row("-t SUBTASK", f"with {paint('stress', 'green')}: only this subtask number", "cyan"))
    L.append(row("--seed N", f"with {paint('stress', 'green')}: first seed {paint('(default: 1)', 'dim')}", "cyan"))
    L.append(row("--color WHEN", f"auto | always | never {paint('(default: auto)', 'dim')}", "cyan"))
    L.append(row("-V, --version", "show the version", "cyan"))
    L.append(row("-h, --help", "show this help", "cyan"))
    L.append("")
    L.append(head("TESTS"))
    L.append(f"  flat       {path('<in_dir>/<id>.in')}  +  {path('<out_dir>/<id>.out')}")
    L.append(f"             id = {path('[problem code][subtask][char]')}, "
             f"e.g. {path('0a')}, {path('abc1b')}, {path('abc12c')}")
    L.append(f"  nested     {path('<in_dir>/sub<N>/<name>.in')}  +  {path('<out_dir>/sub<N>/<name>.out')}")
    L.append("             the subtask comes from the directory, the name is free")
    L.append(f"  defaults   in_dir = {path('in')}, out_dir = {path('out')}")
    L.append("")
    L.append(head("SCORING"))
    L.append("  A subtask scores the minimum over its tests; after one failed test the")
    L.append("  rest of that subtask is skipped. The first WA also stops the whole run")
    L.append("  (use -k to keep going). A test gets full points up to 50% of the time")
    L.append("  limit, then the score drops linearly to 0 at the limit.")
    L.append("  Scores are displayed as integers (rounded to the nearest point).")
    L.append("  Use -q/--time-only to estimate points from runtime without checking correctness.")
    L.append("  In time-only mode, a test with zero time fraction fails its subtask and")
    L.append("  remaining tests in that subtask are skipped. A disclaimer is printed.")
    L.append("")
    L.append(head("STRESS"))
    L.append(f"  Runs {path('<generator> <subtask> <seed>')} to create an input, feeds it to the")
    L.append("  brute force and to the solution and compares the outputs token by token.")
    L.append("  Seeds go up one by one, so every failure can be reproduced. Subtask 0")
    L.append(f"  is skipped unless chosen with {paint('-t 0', 'cyan')}. The first failing case of a")
    L.append(f"  subtask is saved to {path(FAIL_DIR + '/<subtask>_<seed>.{in,out,got}')}")
    L.append("  (not when the brute force times out). Stress awards a subtask's configured")
    L.append("  points only if all generated cases pass; unrun subtasks earn zero.")
    L.append("  The solution is always timed through oiejq, including stress --time-only.")
    L.append("  Stress --time-only estimates points from oiejq-reported time, without checking")
    L.append("  correctness; exceeding a subtask time limit zeros that subtask and skips")
    L.append("  its remaining generated cases.")
    L.append("  The first WA stops the run; with -k it goes on with the next subtask.")
    L.append("")
    L.append(head("EXAMPLES"))
    L.append(row(f"{prog} init -p", paint("preview the generated config", "dim"), "bold", width=38))
    L.append(row(f"{prog} init", paint("write problem.toml", "dim"), "bold", width=38))
    L.append(row(prog, paint("grade ./main (when problem.toml exists)", "dim"), "bold", width=38))
    L.append(row(f"{prog} -k", paint("grade everything, do not stop on WA", "dim"), "bold", width=38))
    L.append(row(f"{prog} -i tests/in -o tests/out", paint("use other test directories", "dim"), "bold", width=38))
    L.append(row(f"{prog} -s ./other", paint("grade another solution", "dim"), "bold", width=38))
    L.append(row(f"{prog} stress", paint("stress all subtasks with ./gen and ./brute", "dim"), "bold", width=38))
    L.append(row(f"{prog} stress -t 2 -n 500", paint("500 cases of subtask 2 only", "dim"), "bold", width=38))
    L.append(row(f"{prog} --time-only", paint("measure runtimes without checking answers", "dim"), "bold", width=38))
    L.append(row(f"{prog} stress --time-only", paint("benchmark solution without running the brute force", "dim"), "bold", width=38))
    L.append("")
    L.append(paint("Ctrl-C stops the run cleanly and prints what was done so far.", "dim"))
    L.append(paint("Set NO_COLOR=1 or use --color never to disable colors.", "dim"))
    print("\n".join(L))


# ----------------------------- config -----------------------------

def load_config(path, explicit):
    if not os.path.isfile(path):
        if explicit:
            die(f"config not found: {path}")
        note(f"[{path} not found, using defaults]")
        return {}
    with open(path, "rb") as f:
        try:
            return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            die(f"invalid TOML in {path}: {e}")


def natural_key(s):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", s)]


def toml_str(s):
    return json.dumps(s, ensure_ascii=False)


def scan_tests(in_dir):
    """Return (test id, subtask number, problem code or None) in natural order."""
    found = []
    base = glob.escape(in_dir)

    for p in glob.glob(os.path.join(base, "*.in")):
        tid = os.path.basename(p)[:-len(".in")]
        m = TEST_ID_RE.fullmatch(tid)
        if m:
            found.append((tid, m[2], (m[1] or "").lower()))

    for d in glob.glob(os.path.join(base, "sub*")):
        dname = os.path.basename(d)
        m = SUBDIR_RE.fullmatch(dname)
        if not m or not os.path.isdir(d):
            continue
        for p in glob.glob(os.path.join(glob.escape(d), "*.in")):
            name = os.path.basename(p)[:-len(".in")]
            t = TEST_ID_RE.fullmatch(name)
            code = t[1].lower() if t and t[1] else None
            found.append((f"{dname}/{name}", m[1], code))

    found.sort(key=lambda x: natural_key(x[0]))
    return found


def config_text(names, scores, code="", in_dir=None, out_dir=None):
    d = DEFAULTS
    in_dir = in_dir or d["in_dir"]
    out_dir = out_dir or d["out_dir"]
    lines = [
        "# Everything here is optional; missing keys fall back to the defaults shown.",
        f'binary     = "{d["binary"]}"',
        f'oiejq      = "{d["oiejq"]}"',
        f'time_limit = {d["time_limit"]}          # ms',
        f'in_dir     = {toml_str(in_dir)}          # <in_dir>/<id>.in (e.g. 0a, abc0a) or <in_dir>/sub<N>/<name>.in',
        f'out_dir    = {toml_str(out_dir)}         # <out_dir>/<id>.out or <out_dir>/sub<N>/<name>.out',
    ]
    if code:
        lines.append(f'problem    = "{code}"')
    else:
        lines.append('# problem = "abc"   # optional 3-letter problem code filter')
    lines += [
        "",
        "# stress command",
        f'# generator      = "{d["generator"]}"    # called as: <generator> <subtask> <seed>',
        f'# brute          = "{d["brute"]}"  # slow reference solution',
        f'# stress_iters   = {d["stress_iters"]}          # cases per subtask',
        f'# stress_timeout = {d["stress_timeout"]}           # seconds per single run',
    ]

    for n in names:
        lines += ["", f"[subtask{n}]", f"score = {scores[n]}"]
        if n == names[-1]:
            lines.append(f'# time_limit = {d["time_limit"]}   # per-subtask override')
    return "\n".join(lines) + "\n"


def split_scores(names):
    # Subtask 0 = examples (0 pts); the rest share 100 points evenly.
    scored = [n for n in names if n != "0"] or names
    base = 100 // len(scored)
    scores = {n: 0 for n in names}
    for n in scored:
        scores[n] = base
    scores[scored[-1]] += 100 - base * len(scored)
    return scores


def subtask_definitions(cfg, in_dir):
    """Return (subtask number, config table) pairs in natural order."""
    keys = sorted(
        (k for k, v in cfg.items()
         if re.fullmatch(r"subtask\w+", k) and isinstance(v, dict)),
        key=natural_key,
    )
    if keys:
        return [(k[len("subtask"):], cfg[k]) for k in keys]

    nums = sorted({num for _, num, _ in scan_tests(in_dir)}, key=natural_key)
    return [(num, {}) for num in nums]


def default_subtask_scores(raw):
    """Mirror init's default policy: subtask 0 is worth 0 when others exist."""
    names = [num for num, _ in raw]
    if not names:
        return {}
    scored = [n for n in names if n != "0"] or names
    base = 100 // len(scored)
    scores = {n: 0 for n in names}
    for n in scored:
        scores[n] = base
    scores[scored[-1]] += 100 - base * len(scored)
    return scores


def init_config(path, print_only=False, in_dir=None, out_dir=None):
    if not print_only and os.path.exists(path):
        die(f"{path} already exists, not overwriting")

    in_dir = in_dir or DEFAULTS["in_dir"]
    nums, codes = set(), set()
    for _, num, code in scan_tests(in_dir):
        nums.add(num)
        if code is not None:
            codes.add(code)
    names = sorted(nums, key=natural_key) or ["1"]
    code = next(iter(codes)) if len(codes) == 1 else ""
    text = config_text(names, split_scores(names), code, in_dir, out_dir)

    if print_only:
        sys.stdout.write(text)
        return

    with open(path, "w") as f:
        f.write(text)
    print(f"{paint(SYM['ok'], 'green', 'bold')} created {paint(path, 'bold')}")


def settings_from(cfg, args):
    """Config values + defaults, with -i / -o command-line overrides."""
    s = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
    if args.i:
        s["in_dir"] = args.i
    if args.o:
        s["out_dir"] = args.o
    return s


def build_settings(cfg, args):
    s = settings_from(cfg, args)
    want = str(s["problem"]).lower()

    by_sub = {}
    codes = set()
    for tid, num, code in scan_tests(s["in_dir"]):
        if code is not None:
            if want and code != want:
                continue
            codes.add(code)
        by_sub.setdefault(num, []).append(tid)

    if len(codes) > 1:
        shown = ", ".join(c or "(none)" for c in sorted(codes))
        warn(f"tests with several problem codes found: {shown}; "
             f"set 'problem' in the TOML to pick one")

    raw = subtask_definitions(cfg, s["in_dir"])
    if not raw:
        die(f"no tests found in '{s['in_dir']}'")

    default_scores = default_subtask_scores(raw)
    subtasks = []
    for num, st in raw:
        tests = by_sub.get(num, [])
        if not tests:
            warn(f"no tests found for subtask {num}")
        subtasks.append({
            "num": num,
            "name": f"Subtask {num}",
            "score": st.get("score", default_scores.get(num, 0)),
            "time_limit": st.get("time_limit", s["time_limit"]),
            "tests": tests,
        })
    s["subtasks"] = subtasks
    return s


# ----------------------------- grading ----------------------------

@dataclass
class Result:
    verdict: str
    time_ms: int
    fraction: float
    info: str = ""
    expected: bytes = b""
    got: bytes = b""

def kill_group(proc):
    """Children run in their own session, so Ctrl-C never reaches them: kill them ourselves."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    proc.wait()


def last_report(text):
    m = None
    for m in REPORT_RE.finditer(text):
        pass
    return m


def time_factor(t, tl):
    full = tl * 0.5
    if t <= full:
        return 1.0
    if t >= tl:
        return 0.0
    return (tl - t) / (tl - full)


def run_oiejq(S, binary, input_path, tl_ms, wall_timeout=None):
    """Run a solution through oiejq and return (Result, stdout bytes).

    oiejq's reported instruction time is the authoritative runtime. The optional
    wall_timeout only prevents a hung oiejq/solution process from running forever.
    """
    if not os.path.isfile(input_path):
        return Result("MISSING", 0, 0.0, f"no such file: {input_path}"), b""

    wall = wall_timeout if wall_timeout is not None else tl_ms / 1000 * 5 + 1
    with open(input_path, "rb") as fin, tempfile.TemporaryFile() as fout:
        proc = subprocess.Popen(
            [S["oiejq"], binary],
            stdin=fin, stdout=fout, stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            err = proc.communicate(timeout=wall)[1]
        except subprocess.TimeoutExpired:
            kill_group(proc)
            proc.communicate()
            return Result("TLE", int(wall * 1000), 0.0,
                          f"killed (wall-clock guard: {wall:g} s)"), b""
        except BaseException:
            kill_group(proc)
            raise
        fout.seek(0)
        out_bytes = fout.read()

    out_text = out_bytes.decode(errors="replace")
    err_text = err.decode(errors="replace")

    # The report normally lands on stderr; support stdout as a fallback.
    rep = last_report(err_text)
    if rep is None:
        rep = last_report(out_text)
        if rep:
            out_bytes = out_text[:rep.start()].encode()
    if rep is None:
        return Result("ERR", 0, 0.0, "no oiejq report found"), out_bytes

    status, code, t = rep["status"], int(rep["code"]), int(rep["time"])
    if t > tl_ms:
        return Result("TLE", t, 0.0), out_bytes
    if status != "OK" or code != 0:
        return Result("RE", t, 0.0,
                      f"status {status}, exit code {code}"), out_bytes

    return Result("OK", t, time_factor(t, tl_ms)), out_bytes


def run_test(S, binary, test_id, tl_ms, check_output=True):
    inp = os.path.join(S["in_dir"], test_id + ".in")
    exp = os.path.join(S["out_dir"], test_id + ".out")
    required_files = (inp, exp) if check_output else (inp,)
    for path in required_files:
        if not os.path.isfile(path):
            return Result("MISSING", 0, 0.0, f"no such file: {path}")

    result, out = run_oiejq(S, binary, inp, tl_ms)
    if result.verdict != "OK":
        return result

    if not check_output:
        return Result("TIME", result.time_ms, result.fraction)

    with open(exp, "rb") as f:
        exp_bytes = f.read()
    if out.decode(errors="replace").split() != exp_bytes.decode(errors="replace").split():
        return Result("WA", result.time_ms, 0.0, expected=exp_bytes, got=out)

    return Result("OK", result.time_ms, result.fraction)


def print_test(tid, r, w=7):
    f = r.fraction
    st = state_style(f)
    icon = SYM["ok"] if f > 0 else SYM["fail"]
    vstyle = st if r.verdict == "OK" else VERDICT_STYLE.get(r.verdict, ("red",))
    tstyle = ("gray",) if f >= 1 else st
    name = f"{tid:<{w}}"
    verd = f"{r.verdict:<7}"
    tm = f"{r.time_ms:>7} ms"
    pct = f"{f * 100:6.1f}%"
    extra = f"  {paint('(' + r.info + ')', 'dim')}" if r.info else ""
    line = (f"  {paint(icon, *st, 'bold')} "
            f"{paint(name, 'bold')} "
            f"{paint(verd, *vstyle)} "
            f"{paint(tm, *tstyle)}  "
            f"{paint(pct, *st)}{extra}")
    print_progress_line(line)


def print_skipped(tid, w=7):
    name = f"{tid:<{w}}"
    line = f"  {paint(SYM['skip'], 'gray')} {paint(name, 'gray')} {paint('skipped', 'gray')}"
    print_progress_line(line)


def print_timing_test(tid, r, w=7):
    """Print only timing and runtime errors in --time-only mode."""
    name = f"{tid:<{w}}"
    tm = f"{r.time_ms:>7} ms"
    if r.verdict == "TIME":
        line = f"  {paint(SYM['dot'], 'dim')} {paint(name, 'bold')} {paint(tm, 'cyan')}"
    else:
        style = VERDICT_STYLE.get(r.verdict, ("red", "bold"))
        extra = f"  {paint('(' + r.info + ')', 'dim')}" if r.info else ""
        line = (f"  {paint(SYM['fail'], *style)} {paint(name, 'bold')} "
                f"{paint(r.verdict, *style)} {paint(tm, 'yellow')}{extra}")
    print_progress_line(line)


def timing_summary_line(label, times):
    """Compact summary of measured per-case times, in milliseconds."""
    if not times:
        return f"  {paint(label, 'bold')}  no successful timings"
    avg = sum(times) / len(times)
    slowest = max(times)
    return (f"  {paint(label, 'bold')}  {len(times)} runs  {SYM['dot']}  "
            f"avg {avg:.1f} ms  {SYM['dot']}  slowest {slowest} ms")


def bar(ratio, width=24):
    filled = round(ratio * width)
    st = state_style(ratio)
    return (paint(SYM["full"] * filled, *st) +
            paint(SYM["empty"] * (width - filled), "gray"))


def calculate_score(subtasks, fractions_by_num):
    """Shared score calculator used by both grading and stress testing."""
    max_total = sum(float(st["score"]) for st in subtasks)
    total = 0.0
    for st in subtasks:
        fraction = max(0.0, min(1.0, float(fractions_by_num.get(st["num"], 0.0))))
        total += float(st["score"]) * fraction
    return total, max_total


def score_summary_line(label, total, max_total):
    """Format score as integer points while preserving the exact ratio in the bar."""
    ratio = total / max_total if max_total else 0.0
    total_txt = f"{round(total)} / {round(max_total)}"
    return f"{paint(label, 'bold')}  {bar(ratio)}  {paint(total_txt, *state_style(ratio), 'bold')}"


def subtask_header_line(subtask):
    """Format the shared subtask heading used by grade and stress."""
    name = subtask.get("name", f"Subtask {subtask['num']}")
    pts_txt = paint(f"{subtask['score']:g} pts", "dim")
    tl_txt = paint(f"TL {subtask['time_limit']} ms", "dim")
    dot = paint(SYM["dot"], "dim")
    return f"{paint(name, 'bold', 'cyan')}  {dot}  {pts_txt}  {dot}  {tl_txt}"


def subtask_score_line(subtask, fraction):
    """Format the points earned for one subtask using the shared integer style."""
    maximum = float(subtask["score"])
    fraction = max(0.0, min(1.0, float(fraction)))
    earned = maximum * fraction
    style = state_style(fraction)
    score_txt = f"{round(earned)} / {round(maximum)}"
    return f"  {paint(SYM['arrow'], *style, 'bold')} {paint(score_txt, *style, 'bold')}"


def grade(args):
    cfg = load_config(args.c, explicit=args.c != "problem.toml")
    S = build_settings(cfg, args)
    binary = args.s or S["binary"]

    if shutil.which(S["oiejq"]) is None:
        die(f"'{S['oiejq']}' not found in PATH")
    if not os.path.isfile(binary):
        die(f"binary not found: {binary}")

    if args.time_only:
        print(paint(
            "TIME-ONLY MODE: points use oiejq-reported time; answer correctness is not checked.",
            "yellow", "bold",
        ))

    subs = S["subtasks"]
    tw = max([7] + [len(t) for st in subs for t in st["tests"]])
    fractions_by_num = {st["num"]: 0.0 for st in subs}
    done = 0
    stop = None

    try:
        for st in subs:
            tl = st["time_limit"]
            print(f"\n{subtask_header_line(st)}")
            fractions = []
            failed = False
            saw_wa = False

            for tid in st["tests"]:
                if failed:
                    print_skipped(tid, tw)
                    continue

                r = run_test(S, binary, tid, tl, check_output=not args.time_only)
                fractions.append(r.fraction)

                if args.time_only:
                    print_timing_test(tid, r, tw)
                else:
                    print_test(tid, r, tw)
                    if r.verdict == "WA":
                        saw_wa = True
                        finish_progress_line()
                        print_expected_got(
                            r.expected, r.got,
                            os.path.join(S["out_dir"], tid + ".out"))

                # In either mode, a zero-fraction test fails the subtask and
                # remaining tests in this subtask are skipped.
                if r.fraction == 0.0:
                    failed = True

            clear_progress_line()
            ratio = min(fractions) if fractions else 0.0
            fractions_by_num[st["num"]] = ratio
            done += 1
            print(subtask_score_line(st, ratio))

            if saw_wa and not args.k:
                stop = "wa"
                break
    except KeyboardInterrupt:
        clear_progress_line()
        stop = "int"
        print(f"\n  {paint('interrupted', 'yellow', 'bold')}")

    if stop == "wa":
        print_stopped_wa()
    rest = [st["name"] for st in subs[done:]]
    if stop and rest:
        label = "not run" if stop == "wa" else "not completed"
        print(paint(f"  {label}: {', '.join(rest)}", "dim"))

    total, max_total = calculate_score(subs, fractions_by_num)
    print(f"\n{paint(SYM['rule'] * 44, 'dim')}")
    label = "TOTAL (TIME-ONLY)" if args.time_only else "TOTAL"
    print(score_summary_line(label, total, max_total))
    if stop == "int":
        sys.exit(130)


# ----------------------------- stress -----------------------------

def run_cmd(cmd, stdin_path, timeout):
    """Return (status, ms, stdout bytes, info); status is OK | RE | TLE."""
    fin = open(stdin_path, "rb") if stdin_path else subprocess.DEVNULL
    try:
        with tempfile.TemporaryFile() as fout, tempfile.TemporaryFile() as ferr:
            start = time.monotonic()
            proc = subprocess.Popen(cmd, stdin=fin, stdout=fout, stderr=ferr,
                                    start_new_session=True)
            try:
                code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                kill_group(proc)
                return "TLE", int(timeout * 1000), b"", f"no result within {timeout} s"
            except BaseException:
                kill_group(proc)
                raise
            ms = int((time.monotonic() - start) * 1000)
            fout.seek(0)
            out = fout.read()
            ferr.seek(0)
            err = ferr.read(2000).decode(errors="replace").strip()
    finally:
        if stdin_path:
            fin.close()

    if code == 0:
        return "OK", ms, out, ""
    if code < 0:
        try:
            info = f"killed by {signal.Signals(-code).name}"
        except ValueError:
            info = f"killed by signal {-code}"
    else:
        info = f"exit code {code}"
    if err:
        info += f", stderr: {err.splitlines()[0][:100]}"
    return "RE", ms, out, info


def clip(b, n=40):
    s = b.decode(errors="replace")
    return s if len(s) <= n else s[:n] + "…"


def first_diff(exp, got):
    e, g = exp.split(), got.split()
    for i, (a, b) in enumerate(zip(e, g)):
        if a != b:
            return f"token {i + 1}: expected {clip(a)}, got {clip(b)}"
    return f"expected {len(e)} tokens, got {len(g)}"


def stress_case(S, gen, sol, brute, num, seed, inp, timeout, tl_ms,
                time_only=False):
    """Return (verdict, info, oiejq solution ms, expected bytes, got bytes)."""
    st, _, out, info = run_cmd([gen, num, str(seed)], None, timeout)
    if st != "OK":
        return "GEN-" + st, info, 0, b"", b""
    with open(inp, "wb") as f:
        f.write(out)

    if time_only:
        result, got = run_oiejq(S, sol, inp, tl_ms, wall_timeout=timeout)
        if result.verdict != "OK":
            return result.verdict, result.info, result.time_ms, b"", got
        return "TIME", "", result.time_ms, b"", got

    st, _, exp, info = run_cmd([brute], inp, timeout)
    if st != "OK":
        return "BRUTE-" + st, info, 0, b"", b""

    result, got = run_oiejq(S, sol, inp, tl_ms, wall_timeout=timeout)
    if result.verdict != "OK":
        return result.verdict, result.info, result.time_ms, exp, got
    # A run whose time fraction is zero (including exactly at the TL) is not
    # considered a successful stress case, matching the grader's scoring rule.
    if result.fraction <= 0.0:
        return "TLE", f"met or exceeded subtask time limit of {tl_ms} ms", result.time_ms, exp, got
    if got.split() != exp.split():
        return "WA", first_diff(exp, got), result.time_ms, exp, got
    return "OK", "", result.time_ms, exp, got


def save_failure(num, seed, inp, exp, got):
    os.makedirs(FAIL_DIR, exist_ok=True)
    base = os.path.join(FAIL_DIR, f"{num}_{seed}")
    shutil.copy(inp, base + ".in")
    if exp:
        with open(base + ".out", "wb") as f:
            f.write(exp)
    if got:
        with open(base + ".got", "wb") as f:
            f.write(got)
    return base


def stress_subtasks(cfg, in_dir):
    raw = subtask_definitions(cfg, in_dir)
    nums = [num for num, _ in raw if num != "0"]
    return nums or ["1"]


def stress_score_subtasks(cfg, in_dir, fallback_nums, default_time_limit):
    """Use the same configured/default point weights and limits as grade()."""
    raw = subtask_definitions(cfg, in_dir)
    if not raw or not any(num != "0" for num, _ in raw):
        raw = [(num, {}) for num in fallback_nums]

    defaults = default_subtask_scores(raw)
    return [
        {
            "num": num,
            "name": f"Subtask {num}",
            "score": st.get("score", defaults.get(num, 0)),
            "time_limit": st.get("time_limit", default_time_limit),
        }
        for num, st in raw
    ]


def stress(args):
    cfg = load_config(args.c, explicit=args.c != "problem.toml")
    S = settings_from(cfg, args)

    sol_arg = args.s or S["binary"]
    brute_arg = args.b or S["brute"]
    gen_arg = args.g or S["generator"]
    iters = args.n if args.n is not None else S["stress_iters"]
    timeout = S["stress_timeout"]

    if iters < 1:
        die("number of cases must be at least 1")
    required_binaries = [("solution", sol_arg), ("generator", gen_arg)]
    if not args.time_only:
        required_binaries.insert(1, ("brute force", brute_arg))
    for label, p in required_binaries:
        if not os.path.isfile(p):
            die(f"{label} not found: {p}")
        if not os.access(p, os.X_OK):
            die(f"{label} is not executable: {p}")
    if shutil.which(S["oiejq"]) is None:
        die(f"'{S['oiejq']}' not found in PATH")
    sol, brute, gen = (os.path.abspath(p) for p in (sol_arg, brute_arg, gen_arg))

    if args.t is not None:
        if not args.t.isdigit():
            die("-t needs a subtask number")
        nums = [args.t]
    else:
        nums = stress_subtasks(cfg, S["in_dir"])

    score_subtasks = stress_score_subtasks(cfg, S["in_dir"], nums, S["time_limit"])
    score_by_num = {st["num"]: st for st in score_subtasks}
    # Correctness stress earns points only when every case agrees with brute.
    # Time-only stress estimates a fraction from each run's oiejq time.
    score_fractions = {st["num"]: 0.0 for st in score_subtasks}

    if args.time_only:
        print(paint(
            "TIME-ONLY MODE: points use oiejq-reported time; correctness is not checked. Wall-clock timeout is only a safety guard.",
            "yellow", "bold",
        ))

    tty = sys.stdout.isatty()
    dot = paint(SYM["dot"], "dim")
    ok_icon = paint(SYM["ok"], "green", "bold")
    fail_icon = paint(SYM["fail"], "red", "bold")
    failed_subs = 0
    checked = 0
    cases = 0
    stop = None
    current_num = None
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "case.in")
        try:
            for num in nums:
                current_num = num
                subtask = score_by_num.get(num, {
                    "num": num,
                    "name": f"Subtask {num}",
                    "score": 0,
                    "time_limit": S["time_limit"],
                })
                tl = int(subtask["time_limit"])
                info_txt = paint(f"stress {SYM['dot']} {iters} cases from seed {args.seed}", "dim")
                print(f"\n{subtask_header_line(subtask)}")
                print(f"  {info_txt}")

                max_ms = 0
                bad = None
                cases = 0
                subtask_times = []
                # Assume all generated cases will meet the time limit until a
                # failure says otherwise; scoring takes the minimum time factor.
                if args.time_only and num in score_fractions:
                    score_fractions[num] = 1.0

                for i in range(iters):
                    seed = args.seed + i
                    if tty:
                        print_progress_line(f"  {paint(f'{i + 1}/{iters}', 'dim')}")

                    verdict, info, ms, exp, got = stress_case(
                        S, gen, sol, brute, num, seed, inp, timeout, tl,
                        time_only=args.time_only,
                    )
                    max_ms = max(max_ms, ms)

                    if args.time_only:
                        # Include a failed solution run's oiejq time in the summary too.
                        if verdict != "TIME" and ms > 0:
                            subtask_times.append(ms)
                        # Generator errors, solution errors, stress-timeout, or
                        # exceeding the configured subtask TL all fail this
                        # subtask and suppress the rest of its generated cases.
                        if verdict == "TIME":
                            subtask_times.append(ms)
                            fraction = time_factor(ms, tl)
                            if fraction <= 0.0:
                                bad = (seed, i, "TLE", f"met or exceeded subtask time limit of {tl} ms", exp, got)
                                score_fractions[num] = 0.0
                                break
                            score_fractions[num] = min(score_fractions[num], fraction)
                            cases += 1
                            continue

                        if verdict.startswith("GEN-") or verdict in ("TLE", "RE", "MISSING", "ERR"):
                            bad = (seed, i, verdict, info, exp, got)
                            score_fractions[num] = 0.0
                            break

                    elif verdict == "OK":
                        cases += 1
                        continue

                    else:
                        bad = (seed, i, verdict, info, exp, got)
                        break

                clear_progress_line()
                checked += 1

                if bad is None:
                    if args.time_only:
                        measured = paint(f"{len(subtask_times)}/{iters} runs timed", "green", "bold")
                        print(f"  {ok_icon} {measured}")
                        print(timing_summary_line("TIMING", subtask_times))
                        print(subtask_score_line(subtask, score_fractions.get(num, 0.0)))
                        current_num = None
                    else:
                        score_fractions[num] = 1.0
                        passed = paint(f"{iters}/{iters} passed", "green", "bold")
                        slow = paint(f"slowest run {max_ms} ms", "dim")
                        print(f"  {ok_icon} {passed}  {dot}  {slow}")
                        if num in score_by_num:
                            print(subtask_score_line(score_by_num[num], score_fractions[num]))
                        current_num = None
                    continue

                seed, i, verdict, info, exp, got = bad
                failed_subs += 1
                vstyle = VERDICT_STYLE.get(verdict, ("magenta",))
                after = paint(f"(after {i} passed)", "dim")
                print(f"  {fail_icon} {paint(verdict, *vstyle)} on seed {seed}  {after}")
                if info:
                    print(f"    {paint(info, 'dim')}")
                if not args.time_only and ms > 0 and not verdict.startswith(("GEN-", "BRUTE-")):
                    print(f"    {paint(f'solution time {ms} ms', 'dim')}")
                if not args.time_only:
                    print(f"    {paint('repro', 'gray')}  {gen_arg} {num} {seed}")
                else:
                    print(f"    {paint('case', 'gray')}  seed {seed}")

                if not args.time_only and verdict == "BRUTE-TLE":
                    print(f"    {paint('not saved', 'gray')}  {paint('brute force timed out', 'dim')}")
                elif not args.time_only and not verdict.startswith("GEN-"):
                    base = save_failure(num, seed, inp, exp, got)
                    print(f"    {paint('saved', 'gray')}  {paint(base + '.{in,out,got}', 'magenta')}")
                    if verdict == "WA":
                        print_expected_got(exp, got, base + ".{in,out,got}")
                        
                if args.time_only:
                    print(timing_summary_line("TIMING", subtask_times))
                if num in score_by_num:
                    print(subtask_score_line(score_by_num[num], score_fractions.get(num, 0.0)))

                current_num = None
                if verdict == "WA" and not args.k:
                    stop = "wa"
                    break
        except KeyboardInterrupt:
            stop = "int"
            if args.time_only and current_num is not None:
                # An interrupted subtask did not complete every planned case.
                score_fractions[current_num] = 0.0
            clear_progress_line()
            after = paint(f"after {cases} passed cases", "dim")
            print(f"  {paint('interrupted', 'yellow', 'bold')} {after}")

    if stop == "wa":
        print_stopped_wa()

    total = len(nums)
    ok_n = checked - failed_subs
    st = state_style(ok_n / total if total else 0.0)
    summary = f"{ok_n}/{total} subtasks passed"

    print(f"\n{paint(SYM['rule'] * 44, 'dim')}")
    if args.time_only:
        completed = f"{ok_n}/{total} subtasks benchmarked successfully"
        line = f"{paint('STRESS TIME-ONLY', 'bold')}  {paint(completed, *st, 'bold')}"
        if stop:
            left = total - checked
            line += "  " + paint(f"({left} not run)" if left else "(stopped early)", "dim")
        print(line)
        score_total, score_max = calculate_score(score_subtasks, score_fractions)
        print(score_summary_line("SCORE (TIME-ONLY)", score_total, score_max))
        sys.exit(130 if stop == "int" else 1 if failed_subs else 0)

    line = f"{paint('STRESS', 'bold')}  {paint(summary, *st, 'bold')}"
    if stop:
        left = total - checked
        line += "  " + paint(f"({left} not run)" if left else "(stopped early)", "dim")
    print(line)
    score_total, score_max = calculate_score(score_subtasks, score_fractions)
    print(score_summary_line("SCORE", score_total, score_max))
    sys.exit(130 if stop == "int" else 1 if failed_subs else 0)


# ------------------------------ main ------------------------------

class Parser(argparse.ArgumentParser):
    def error(self, message):
        die(f"{message}  (try '{self.prog} help')", 2)


def main():
    global COLOR_MODE
    prog = os.path.basename(sys.argv[0])
    ap = Parser(prog=prog, add_help=False)
    ap.add_argument("cmd", nargs="?", choices=COMMANDS, metavar="command")
    ap.add_argument("-c", default="problem.toml")
    ap.add_argument("-s")
    ap.add_argument("-i", "--in-dir", dest="i")
    ap.add_argument("-o", "--out-dir", dest="o")
    ap.add_argument("-k", "--keep-going", dest="k", action="store_true")
    ap.add_argument("-q", "--time-only", "--timing-only", dest="time_only", action="store_true",
                    help="measure runtimes only; skip answer checking (grade and stress)")
    ap.add_argument("-p", action="store_true")
    ap.add_argument("-b")
    ap.add_argument("-g")
    ap.add_argument("-n", type=int)
    ap.add_argument("-t")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--color", choices=["auto", "always", "never"], default="auto")
    ap.add_argument("-V", "--version", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    COLOR_MODE = args.color

    if args.help or args.cmd == "help":
        show_help(prog)
        return
    if args.version or args.cmd == "version":
        print(f"{paint(prog, 'bold')} {paint(__version__, 'green')}")
        return

    if args.p and args.cmd != "init":
        ap.error("-p can only be used with the 'init' command")
    if args.time_only and args.cmd not in (None, "grade", "stress"):
        ap.error("-q/--time-only can only be used with 'grade' and 'stress'")
    if args.cmd != "stress" and any(v is not None for v in (args.b, args.g, args.n, args.t)):
        ap.error("-b, -g, -n and -t can only be used with the 'stress' command")
    if args.k and args.cmd not in (None, "grade", "stress"):
        ap.error("-k can only be used with the 'grade' and 'stress' commands")

    if args.cmd is None and len(sys.argv) == 1 and not os.path.isfile(args.c):
        show_help(prog)
        return

    try:
        if args.cmd == "init":
            init_config(args.c, print_only=args.p, in_dir=args.i, out_dir=args.o)
        elif args.cmd == "stress":
            stress(args)
        else:
            grade(args)
    except KeyboardInterrupt:
        clear_progress_line()
        print(f"\n{paint('interrupted', 'yellow', 'bold', file=sys.stderr)}", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
