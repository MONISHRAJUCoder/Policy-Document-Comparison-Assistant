/**
 * PolicyLens — Frontend Application
 * Handles form submission, loading states, and results rendering
 */

document.getElementById('year').textContent = new Date().getFullYear();

// File input handlers
function setupFileInput(inputId, fileNameId) {
  const input = document.getElementById(inputId);
  const nameEl = document.getElementById(fileNameId);
  input.addEventListener('change', () => {
    if (input.files[0]) {
      nameEl.textContent = '✓ ' + input.files[0].name;
    }
  });
}
setupFileInput('legacyFile', 'legacyFileName');
setupFileInput('modernFile', 'modernFileName');

// Load sample data
document.getElementById('loadSampleBtn').addEventListener('click', async () => {
  const btn = document.getElementById('loadSampleBtn');
  btn.textContent = 'Loading...';
  btn.disabled = true;
  try {
    const res = await fetch('/sample');
    const data = await res.json();
    document.getElementById('legacyText').value = data.legacy;
    document.getElementById('modernText').value = data.modern;
    btn.textContent = '✓ Sample Loaded';
  } catch {
    btn.textContent = 'Load Sample GDPR Migration';
  } finally {
    btn.disabled = false;
  }
});

// Tab navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');
  });
});

// Loading animation steps
let loadingInterval;
function startLoadingAnimation() {
  const steps = ['step1', 'step2', 'step3', 'step4'];
  let current = 0;
  steps.forEach(id => {
    document.getElementById(id).classList.remove('active', 'done');
  });
  document.getElementById('step1').classList.add('active');

  loadingInterval = setInterval(() => {
    if (current < steps.length) {
      document.getElementById(steps[current]).classList.remove('active');
      document.getElementById(steps[current]).classList.add('done');
      current++;
      if (current < steps.length) {
        document.getElementById(steps[current]).classList.add('active');
      }
    }
  }, 4000);
}

function stopLoadingAnimation() {
  clearInterval(loadingInterval);
}

// Form submission
document.getElementById('compareForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const legacyText = document.getElementById('legacyText').value.trim();
  const modernText = document.getElementById('modernText').value.trim();
  const legacyFile = document.getElementById('legacyFile').files[0];
  const modernFile = document.getElementById('modernFile').files[0];

  if (!legacyText && !legacyFile) {
    showError('Please provide the legacy policy document (upload a file or paste text).');
    return;
  }
  if (!modernText && !modernFile) {
    showError('Please provide the modernized policy document (upload a file or paste text).');
    return;
  }

  // Show loading
  document.getElementById('loadingOverlay').style.display = 'flex';
  document.getElementById('analyzeBtn').disabled = true;
  startLoadingAnimation();

  try {
    const formData = new FormData(e.target);
    const response = await fetch('/compare', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(data.error || 'Analysis failed. Please try again.');
    }

    stopLoadingAnimation();
    document.getElementById('loadingOverlay').style.display = 'none';
    document.getElementById('analyzeBtn').disabled = false;

    renderResults(data);

  } catch (err) {
    stopLoadingAnimation();
    document.getElementById('loadingOverlay').style.display = 'none';
    document.getElementById('analyzeBtn').disabled = false;
    showError(err.message);
  }
});

function renderResults(data) {
  const { diff, regulatory_analysis: ra, stats } = data;

  // Show results section
  document.getElementById('results-section').style.display = 'block';
  document.getElementById('nav-results').style.display = 'inline';
  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });

  // Score banner
  const score = ra.modernization_score || 0;
  document.getElementById('modernizationScore').textContent = score + '%';

  const riskEl = document.getElementById('riskChange');
  const riskChange = ra.risk_assessment?.overall_risk_change || 'neutral';
  riskEl.textContent = riskChange.charAt(0).toUpperCase() + riskChange.slice(1);
  riskEl.className = 'score-value risk-value ' + riskChange;

  const totalChanged = stats.additions + stats.deletions + stats.modifications;
  document.getElementById('linesChanged').textContent = totalChanged;
  document.getElementById('similarity').textContent = diff.stats.similarity_percent + '%';

  // Executive Summary
  document.getElementById('execSummaryText').textContent = ra.executive_summary || '';
  const tagsEl = document.getElementById('complianceTags');
  tagsEl.innerHTML = '';
  (ra.compliance_frameworks || []).forEach(fw => {
    const tag = document.createElement('span');
    tag.className = `compliance-tag ${fw.status || 'neutral'}`;
    tag.textContent = fw.framework;
    tag.title = fw.details || '';
    tagsEl.appendChild(tag);
  });

  // Render tabs
  renderDiffView(diff.chunks);
  renderRegulatoryImpact(ra.regulatory_changes || []);
  renderRiskAnalysis(ra.risk_assessment || {});
  renderRecommendations(ra.implementation_recommendations || [], ra.key_improvements || [], ra.compliance_gaps || []);
}

