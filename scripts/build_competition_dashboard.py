from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


FORBIDDEN = {
    "candidate_code", "raw_response", "hidden_reference_tests", "canonical_solution",
    "reference_solution", "official_tests", "expected_output", "private_traceback",
    "api_key", "authorization", "request_ids",
}
SAFE_FIELDS = {
    "experiment_group", "dataset", "group_id", "seed", "record_count", "task_count",
    "task_success", "task_success_rate", "official_test_pass_rate", "parse_success_rate",
    "sandbox_completion_rate", "agent_message_count", "agent_text_message_count",
    "agent_protocol_message_count", "agent_text_characters", "agent_text_tokens",
    "protocol_payload_bytes", "protocol_payload_tokens", "protocol_header_bytes",
    "capability_handshake_count", "capability_handshake_bytes", "reference_id_count",
    "repeated_context_bytes", "deduplicated_context_bytes", "prompt_tokens",
    "completion_tokens", "total_tokens", "provider_latency_seconds", "total_wall_time",
    "state_vector_count", "state_vector_bytes", "equivalent_text_state_bytes",
    "state_compression_ratio", "state_encode_latency", "state_decode_latency",
    "memory_query_count", "memory_candidate_count", "memory_hit_count",
    "memory_accept_count", "memory_reject_count", "memory_abstain_count",
    "memory_reuse_count", "memory_injected_tokens", "memory_injected_bytes",
    "memory_hit_rate", "memory_accept_rate", "memory_effective_reuse_rate",
    "infrastructure_failure", "model_quality_failure",
}
PATH_PATTERN = re.compile(r"(?:[A-Za-z]:\\|/(?:home|Users|root|tmp)/)")
SECRET_PATTERN = re.compile(r"(?i)(?:api[_-]?key\s*[:=]|authorization\s*[:=]|bearer\s+[a-z0-9._-]+)")

METRICS = (
    ("agent_message_count", "Agent 消息数"), ("agent_text_characters", "Agent 文本字符"),
    ("agent_text_tokens", "Agent 文本 Token"), ("protocol_payload_bytes", "Protocol Payload Bytes"),
    ("prompt_tokens", "Prompt Token"), ("completion_tokens", "Completion Token"),
    ("total_tokens", "Total Token"), ("state_vector_count", "StateVector 次数"),
    ("state_vector_bytes", "StateVector Bytes"), ("state_compression_ratio", "StateVector 压缩率"),
    ("memory_hit_count", "Memory 命中"), ("memory_accept_count", "Memory 接受"),
    ("memory_reject_count", "Memory 拒绝"), ("memory_abstain_count", "Memory 放弃"),
    ("memory_reuse_count", "Memory 复用"), ("memory_injected_tokens", "Memory 注入 Token"),
    ("task_success", "任务成功率"), ("task_success_rate", "任务成功率"),
    ("official_test_pass_rate", "official-test 通过率"), ("parse_success_rate", "解析成功率"),
    ("sandbox_completion_rate", "Sandbox 完成率"), ("infrastructure_failure", "基础设施失败"),
    ("provider_latency_seconds", "Provider 延迟（秒）"), ("total_wall_time", "总耗时（秒）"),
)


