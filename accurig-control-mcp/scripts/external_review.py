"""Validate recorded browser evidence, not a vision model or provider attestation."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

PROMPT = ('Revisa este modelo 3D para detectar errores visuales de anatomía, '
          'proporciones, uniones y superficie. Indica dónde ves cada defecto y qué '
          'se observa. Si alguna zona no se puede evaluar, dilo.')

def require(ok, error):
    if not ok:
        raise ValueError(error)

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def image(p):
    require(Path(p).suffix.lower() != '.zip', 'ZIP_NOT_A_REVIEW_EVIDENCE')
    with Path(p).open('rb') as f:
        h = f.read(16)
    require(h.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff')) or
            (h[:4] == b'RIFF' and h[8:12] == b'WEBP'), 'REVIEW_IMAGE_REQUIRED')

def validate(report_path, source_sha256, evidence, required_views, builder_id,
             approval_path=None, require_approval=True):
    """Return blockers and hashed dependencies. All provider text stays unmodified."""
    require(report_path, 'GEMINI_BROWSER_REVIEW_REQUIRED')
    r = read(report_path)
    require(r.get('schema') == 'gemini-browser-review/1', 'EXTERNAL_REVIEW_SCHEMA_REQUIRED')
    require(r.get('source_sha256') == source_sha256, 'EXTERNAL_REVIEW_SOURCE_CHANGED')
    require(r.get('provider') == 'Gemini' and r.get('transport') == 'browser',
            'GEMINI_BROWSER_ONLY_NO_CLI')
    require(r.get('reviewer_id') and r['reviewer_id'] != builder_id,
            'EXTERNAL_REVIEWER_REQUIRED')
    require(r.get('account_verified') is True, 'REVIEW_ACCOUNT_UNVERIFIED')
    selection = r.get('model_selection', {})
    selected = selection.get('selected', '')
    available = selection.get('available_flash_models', [])
    def version(name):
        match = re.fullmatch(r'(?:Gemini\s+)?(\d+(?:\.\d+)+)\s+Flash', name, re.I)
        return tuple(map(int, match.group(1).split('.'))) if match else None
    def flash_family(name):
        return isinstance(name, str) and re.fullmatch(r'(?:Gemini\s+)?\d+(?:\.\d+)+\s+Flash(?:-Lite)?',name,re.I)
    require(isinstance(available, list) and available and
            all(flash_family(n) for n in available),
            'OBSERVED_FLASH_CATALOG_REQUIRED')
    full_versions=[version(n) for n in available if version(n) is not None]
    normal_selection=(version(selected) is not None and selected in available and
                      full_versions and version(selected)==max(full_versions) and
                      selection.get('latest_available_verified') is True)
    authorization_path=selection.get('user_authorization_path') if not normal_selection else None
    authorization=None
    if not normal_selection:
        require(authorization_path and flash_family(selected) and selected in available,
                'LATEST_AVAILABLE_FLASH_REQUIRED')
        authorization=read(authorization_path)
        require(authorization.get('schema')=='user-model-choice/1' and
                authorization.get('source_sha256')==source_sha256 and
                authorization.get('selected')==selected and
                authorization.get('actor')=='user' and
                authorization.get('status')=='authorized' and
                authorization.get('message_reference') and authorization.get('authorization_text'),
                'EXACT_USER_MODEL_CHOICE_REQUIRED')
    u = urlparse(r.get('session_url', ''))
    require(u.scheme == 'https' and u.hostname == 'gemini.google.com' and
            re.fullmatch(r'/app/[a-zA-Z0-9_-]+', u.path), 'ACTUAL_GEMINI_CONVERSATION_REQUIRED')
    files = {str(Path(report_path).resolve(strict=True)): sha(report_path)}
    def track(p):
        require(isinstance(p, str) and p and Path(p).suffix.lower() != '.zip',
                'REVIEW_EVIDENCE_PATH_REQUIRED')
        files[str(Path(p).resolve(strict=True))] = sha(p)
        return p
    if authorization is not None:
        track(authorization_path)
        track(authorization.get('evidence_path'))
    for key in ('selector_evidence', 'response_evidence'):
        image(track(r.get(key)))
    prompt = Path(track(r.get('prompt_path'))).read_text(encoding='utf-8-sig').strip()
    require(prompt == PROMPT, 'SIMPLE_UNBIASED_PROMPT_REQUIRED')
    raw = Path(track(r.get('raw_response_path'))).read_text(encoding='utf-8-sig').strip()
    require(len(raw) >= 20, 'ACTUAL_GEMINI_RESPONSE_REQUIRED')
    uploaded = r.get('reviewed_images', {})
    require(isinstance(uploaded, dict) and uploaded, 'ACTUAL_REVIEW_ATTACHMENTS_REQUIRED')
    for p, h in uploaded.items():
        image(track(p))
        require(h == sha(p), 'EXTERNAL_REVIEW_ATTACHMENT_CHANGED')
    require(isinstance(r.get('findings'), list) and
            isinstance(r.get('limitations'), list), 'EXTERNAL_FINDINGS_AND_LIMITATIONS_REQUIRED')
    status = r.get('status')
    require(status in {'passed', 'failed', 'needs_review', 'unavailable'}, 'EXTERNAL_REVIEW_PENDING')
    blockers = []
    if status != 'passed' or r['limitations']:
        blockers.append('EXTERNAL_REVIEW_NOT_ACCEPTED')
    for f in r['findings']:
        require(isinstance(f, dict) and f.get('status') in {'open', 'resolved'} and
                f.get('location') and f.get('observation'), 'CONCRETE_EXTERNAL_FINDING_REQUIRED')
        # A response that found a defect cannot be cleared by changing its local status.
        blockers.append('EXTERNAL_FINDINGS_REQUIRE_NEW_REVIEW')
    if not blockers:
        for view in required_views:
            require(view in evidence and uploaded.get(evidence[view]) == sha(evidence[view]),
                    'EXTERNAL_REVIEW_VIEW_MISSING:' + view)
    if require_approval and not blockers:
        require(approval_path, 'USER_APPROVAL_REQUIRED')
        a = read(track(str(approval_path)))
        require(a.get('source_sha256') == source_sha256 and
                a.get('status') == 'approved' and a.get('actor') == 'user',
                'EXACT_MODEL_USER_APPROVAL_REQUIRED')
        require(a.get('message_reference') and a.get('approval_text'), 'REAL_USER_APPROVAL_EVIDENCE_REQUIRED')
        track(a.get('evidence_path'))
    return {'blockers': blockers, 'files': files, 'model': selected,
            'session_url': r['session_url'], 'status': status}
