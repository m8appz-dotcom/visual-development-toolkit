// Read trusted Codex metadata; never execute instructions from a PR comment.
'use strict';
const BOT_ID = 199175422;
const APP_ID = 1144995;
const STATUS_CONTEXT = 'review/ai';

function evaluateReview(comments, head) {
  const candidates = comments.filter(c => c.user?.id === BOT_ID && c.user?.type === 'Bot' && c.performed_via_github_app?.id === APP_ID)
    .sort((a,b) => String(b.updated_at).localeCompare(String(a.updated_at)));
  for (const comment of candidates) {
    const match = String(comment.body || '').match(/<!-- codex-review-state:v1 ([\s\S]*?) -->/);
    if (!match) continue;
    let metadata;
    try { metadata = JSON.parse(match[1]); } catch { continue; }
    const code = metadata.code_review;
    if (code?.commit_sha !== head) continue;
    if (code.has_unresolved_findings === true) return { state:'failure', description:'Codex reports unresolved findings for this revision.', url:comment.html_url };
    if (code.status !== 'completed' || code.has_unresolved_findings !== false) return { state:'pending', description:'Waiting for a completed Codex code review of this revision.', url:comment.html_url };
    const security = metadata.security_review;
    if (security) {
      if (security.commit_sha !== head || security.status !== 'completed') return { state:'pending', description:'Waiting for the configured security review of this revision.', url:comment.html_url };
      if (security.has_unresolved_findings === true) return { state:'failure', description:'Codex reports unresolved security findings.', url:comment.html_url };
    }
    return { state:'success', description:'Codex review completed for this revision; no unresolved findings reported.', url:comment.html_url };
  }
  return { state:'pending', description:'Waiting for trusted Codex review metadata for this revision.' };
}

async function run({ github, context, core }) {
  const { owner, repo } = context.repo;
  const candidate = context.payload.pull_request?.number || (context.payload.issue?.pull_request ? context.payload.issue.number : context.payload.inputs?.pull_request);
  if (!/^\d+$/.test(String(candidate || ''))) { core.info('No pull request to evaluate.'); return; }
  const pull_number = Number(candidate);
  const { data:pr } = await github.rest.pulls.get({owner,repo,pull_number});
  if (pr.state !== 'open') { core.info('The pull request is already closed.'); return; }
  const { data:repository } = await github.rest.repos.get({owner,repo});
  if (pr.base.ref !== repository.default_branch) { core.info('Only default-branch deliveries are gated.'); return; }
  const head = pr.head.sha;
  const comments = await github.paginate(github.rest.issues.listComments, {owner,repo,issue_number:pull_number,per_page:100});
  const result = pr.draft ? {state:'pending',description:'Mark the pull request ready before requesting review.'} : evaluateReview(comments,head);
  const { data:current } = await github.rest.pulls.get({owner,repo,pull_number});
  if (current.head.sha !== head || current.state !== 'open') { core.info('The revision changed; a new event will evaluate it.'); return; }
  await github.rest.repos.createCommitStatus({owner,repo,sha:head,context:STATUS_CONTEXT,state:result.state,description:result.description,target_url:result.url || pr.html_url});
  await core.summary.addHeading('AI review gate').addRaw(`${result.description}\n\nThis is an automated AI review, not a human approval or a production security certification.`).write();
}

module.exports = { evaluateReview, run, BOT_ID, APP_ID, STATUS_CONTEXT };