def recursive_keys(value: Any) -> set[str]:
    """递归返回结构化公开数据中的全部字段名。"""
    if isinstance(value, dict):
        return set(value).union(*(recursive_keys(child) for child in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(recursive_keys(child) for child in value)) if value else set()
    return set()


def _validate_values(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _validate_values(child)
    elif isinstance(value, list):
        for child in value:
            _validate_values(child)
    elif isinstance(value, str) and (PATH_PATTERN.search(value) or SECRET_PATTERN.search(value)):
        raise ValueError("forbidden_public_value")


def _read_json(path: Path) -> Any:
    value = json.loads(path.read_text(encoding="utf-8"))
    forbidden = FORBIDDEN & recursive_keys(value)
    if forbidden:
        raise ValueError("forbidden_public_field:" + ",".join(sorted(forbidden)))
    _validate_values(value)
    return value


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        forbidden = FORBIDDEN & set(reader.fieldnames or ())
        if forbidden:
            raise ValueError("forbidden_public_field:" + ",".join(sorted(forbidden)))
        rows = [{key: row[key] for key in SAFE_FIELDS if key in row} for row in reader]
        _validate_values(rows)
        return rows


def _safe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe = [{key: row[key] for key in SAFE_FIELDS if key in row} for row in rows]
    _validate_values(safe)
    return safe


def _embedded_json(data: dict[str, Any]) -> str:
    """生成不会提前结束 HTML script 节点的确定性 JSON。"""
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e"))


def page(data: dict[str, Any]) -> str:
    """生成仅使用安全 DOM API 的中文离线 Dashboard 页面。"""
    metric_labels = json.dumps(dict(METRICS), ensure_ascii=False, sort_keys=True)
    html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LiteTest-MAS 赛事指标 Dashboard</title><style>
:root{--ink:#182027;--muted:#68747d;--line:#d6dde1;--paper:#fff;--page:#f3f5f6;--green:#087f5b;--blue:#2468a2;--red:#b42318}*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:14px/1.5 Arial,"Microsoft YaHei",sans-serif}header{background:#18313d;color:#fff;padding:20px max(20px,calc((100vw - 1240px)/2));border-bottom:4px solid var(--green)}h1{font-size:24px;margin:0;letter-spacing:0}header p{margin:4px 0 0;color:#d5e0e4}main{max-width:1240px;margin:auto;padding:18px 20px 36px}.toolbar{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:10px;margin-bottom:16px}label{color:var(--muted);font-size:12px}select{display:block;width:100%;margin-top:4px;padding:8px;border:1px solid var(--line);background:#fff}.status{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.card,.panel{background:var(--paper);border:1px solid var(--line);border-radius:6px}.card{padding:12px;min-height:86px}.card strong{display:block;margin-top:4px;overflow-wrap:anywhere}.ok{color:var(--green)}.panel{margin-top:16px;overflow:auto}h2{font-size:17px;margin:18px 0 8px}table{width:100%;border-collapse:collapse;min-width:900px}th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line)}th{background:#f8fafb;color:var(--muted);font-size:12px}.empty{padding:22px;color:var(--muted)}footer{margin-top:16px;color:var(--muted);font-size:12px}@media(max-width:760px){.toolbar,.status{grid-template-columns:1fr 1fr}main{padding:14px 10px}}
</style></head><body><header><h1>LiteTest-MAS 赛事指标 Dashboard</h1><p>公开聚合数据 · 固定任务与固定模型结论</p></header><main>
<div class="toolbar"><label>实验<select id="experiment"></select></label><label>视图<select id="view"></select></label><label>实验组<select id="group"></select></label><label id="dimension-label">筛选<select id="dimension"></select></label></div>
<div id="status" class="status"></div><h2 id="section-title">指标</h2><div class="panel"><table><thead><tr><th>实验组</th><th>维度</th><th>指标</th><th>值</th></tr></thead><tbody id="metrics"></tbody></table><div id="empty" class="empty" hidden>当前筛选没有可用的公开聚合记录。</div></div>
<footer>页面不包含任务 Prompt、候选代码、private tests、原始响应、凭据或文件系统路径。</footer></main>
<script id="dashboard-data" type="application/json">__DATA__</script><script>
"use strict";const DATA=JSON.parse(document.getElementById("dashboard-data").textContent);const LABELS=__LABELS__;
const byId=id=>document.getElementById(id),expSel=byId("experiment"),viewSel=byId("view"),groupSel=byId("group"),dimSel=byId("dimension");
const add=(parent,tag,text,cls)=>{const node=document.createElement(tag);node.textContent=String(text);if(cls)node.className=cls;parent.appendChild(node);return node};
const option=(select,value,label)=>{const node=document.createElement("option");node.value=String(value);node.textContent=String(label);select.appendChild(node)};
const fill=(select,values,allLabel)=>{select.replaceChildren();option(select,"",allLabel);values.forEach(value=>option(select,value,value))};
const unique=(rows,key)=>[...new Set(rows.map(row=>row[key]).filter(value=>value!==undefined&&value!==""&&value!=="unavailable"))].sort();
const shown=value=>value===undefined||value===null||value===""?"unavailable":value;
const current=()=>DATA.experiments[expSel.value];
function renderStatus(){const root=byId("status"),manifest=current().manifest;root.replaceChildren();[["Strict Verifier",manifest.strict_verifier&&manifest.strict_verifier.valid?"通过":"未通过","ok"],["Final records",shown(manifest.final_record_count),""],["Freeze SHA",shown(manifest.freeze_git_sha),""],["Spec hash",shown(manifest.spec_sha256),""]].forEach(item=>{const card=add(root,"div","","card");add(card,"span",item[0]);add(card,"strong",item[1],item[2])})}
function viewRows(){return current()[viewSel.value]||[]}
function configureFilters(){const rows=viewRows();fill(groupSel,unique(rows,"experiment_group"),"全部实验组");const key=viewSel.value==="datasets"?"dataset":viewSel.value==="task_groups"?"group_id":viewSel.value==="seeds"?"seed":"";byId("dimension-label").firstChild.textContent=key==="dataset"?"数据集":key==="group_id"?"任务组":key==="seed"?"Seed":"筛选";fill(dimSel,key?unique(rows,key):[],"全部");dimSel.disabled=!key;dimSel.dataset.key=key}
function renderMetrics(){const body=byId("metrics"),empty=byId("empty"),key=dimSel.dataset.key;body.replaceChildren();let rows=viewRows().filter(row=>(!groupSel.value||String(row.experiment_group)===groupSel.value)&&(!key||!dimSel.value||String(row[key])===dimSel.value));rows.forEach(row=>Object.keys(LABELS).filter(metric=>metric in row).forEach(metric=>{const tr=document.createElement("tr");add(tr,"td",shown(row.experiment_group));add(tr,"td",key?shown(row[key]):"概览");add(tr,"td",LABELS[metric]);add(tr,"td",shown(row[metric]));body.appendChild(tr)}));empty.hidden=rows.length!==0}
function refresh(){configureFilters();renderStatus();renderMetrics()}
Object.entries(DATA.experiments).forEach(([key,value])=>option(expSel,key,value.label));[["groups","概览"],["datasets","数据集"],["task_groups","任务组"],["seeds","Seed"]].forEach(item=>option(viewSel,item[0],item[1]));expSel.addEventListener("change",refresh);viewSel.addEventListener("change",refresh);groupSel.addEventListener("change",renderMetrics);dimSel.addEventListener("change",renderMetrics);refresh();
</script></body></html>"""
    return html.replace("__DATA__", _embedded_json(data)).replace("__LABELS__", metric_labels)


def build_data(m9_dir: Path, m9_1_dir: Path, output_dir: Path) -> dict[str, Any]:
    """从公开聚合产物构建赛事 Dashboard 的统一数据文件。"""
    m9_manifest = _read_json(m9_dir / "analysis_manifest.json")
    m9_1_manifest = _read_json(m9_1_dir / "m9_1_aggregate_manifest.json")
    for name, manifest in (("M9", m9_manifest), ("M9.1", m9_1_manifest)):
        if manifest.get("final_record_count") != 240 or manifest.get("strict_verifier", {}).get("valid") is not True:
            raise ValueError(f"invalid_public_manifest:{name}")

    data = {
        "schema_version": "1.0",
        "experiments": {
            "m9": {
                "label": "M9 正式实验", "manifest": m9_manifest,
                "groups": _read_csv(m9_dir / "quality_cost_tradeoff.csv"),
                "datasets": _read_csv(m9_dir / "dataset_group_summary.csv"),
                "task_groups": _read_csv(m9_dir / "dataset_group_summary.csv"),
                "seeds": _read_csv(m9_dir / "seed_consistency_summary.csv"),
            },
            "m9_1": {
                "label": "M9.1 赛题对齐补充实验", "manifest": m9_1_manifest,
                "groups": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_groups.json")),
                "datasets": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_datasets.json")),
                "task_groups": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_task_groups.json")),
                "seeds": _safe_rows(_read_json(m9_1_dir / "m9_1_aggregate_seeds.json")),
            },
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "data.json"
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    index = output_dir / "index.html"
    index.write_text(page(data), encoding="utf-8")
    return {
        "data_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "index_sha256": hashlib.sha256(index.read_bytes()).hexdigest(),
        "experiment_count": 2,
    }


def main() -> int:
    """执行赛事 Dashboard 公开数据构建命令。"""
    parser = argparse.ArgumentParser(description="构建中文赛事 Dashboard 的公开数据")
    parser.add_argument("--m9-dir", required=True)
    parser.add_argument("--m9-1-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        result = build_data(Path(args.m9_dir), Path(args.m9_1_dir), Path(args.output_dir))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"赛事 Dashboard 数据构建失败：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
