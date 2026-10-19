"""Run every sample resume against every sample JD and print a compact report."""
import sys
from pathlib import Path

from app.analyzer import run_analysis
from app.file_reader import read_document

SAMPLES = Path("samples")


def load(prefix):
    return {p.stem: read_document(p.read_bytes(), p.name) for p in sorted(SAMPLES.glob(prefix + "*"))}


resumes, jobs = load("resume"), load("jd")
detail = len(sys.argv) > 1

print(f"{'':32}" + "".join(f"{j[:14]:>16}" for j in jobs))
for rname, rtext in resumes.items():
    cells = []
    for jname, jtext in jobs.items():
        s = run_analysis(rtext, jtext)["score"]
        cells.append(f"{s['overall']:5.1f} ({s['semantic_match']:4.1f})")
    print(f"{rname[:32]:32}" + "".join(f"{c:>16}" for c in cells))

if detail:
    for (rname, rtext), (jname, jtext) in zip(resumes.items(), jobs.items()):
        r = run_analysis(rtext, jtext)
        print(f"\n===== {rname}  vs  {jname}")
        print("matched:", [x["skill"] for x in r["matched"]])
        print("missing required:", [x["skill"] for x in r["missing_required"]])
        print("missing preferred:", [x["skill"] for x in r["missing_preferred"]])
        print("uncertain:", [x["skill"] for x in r["uncertain"]])
        print("roadmap:", [f"{s['skill']}({s['priority'][0]})" for s in r["roadmap"]["steps"]])
        for m in r["requirement_matches"]:
            print(f"   {m['similarity']:.2f} {m['match']:9} {m['requirement'][:55]!r} -> {m['closest_resume_line'][:45]!r}")