function renderDiffView(chunks) {
  const container = document.getElementById('diffView');
  container.innerHTML = '';

  chunks.forEach(chunk => {
    const div = document.createElement('div');
    div.className = 'diff-chunk ' + chunk.type;

    if (chunk.type === 'equal') {
      div.innerHTML = `<div class="diff-content">${escHtml(chunk.text)}</div>`;
    } else if (chunk.type === 'addition') {
      div.innerHTML = `
        <div class="diff-chunk-header">
          <span>+ Added</span>
          <span>${chunk.line_count} line${chunk.line_count !== 1 ? 's' : ''}</span>
        </div>
        <div class="diff-content">${escHtml(chunk.text)}</div>`;
    } else if (chunk.type === 'deletion') {
      div.innerHTML = `
        <div class="diff-chunk-header">
          <span>− Removed</span>
          <span>${chunk.line_count} line${chunk.line_count !== 1 ? 's' : ''}</span>
        </div>
        <div class="diff-content">${escHtml(chunk.text)}</div>`;
    } else if (chunk.type === 'modification') {
      const legacyHtml = chunk.inline_diff?.legacy || escHtml(chunk.legacy_text);
      const modernHtml = chunk.inline_diff?.modern || escHtml(chunk.modern_text);
      div.innerHTML = `
        <div class="diff-chunk-header">
          <span>≠ Modified</span>
          <span>Lines ${chunk.legacy_start} → ${chunk.modern_start}</span>
        </div>
        <div class="diff-content">
          <div class="diff-side-by-side">
            <div class="diff-side legacy">
              <span class="diff-side-label">Legacy</span>
              ${legacyHtml}
            </div>
            <div class="diff-side modern">
              <span class="diff-side-label">Modernized</span>
              ${modernHtml}
            </div>
          </div>
        </div>`;
    }

    container.appendChild(div);
  });
}

function renderRegulatoryImpact(changes) {
  const container = document.getElementById('regulatoryGrid');
  container.innerHTML = '';

  if (!changes.length) {
    container.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:40px">No regulatory changes detected.</p>';
    return;
  }

  changes.forEach(change => {
    const card = document.createElement('div');
    card.className = 'reg-card';
    card.innerHTML = `
      <div class="reg-card-header">
        <span class="reg-category">${escHtml(change.category || '')}</span>
        <div class="reg-badges">
          <span class="reg-badge ${change.impact || 'medium'}">${change.impact || 'medium'} impact</span>
          <span class="reg-badge ${change.change_type || 'modified'}">${change.change_type || ''}</span>
        </div>
      </div>
      <div class="reg-comparison">
        <div class="reg-stance legacy">
          <span class="reg-stance-label">Legacy</span>
          ${escHtml(change.legacy_stance || '')}
        </div>
        <div class="reg-stance modern">
          <span class="reg-stance-label">Modernized</span>
          ${escHtml(change.modern_stance || '')}
        </div>
      </div>
      <div class="reg-significance">${escHtml(change.regulatory_significance || '')}</div>
    `;
    container.appendChild(card);
  });
}

