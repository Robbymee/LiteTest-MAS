from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


FORBIDDEN = {
    "candidate_code", "raw_response", "hidden_reference_tests", "canonical_solution", "reference_solution",
    "official_tests", "contract", "expected_output", "api_key", "authorization", "request_ids",
}
INPUT_FILES = (
    "m9_aggregate_manifest.json", "m9_aggregate_groups.json", "m9_aggregate_datasets.json",
    "m9_aggregate_seeds.json", "m9_paired_comparisons.json",
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(*(recursive_keys(child) for child in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(recursive_keys(child) for child in value)) if value else set()
    return set()


def read_inputs(aggregate_dir: Path) -> dict[str, Any]:
    values = {}
    for name in INPUT_FILES:
        path = aggregate_dir / name
        values[name] = json.loads(path.read_text(encoding="utf-8"))
    forbidden = FORBIDDEN & set().union(*(recursive_keys(value) for value in values.values()))
    if forbidden:
        raise ValueError("forbidden_aggregate_field:" + ",".join(sorted(forbidden)))
    manifest = values["m9_aggregate_manifest.json"]
    if manifest.get("result_scope") != "formal_real_llm_ablation" or not manifest.get("strict_verifier", {}).get("valid"):
        raise ValueError("aggregate_manifest_not_strict_formal")
    return values


def dashboard_data(inputs: dict[str, Any]) -> dict[str, Any]:
    manifest = inputs["m9_aggregate_manifest.json"]
    groups = inputs["m9_aggregate_groups.json"]
    comparisons = inputs["m9_paired_comparisons.json"]
    safe_groups = [{
        key: row[key] for key in (
            "experiment_group", "task_count", "task_success_count", "task_success_rate",
            "official_test_pass_rate", "mean_total_tokens", "mean_latency_seconds",
            "mean_state_vector_bytes", "mean_memory_hit_count", "mean_memory_reuse_count",
            "model_quality_failure_count", "infrastructure_failure_count",
        )
    } for row in groups]
    safe_comparisons = [{
        key: row[key] for key in (
            "treatment_group", "control_group", "metric", "mean_difference", "ci_lower", "ci_upper",
            "paired_count", "bootstrap_resamples", "confidence",
        )
    } for row in comparisons if row["metric"] in {"task_success", "official_test_pass_rate", "total_tokens", "latency_seconds"}]
    return {
        "schema_version": "1.0",
        "result_scope": manifest["result_scope"],
        "model": manifest["model"],
        "freeze_git_sha": manifest["freeze_git_sha"],
        "spec_sha256": manifest["spec_sha256"],
        "final_record_count": manifest["final_record_count"],
        "strict_verifier": manifest["strict_verifier"],
        "bootstrap": manifest["bootstrap"],
        "aggregate_input_sha256": manifest["aggregate_input_sha256"],
        "deterministic_aggregate_sha256": manifest["deterministic_aggregate_sha256"],
        "groups": safe_groups,
        "datasets": inputs["m9_aggregate_datasets.json"],
        "seeds": inputs["m9_aggregate_seeds.json"],
        "comparisons": safe_comparisons,
    }


def page(data: dict[str, Any]) -> str:
    serialized = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LiteTest-MAS M9 Results</title>
<style>
:root {{ color-scheme: light; --ink:#17212b; --muted:#637381; --line:#d9e0e5; --panel:#ffffff; --page:#f5f7f8; --green:#16845b; --blue:#276fbf; --orange:#b86a19; --red:#b64040; }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--page); color:var(--ink); font:14px/1.45 Arial,sans-serif }}
header {{ background:#142b3b; color:#fff; padding:24px max(24px,calc((100vw - 1180px)/2)); border-bottom:4px solid #16845b }}
h1 {{ margin:0; font-size:26px; font-weight:650; letter-spacing:0 }} header p {{ margin:5px 0 0; color:#c7d6df }}
main {{ max-width:1180px; margin:0 auto; padding:22px 24px 38px }} .facts {{ color:var(--muted); margin:0 0 18px }}
.cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:16px 0 24px }} .card {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:14px; min-height:116px }}
.label {{ color:var(--muted); font-size:12px }} .value {{ font-size:25px; font-weight:650; margin-top:3px }} .detail {{ color:var(--muted); margin-top:4px; font-size:12px }}
section {{ margin-top:24px }} h2 {{ font-size:18px; margin:0 0 10px }} .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; overflow:auto }}
table {{ width:100%; border-collapse:collapse; min-width:760px }} th,td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:middle }} th {{ font-size:12px; color:var(--muted); background:#fafcfd }} tr:last-child td {{ border-bottom:0 }}
.bar {{ height:8px; background:#e8eef1; width:130px; border-radius:2px; overflow:hidden }} .bar span {{ display:block; height:100%; background:var(--green) }} .good {{ color:var(--green) }} .neutral {{ color:var(--blue) }} .negative {{ color:var(--red) }}
footer {{ color:var(--muted); font-size:12px; margin-top:22px }} @media(max-width:760px) {{ .cards {{ grid-template-columns:repeat(2,minmax(0,1fr)) }} main {{ padding:18px 14px }} header {{ padding:20px 14px }} }}
</style></head><body><header><h1>LiteTest-MAS M9 Results</h1><p>Offline, public aggregate view of the frozen formal experiment.</p></header><main>
<p id="facts" class="facts"></p><div id="cards" class="cards"></div>
<section><h2>Group Outcomes</h2><div class="panel"><table><thead><tr><th>Group</th><th>Task Success</th><th>Official Test Rate</th><th>Mean Tokens</th><th>Mean Latency</th><th>State Bytes</th><th>Memory Hits</th></tr></thead><tbody id="groups"></tbody></table></div></section>
<section><h2>Paired Comparisons</h2><div class="panel"><table><thead><tr><th>Comparison</th><th>Metric</th><th>Difference</th><th>95% CI</th><th>Pairs</th></tr></thead><tbody id="comparisons"></tbody></table></div></section>
<footer>Static dashboard. Values are fixed-task, fixed-model results and do not contain task prompts, candidates, private tests, credentials, or filesystem paths.</footer>
</main><script id="m9-data" type="application/json">{serialized}</script><script>
const d=JSON.parse(document.getElementById('m9-data').textContent), pct=x=>(x*100).toFixed(1)+'%', n=x=>Number(x).toFixed(2), esc=x=>String(x).replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
document.getElementById('facts').textContent=`${{d.final_record_count}} final records · strict verifier passed · ${{d.bootstrap.resamples}} bootstrap resamples`;
document.getElementById('cards').innerHTML=d.groups.map(g=>`<article class="card"><div class="label">${{g.experiment_group}}</div><div class="value">${{pct(g.task_success_rate)}}</div><div class="detail">${{g.task_success_count}} / ${{g.task_count}} task success · official ${{pct(g.official_test_pass_rate)}}</div></article>`).join('');
document.getElementById('groups').innerHTML=d.groups.map(g=>`<tr><td><strong>${{g.experiment_group}}</strong></td><td><div class="bar"><span style="width:${{g.task_success_rate*100}}%"></span></div> ${{pct(g.task_success_rate)}}</td><td>${{pct(g.official_test_pass_rate)}}</td><td>${{n(g.mean_total_tokens)}}</td><td>${{n(g.mean_latency_seconds)}} s</td><td>${{n(g.mean_state_vector_bytes)}}</td><td>${{n(g.mean_memory_hit_count)}}</td></tr>`).join('');
const wanted=['task_success','official_test_pass_rate']; document.getElementById('comparisons').innerHTML=d.comparisons.filter(x=>wanted.includes(x.metric)).map(x=>{{const c=x.mean_difference>0?'good':x.mean_difference<0?'negative':'neutral'; return `<tr><td>${{x.treatment_group}} - ${{x.control_group}}</td><td>${{esc(x.metric)}}</td><td class="${{c}}">${{n(x.mean_difference)}}</td><td>${{n(x.ci_lower)}} to ${{n(x.ci_upper)}}</td><td>${{x.paired_count}}</td></tr>`}}).join('');
</script></body></html>"""


def build(aggregate_dir: Path, output_dir: Path) -> dict[str, Any]:
    data = dashboard_data(read_inputs(aggregate_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "data.json"
    page_path = output_dir / "index.html"
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    page_path.write_text(page(data), encoding="utf-8")
    return {
        "dashboard_schema_version": "1.0",
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "index_sha256": hashlib.sha256(page_path.read_bytes()).hexdigest(),
        "final_record_count": data["final_record_count"],
        "strict_verifier_valid": data["strict_verifier"]["valid"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(Path(args.aggregate_dir), Path(args.output_dir)), sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"dashboard build failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
