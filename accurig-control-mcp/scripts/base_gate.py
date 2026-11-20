"""Persistent pre-AccuRIG evidence gate. Does not generate models or pretend to inspect them."""
import argparse, hashlib, json, os, sys, uuid
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from external_review import validate as validate_external

TECH = {'geometry', 'pose', 'shoulders', 'hands', 'finger_separation', 'deformation_topology', 'uv_textures', 'wrist_transition'}
VISUAL = {'identity', 'proportions', 'shoulders', 'hands', 'finger_separation', 'materials', 'wrist_transition'}
VIEWS = {'front', 'left', 'right', 'back', 'hands'} | {f'{hand}_wrist_{view}' for hand in ('left', 'right') for view in ('front', 'profile', 'palm', 'back')}
STATES = {'passed', 'warning', 'failed', 'unverified'}

def require(value, reason):
    if not value: raise ValueError(reason)

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def canonical(p): return str(Path(p).resolve(strict=True))
def model(p):
    p = canonical(p)
    require(Path(p).suffix.lower() in {'.obj', '.fbx', '.glb', '.gltf'}, 'BASE_MODEL_FORMAT_REQUIRED')
    return {'path': p, 'sha256': sha(p)}
def save(p, data):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    temp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('x', encoding='utf8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(temp,p)
    finally:
        temp.unlink(missing_ok=True)

@contextmanager
def locked(p):
    lock=Path(str(p)+'.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try: yield
    finally: os.close(fd);lock.unlink()

def init(case, source, references, builder):
    source=model(source)
    require(all(Path(p).suffix.lower()!='.zip' for p in references),'ZIP_NOT_A_BASE_REFERENCE')
    refs={canonical(p):sha(p) for p in references}
    require(refs and builder.strip(), 'ORIGINAL_REFERENCES_AND_BUILDER_REQUIRED')
    with locked(case):
        if Path(case).exists():
            old=read(case)
            require(old['source']==source and old['references']==refs, 'CASE_IDENTITY_CHANGED')
            return old # never reset attempts by starting again
        value={'schema':'base-gate/1','source':source,'references':refs,'builder_id':builder,
               'artifacts':[source], 'attempts':[], 'reviews':{},'blender':None,'created_at':now()}
        save(case,value);return value

def assert_sources(c):
    require(sha(c['source']['path'])==c['source']['sha256'],'ORIGINAL_CHANGED')
    for p,h in c['references'].items(): require(sha(p)==h,'REFERENCE_CHANGED')

def checks(report, required):
    found=report.get('checks',{})
    require(required <= set(found),'INCOMPLETE_BASE_CHECKS')
    flags=[]
    for key in required:
        row=found[key]
        require(row.get('status') in STATES and len(row.get('observation','').strip())>=10,'INVALID_BASE_CHECK:'+key)
        if row['status'] in {'failed','unverified'}: flags.append('reject')
        elif row['status']=='warning':
            require(isinstance(row.get('rig_blocking'),bool) and len(row.get('mitigation','').strip())>=10,'WARNING_RATIONALE_REQUIRED')
            flags.append('reject' if row['rig_blocking'] else 'warning')
    return flags

def review(case, input_path, technical_path, visual_path):
    with locked(case):
        c=read(case);assert_sources(c);m=model(input_path)
        require(m in c['artifacts'],'UNREGISTERED_BASE_ARTIFACT')
        t,v=read(technical_path),read(visual_path)
        require(canonical(technical_path)!=canonical(visual_path),'SEPARATE_REPORTS_REQUIRED')
        for r in (t,v): require(r.get('source_sha256')==m['sha256'] and r.get('reviewer_id'),'REPORT_SOURCE_MISMATCH')
        require(t['reviewer_id']!=c['builder_id'],'INDEPENDENT_TECHNICAL_REVIEW_REQUIRED')
        producers={a['worker_id'] for a in c['attempts'] if a.get('output',{}).get('sha256')==m['sha256']}
        require(not {t['reviewer_id'],v['reviewer_id']}.intersection(producers),'WORKER_CANNOT_APPROVE_OWN_OUTPUT')
        native_hashes={c['source']['sha256']}|{a['output']['sha256'] for a in c['attempts'] if a.get('output')}
        if m['sha256'] not in native_hashes:
            require(c.get('blender') and c['blender']['feasible'] and sha(c['blender']['report'])==c['blender']['sha256'],'BLENDER_FEASIBILITY_REQUIRED')
        flags=checks(t,TECH)+checks(v,VISUAL)
        met=t.get('metrics',{})
        for key in ['vertices','triangles']:
            require(isinstance(met.get(key),int) and not isinstance(met[key],bool) and met[key]>0,'INVALID_BASE_METRICS')
        require(isinstance(met.get('finite_positions'),bool),'FINITE_POSITION_CHECK_REQUIRED')
        if not met['finite_positions']:flags.append('reject')
        # Passing requires actual coverage. A rejection may stop at the first defect.
        evidence=v.get('evidence',{})
        if 'reject' not in flags: require(VIEWS <= set(evidence),'MULTIVIEW_BASE_REVIEW_REQUIRED')
        require(evidence,'VISUAL_EVIDENCE_REQUIRED')
        require(len(set(evidence.values()))==len(evidence),'DISTINCT_VIEWS_REQUIRED')
        require(isinstance(t.get('dependencies'),list),'EXTERNAL_DEPENDENCY_INVENTORY_REQUIRED')
        files={canonical(technical_path):sha(technical_path),canonical(visual_path):sha(visual_path)}
        external = None
        if 'reject' not in flags:
            external = validate_external(v.get('external_review_path'), m['sha256'], evidence,
                                         VIEWS, c['builder_id'], v.get('user_approval_path'))
            files.update(external['files'])
            if external['blockers']: flags.append('reject')
        for p in evidence.values():
            with Path(p).open('rb') as stream: header=stream.read(16)
            require(header.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff')) or (header[:4]==b'RIFF' and header[8:12]==b'WEBP'),'ACTUAL_IMAGE_EVIDENCE_REQUIRED')
        if c.get('blender'):
            files[c['blender']['report']]=c['blender']['sha256']
        for p in [*evidence.values(),*t.get('dependencies',[])]:
            require(Path(p).suffix.lower()!='.zip','ZIP_NOT_A_BASE_EVIDENCE')
            files[canonical(p)]=sha(p)
        verdict='discard' if 'reject' in flags else 'pass_warning' if 'warning' in flags else 'pass_total'
        receipt={'schema':'base-gate/2','case':str(Path(case).resolve()),'model':m,'verdict':verdict,
                 'files':files,'reviewed_at':now(),'review_id':uuid.uuid4().hex,
                 'visual_report_path':canonical(visual_path),
                 'external_review':external,
                 'next_action':'request_changes_then_meshy' if verdict=='discard' and len(c['attempts'])<3 else 'assess_blender' if verdict=='discard' else 'accurig',
                 'warnings':[{'check':k,**row} for r in (t,v) for k,row in r['checks'].items() if row['status']=='warning']}
        dest=Path(case).parent/('base-review-'+m['sha256']+'.json')
        c['reviews'][m['sha256']]=receipt
        save(case,c);save(dest,receipt)
        return {**receipt,'receipt_path':str(dest.resolve())}


USER_AUTHORITY_SCHEMA = 'base-gate/user-authority/1'

def validate_user_authority(approval_path, input_path):
    """Human approval is authority, never a fabricated reviewer pass."""
    m=model(input_path);a=read(approval_path)
    require(a.get('actor')=='user' and a.get('status')=='approved', 'USER_AUTHORITY_APPROVAL_REQUIRED')
    require(a.get('source_sha256')==m['sha256'], 'USER_AUTHORITY_SOURCE_CHANGED')
    require(a.get('scope')=='base_model_accurig' and
            a.get('decision_authority')=='supersedes_reviewer_verdicts', 'EXPLICIT_USER_AUTHORITY_REQUIRED')
    require(isinstance(a.get('message_reference'),str) and a['message_reference'].strip() and
            isinstance(a.get('approval_text'),str) and a['approval_text'].strip(), 'REAL_USER_APPROVAL_EVIDENCE_REQUIRED')
    evidence=canonical(a.get('evidence_path'))
    require(Path(evidence).suffix.lower()!='.zip' and Path(evidence).is_file() and
            Path(evidence).stat().st_size>0,'REAL_USER_APPROVAL_EVIDENCE_REQUIRED')
    require(Path(m['path']).stat().st_size>0, 'EMPTY_BASE_MODEL')
    return m,{canonical(approval_path):sha(approval_path),evidence:sha(evidence)}

def approve_user(input_path, approval_path, receipt_path, report_paths=()):
    m,files=validate_user_authority(approval_path,input_path)
    require(Path(receipt_path).suffix.lower()=='.json' and str(Path(receipt_path).resolve())!=m['path'],'SEPARATE_AUTHORITY_RECEIPT_REQUIRED')
    require(canonical(approval_path)!=str(Path(receipt_path).resolve()),'SEPARATE_AUTHORITY_RECEIPT_REQUIRED')
    reports=[]
    for report in report_paths:
        r=canonical(report)
        require(Path(r).suffix.lower()!='.zip','ZIP_NOT_A_BASE_EVIDENCE')
        require(r!=str(Path(receipt_path).resolve()),'SEPARATE_AUTHORITY_RECEIPT_REQUIRED')
        files[r]=sha(r);reports.append(r)
    receipt={'schema':USER_AUTHORITY_SCHEMA,'model':m,'verdict':'pass_warning',
             'authority':'user','approval_path':canonical(approval_path),'files':files,
             'reviewed_at':now(),'review_id':uuid.uuid4().hex,'retained_reports':reports,
             'warnings':[{'check':'reviewer_verdicts','observation':
              'User explicitly authorizes this exact base despite reviewer findings or missing review. '
              'Reports remain unchanged; this is not reviewer acceptance.'}],
             'next_action':'accurig','scope':'base_model_accurig'}
    require(str(Path(receipt_path).resolve()) not in files,'SEPARATE_AUTHORITY_RECEIPT_REQUIRED')
    save(receipt_path,receipt)
    return {**receipt,'receipt_path':str(Path(receipt_path).resolve())}

def assert_user_authority(r,input_path):
    require(r.get('authority')=='user' and r.get('verdict')=='pass_warning' and
            r.get('scope')=='base_model_accurig','INVALID_USER_AUTHORITY_RECEIPT')
    m,files=validate_user_authority(r['approval_path'],input_path)
    require(r['model']==m,'BASE_REVIEW_SOURCE_CHANGED')
    for p,h in r['files'].items():require(sha(p)==h,'BASE_EVIDENCE_CHANGED')
    require(all(r['files'].get(p)==h for p,h in files.items()),'USER_AUTHORITY_EVIDENCE_MISSING')
    require(all(p in r['files'] for p in r['retained_reports']),'USER_AUTHORITY_EVIDENCE_MISSING')
    return {'allowed':True,'verdict':'pass_warning','authority':'user',
            'warnings':r['warnings'],'source_sha256':m['sha256']}

def assert_gate(receipt_path, input_path):
    r=read(receipt_path)
    if r.get('schema')==USER_AUTHORITY_SCHEMA:return assert_user_authority(r,input_path)
    c=read(r['case']);assert_sources(c)
    require(r['model']==model(input_path),'BASE_REVIEW_SOURCE_CHANGED')
    require(c['reviews'].get(r['model']['sha256'])==r,'BASE_REVIEW_REPLACED')
    require(r['verdict'] in {'pass_total','pass_warning'},'BASE_MODEL_REJECTED')
    require(r['schema']=='base-gate/2' and r.get('external_review') and
            not r['external_review']['blockers'] and r['external_review']['status']=='passed',
            'GEMINI_BROWSER_REVIEW_REQUIRED')
    for p,h in r['files'].items():require(sha(p)==h,'BASE_EVIDENCE_CHANGED')
    # Recheck the actual third-party contract, not merely a cached "passed" flag.
    visual_path=r.get('visual_report_path')
    require(visual_path in r['files'],'GEMINI_BROWSER_REVIEW_REQUIRED')
    v=read(visual_path)
    current=validate_external(v.get('external_review_path'),r['model']['sha256'],
                              v.get('evidence',{}),VIEWS,c['builder_id'],v.get('user_approval_path'))
    require(current==r['external_review'] and not current['blockers'],'EXTERNAL_REVIEW_CHANGED')
    return {'allowed':True,'verdict':r['verdict'],'warnings':r['warnings'],'source_sha256':r['model']['sha256']}

def reserve(case, worker_id, brief_path):
    with locked(case):
        c=read(case);assert_sources(c)
        require(worker_id and worker_id!=c['builder_id'],'DELEGATED_WORKER_REQUIRED')
        require(c['reviews'] and all(x['verdict']=='discard' for x in c['reviews'].values()),'REMAKE_ONLY_AFTER_REJECTION')
        require(not any(a['state']=='reserved' for a in c['attempts']),'MESHY_ATTEMPT_PENDING')
        require(all(a['state']=='failed' or a['output']['sha256'] in c['reviews'] for a in c['attempts']),'REVIEW_EACH_MESHY_OUTPUT_FIRST')
        require(len(c['attempts'])<3,'MESHY_LIMIT_3_ASSESS_BLENDER')
        a={'id':uuid.uuid4().hex,'number':len(c['attempts'])+1,'state':'reserved','provider':'Meshy',
           'worker_id':worker_id,'brief':canonical(brief_path),'brief_sha256':sha(brief_path),'reserved_at':now()}
        c['attempts'].append(a);save(case,c);return a

def finish(case, attempt_id, provider_job, output_path=None, error=None):
    with locked(case):
        c=read(case);assert_sources(c)
        a=next(x for x in c['attempts'] if x['id']==attempt_id)
        require(a['state']=='reserved','ATTEMPT_ALREADY_FINISHED')
        require(sha(a['brief'])==a['brief_sha256'],'BRIEF_CHANGED')
        require(bool(output_path)!=bool(error),'OUTPUT_OR_ERROR_REQUIRED')
        require(provider_job.strip(),'ACTUAL_PROVIDER_JOB_OR_FAILURE_ID_REQUIRED')
        a.update(provider_job=provider_job,finished_at=now())
        if output_path:
            m=model(output_path)
            require(m not in c['artifacts'],'REUSED_OUTPUT_IS_NOT_REMAKE')
            c['artifacts'].append(m);a.update(state='completed',output=m)
        else:a.update(state='failed',error=error)
        save(case,c);return a

def blender(case, report_path, output_path=None):
    with locked(case):
        c=read(case);assert_sources(c)
        require(len(c['attempts'])==3 and all(a['state']!='reserved' for a in c['attempts']),'EXHAUST_MESHY_FIRST')
        require(all(x['verdict']=='discard' for x in c['reviews'].values()),'ACCEPTED_BASE_EXISTS')
        require(all(a['state']=='failed' or a['output']['sha256'] in c['reviews'] for a in c['attempts']),'REVIEW_EACH_MESHY_OUTPUT_FIRST')
        r=read(report_path)
        hashes={a['sha256'] for a in c['artifacts']}
        require(r.get('source_sha256') in hashes and r.get('reviewer_id') and r['reviewer_id']!=c['builder_id'],'BLENDER_REPORT_SOURCE_REQUIRED')
        require(isinstance(r.get('feasible'),bool) and len(r.get('reason','').strip())>=20,'BLENDER_FEASIBILITY_REQUIRED')
        require(r.get('preserves_identity') is True or r['feasible'] is False,'IDENTITY_PRESERVATION_REQUIRED')
        require(r.get('operations') or r['feasible'] is False,'CONCRETE_REPAIR_PLAN_REQUIRED')
        require('report' not in r and 'sha256' not in r,'RESERVED_FEASIBILITY_FIELDS')
        c['blender']={'report':canonical(report_path),'sha256':sha(report_path),**r}
        if output_path:
            require(r['feasible'],'BLENDER_REPAIR_NOT_FEASIBLE')
            m=model(output_path);require(m not in c['artifacts'],'NEW_REPAIR_COPY_REQUIRED');c['artifacts'].append(m)
        save(case,c);return c['blender']

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['approve-user','init','review','assert','reserve-meshy','finish-meshy','blender','status'])
    p.add_argument('--approval');p.add_argument('--retain-report',action='append',default=[])
    p.add_argument('--case');p.add_argument('--input');p.add_argument('--reference',action='append',default=[])
    for k in ['builder','technical','visual','receipt','worker','brief','attempt','provider-job','output','error','report']:p.add_argument('--'+k)
    a=p.parse_args()
    try:
        if a.command=='approve-user':r=approve_user(a.input,a.approval,a.receipt,a.retain_report)
        elif a.command=='init':r=init(a.case,a.input,a.reference,a.builder)
        elif a.command=='review':r=review(a.case,a.input,a.technical,a.visual)
        elif a.command=='assert':r=assert_gate(a.receipt,a.input)
        elif a.command=='reserve-meshy':r=reserve(a.case,a.worker,a.brief)
        elif a.command=='finish-meshy':r=finish(a.case,a.attempt,a.provider_job,a.output,a.error)
        elif a.command=='blender':r=blender(a.case,a.report,a.output)
        else:r=read(a.case)
        print(json.dumps({'ok':True,'result':r},ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError,StopIteration) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':sys.exit(main())