function renderRiskAnalysis(risk) {
  const container = document.getElementById('riskSection');
  const legacyScore = risk.risk_score_legacy || 0;
  const modernScore = risk.risk_score_modern || 0;

  const eliminated = (risk.key_risks_eliminated || []).map(r =>
    `<li>${escHtml(r)}</li>`).join('');
  const introduced = (risk.new_risks_introduced || []).map(r =>
    `<li>${escHtml(r)}</li>`).join('');

  container.innerHTML = `
    <div class="risk-gauge-row">
      <div class="risk-gauge">
        <div class="gauge-label">Legacy Risk Score</div>
        <div class="gauge-score legacy">${legacyScore}</div>
        <div class="gauge-bar"><div class="gauge-fill legacy" style="width: ${legacyScore}%"></div></div>
        <div class="gauge-sub">Higher = more compliance risk</div>
      </div>
      <div class="risk-gauge">
        <div class="gauge-label">Modernized Risk Score</div>
        <div class="gauge-score modern">${modernScore}</div>
        <div class="gauge-bar"><div class="gauge-fill modern" style="width: ${modernScore}%"></div></div>
        <div class="gauge-sub">Lower = better compliance</div>
      </div>
    </div>
    <div class="risk-lists">
      <div class="risk-list-card">
        <div class="risk-list-title">✅ Risks Eliminated</div>
        <ul class="risk-list eliminated">${eliminated || '<li>None identified</li>'}</ul>
      </div>
      <div class="risk-list-card">
        <div class="risk-list-title">⚠ New Obligations</div>
        <ul class="risk-list introduced">${introduced || '<li>None identified</li>'}</ul>
      </div>
    </div>
    <div class="risk-explanation">${escHtml(risk.risk_explanation || '')}</div>
  `;
}

function renderRecommendations(recs, improvements, gaps) {
  const container = document.getElementById('recommendationsSection');
  container.innerHTML = '';

  // Key improvements
  if (improvements.length) {
    const improveSection = document.createElement('div');
    improveSection.style.cssText = 'margin-bottom:24px';
    improveSection.innerHTML = `
      <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:12px">✅ Key Improvements Made</h3>
      ${improvements.map(i => `
        <div style="background:var(--green-dim);border-radius:6px;padding:10px 14px;font-size:13px;color:var(--text-secondary);margin-bottom:8px;line-height:1.6">
          ${escHtml(i)}
        </div>`).join('')}
    `;
    container.appendChild(improveSection);
  }

  // Compliance gaps
  if (gaps.length) {
    const gapSection = document.createElement('div');
    gapSection.style.cssText = 'margin-bottom:24px';
    gapSection.innerHTML = `
      <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:12px">⚠ Remaining Compliance Gaps</h3>
      ${gaps.map(g => `
        <div style="background:var(--red-dim);border-radius:6px;padding:10px 14px;font-size:13px;color:var(--text-secondary);margin-bottom:8px;line-height:1.6">
          ${escHtml(g)}
        </div>`).join('')}
    `;
    container.appendChild(gapSection);
  }

  // Action items
  if (recs.length) {
    const recsHeader = document.createElement('h3');
    recsHeader.style.cssText = 'font-family:var(--font-display);font-size:18px;margin-bottom:12px';
    recsHeader.textContent = '📋 Implementation Recommendations';
    container.appendChild(recsHeader);

    recs.forEach(rec => {
      const card = document.createElement('div');
      card.className = 'rec-card';
      const priority = (rec.priority || 'short-term').toLowerCase().replace(' ', '-');
      card.innerHTML = `
        <span class="rec-priority ${priority}">${rec.priority || 'Short-term'}</span>
        <div class="rec-content">
          <div class="rec-action">${escHtml(rec.action || '')}</div>
          <div class="rec-rationale">${escHtml(rec.rationale || '')}</div>
        </div>
      `;
      container.appendChild(card);
    });
  }
}

function showError(msg) {
  const toast = document.getElementById('errorToast');
  document.getElementById('errorMessage').textContent = msg;
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 6000);
}

function escHtml(str) {
  if (!str) return '';
  // Preserve inline mark tags from diff engine, escape everything else
  const escaped = String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
  // Re-allow mark tags for inline diff highlighting
  return escaped
    .replace(/&lt;mark class=&quot;del&quot;&gt;/g, '<mark class="del">')
    .replace(/&lt;mark class=&quot;ins&quot;&gt;/g, '<mark class="ins">')
    .replace(/&lt;\/mark&gt;/g, '</mark>');
}
