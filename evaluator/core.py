from __future__ import annotations

import csv, hashlib, json
from pathlib import Path
from typing import Any

BLOCKED = {"hidden_reference_tests", "canonical_solution", "reference_solution", "test", "contract", "api_key", "secret", "authorization"}

def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def scan(input_dir: Path, strict: bool = True) -> list[dict]:
    runs=[]
    for summary_path in sorted(input_dir.rglob("run_summary.json")):
        root=summary_path.parent; plan_path=root/'sequence_plan.json'; rounds_path=root/'rounds.jsonl'
        if not plan_path.is_file() or not rounds_path.is_file():
            if strict: raise ValueError(f"incomplete run artifact: {root}")
            continue
        plan=json.loads(plan_path.read_text(encoding='utf-8')); summary=json.loads(summary_path.read_text(encoding='utf-8'))
        rounds=[json.loads(line) for line in rounds_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if BLOCKED & set().union(*(set(item) for item in rounds)) or BLOCKED & set(plan): raise ValueError("leakage field in raw run")
        if strict and (len(rounds)!=summary['executed_rounds'] or len(rounds)!=plan['total_rounds'] or summary['planned_rounds']!=plan['total_rounds']): raise ValueError("round count mismatch")
        indices=[item['global_round_index'] for item in rounds]
        if strict and (len(indices)!=len(set(indices)) or indices!=list(range(1,len(rounds)+1))): raise ValueError("invalid global round order")
        dataset=plan['source_dataset']; mode=summary['mode']; succeeded=sum(item['status']=='succeeded' for item in rounds)
        messages=sum(item.get('emitted_message_count',0) for item in rounds); events=sum(item.get('emitted_event_count',0) for item in rounds)
        groups={}
        for item in rounds:
            bucket=groups.setdefault(item['group_id'], {'dataset':dataset,'mode':mode,'seed':summary['seed'],'group_id':item['group_id'],'rounds':0,'succeeded_rounds':0,'emitted_message_count':0,'emitted_event_count':0})
            bucket['rounds']+=1; bucket['succeeded_rounds']+=item['status']=='succeeded'; bucket['emitted_message_count']+=item.get('emitted_message_count',0); bucket['emitted_event_count']+=item.get('emitted_event_count',0)
        runs.append({'dataset':dataset,'mode':mode,'seed':summary['seed'],'run_id':summary['run_id'],'task_plan_sha256':summary['task_plan_sha256'],'deterministic_result_sha256':summary['deterministic_result_sha256'],'planned_rounds':summary['planned_rounds'],'executed_rounds':summary['executed_rounds'],'succeeded_rounds':succeeded,'failed_rounds':sum(item['status']=='failed' for item in rounds),'skipped_rounds':summary['skipped_rounds'],'success_rate':succeeded/summary['planned_rounds'] if summary['planned_rounds'] else None,'completion_rate':summary['executed_rounds']/summary['planned_rounds'] if summary['planned_rounds'] else None,'failure_rate':sum(item['status']=='failed' for item in rounds)/summary['planned_rounds'] if summary['planned_rounds'] else None,'emitted_message_count':messages,'emitted_event_count':events,'protocol_event_count':events if mode=='protocol' else None,'average_messages_per_round':messages/len(rounds) if rounds else None,'average_events_per_round':events/len(rounds) if rounds else None,'actual_token_count':{'value':None,'available':False,'reason':'no_real_llm_usage'},'estimated_token_count':{'value':None,'available':False,'reason':'safe_message_text_not_recorded'},'wall_time_seconds':{'value':None,'available':False,'reason':'not_recorded_in_mock_runtime'},'groups':list(groups.values()),'tasks':[{'dataset':dataset,'mode':mode,'seed':summary['seed'],'task_id':item['task_id'],'function_name':item['function_name'],'group_id':item['group_id'],'status':item['status'],'emitted_message_count':item.get('emitted_message_count',0),'emitted_event_count':item.get('emitted_event_count',0)} for item in rounds]})
    return runs

def evaluate(input_dir: Path, output_dir: Path, strict: bool=True) -> dict:
    runs=scan(input_dir,strict); comparisons=[]
    for dataset in sorted({run['dataset'] for run in runs}):
        text=next((x for x in runs if x['dataset']==dataset and x['mode']=='text'),None); protocol=next((x for x in runs if x['dataset']==dataset and x['mode']=='protocol'),None)
        valid=bool(text and protocol and text['seed']==protocol['seed'] and text['task_plan_sha256']==protocol['task_plan_sha256'] and text['planned_rounds']==protocol['planned_rounds'])
        for metric in ('success_rate','emitted_message_count','emitted_event_count'):
            a=text[metric] if text else None; b=protocol[metric] if protocol else None
            comparisons.append({'dataset':dataset,'metric':metric,'text_value':a,'protocol_value':b,'comparison_valid':valid,'absolute_difference':b-a if valid else None,'relative_change_percent':((b-a)/a*100) if valid and a else None,'reduction_percent':((a-b)/a*100) if valid and a else None})
    groups=[group for run in runs for group in run['groups']]; tasks=[task for run in runs for task in run['tasks']]
    manifest={'schema_version':'1.0','evaluator_version':'m3','result_scope':'mock_validation','conclusion_scope':'infrastructure_and_accounting_validation_only','source_run_paths':sorted(str(path.parent.relative_to(input_dir)) for path in input_dir.rglob('run_summary.json')),'datasets':sorted({run['dataset'] for run in runs}),'modes':sorted({run['mode'] for run in runs}),'seeds':sorted({run['seed'] for run in runs}),'unavailable_metrics':['actual_token_count','estimated_token_count','wall_time_seconds','peak_process_memory_bytes','shared_memory','state_vector']}
    deterministic={'manifest':manifest,'runs':runs,'comparisons':comparisons}; manifest['deterministic_evaluation_sha256']=hashlib.sha256(canonical(deterministic).encode()).hexdigest()
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,data in [('aggregate_runs.json',runs),('aggregate_groups.json',groups),('aggregate_tasks.json',tasks),('comparison_text_protocol.json',comparisons),('evaluation_manifest.json',manifest)]: (output_dir/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    for name,rows in [('runs.csv',runs),('groups.csv',groups),('tasks.csv',tasks),('text_protocol_comparison.csv',comparisons)]:
        fields=sorted({key for row in rows for key,value in row.items() if not isinstance(value,(dict,list))});
        with (output_dir/name).open('w',newline='',encoding='utf-8') as handle:
            writer=csv.DictWriter(handle,fieldnames=fields); writer.writeheader(); writer.writerows([{key:value for key,value in row.items() if key in fields} for row in rows])
    (output_dir/'report.md').write_text('# M3 Mock Evaluation\n\nresult_scope: `mock_validation`\n\nThis report validates infrastructure and accounting only; it does not measure real LLM quality. StateVector, SharedMemory, quality, token usage, time, and memory metrics are unavailable unless recorded.\n',encoding='utf-8')
    return manifest
