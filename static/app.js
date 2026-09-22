const form = document.getElementById('download-form');
const urlInput = document.getElementById('url');
const qualitySelect = document.getElementById('quality');
const formError = document.getElementById('form-error');
const jobsEl = document.getElementById('jobs');
const cookieWarning = document.getElementById('cookie-warning');

function showError(msg) {
  formError.textContent = msg;
  formError.hidden = false;
}

function clearError() {
  formError.hidden = true;
  formError.textContent = '';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();

  const url = urlInput.value.trim();
  const quality = qualitySelect.value;
  const submitBtn = form.querySelector('button');
  submitBtn.disabled = true;

  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality }),
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || 'Something went wrong');
    } else {
      urlInput.value = '';
      refreshJobs();
    }
  } catch (err) {
    showError('Could not reach the server');
  } finally {
    submitBtn.disabled = false;
  }
});

function statusLabel(job) {
  switch (job.status) {
    case 'queued': return 'Queued';
    case 'downloading': return 'Downloading';
    case 'done': return 'Done';
    case 'error': return 'Failed';
    default: return job.status;
  }
}

function renderJob(job) {
  const wrap = document.createElement('div');
  wrap.className = 'job';

  const title = document.createElement('div');
  title.className = 'job-title';
  title.textContent = job.filename || job.url;
  wrap.appendChild(title);

  const track = document.createElement('div');
  track.className = 'progress-track';
  const fill = document.createElement('div');
  fill.className = 'progress-fill';
  if (job.status === 'done') fill.classList.add('done');
  if (job.status === 'error') fill.classList.add('error');
  fill.style.width = `${job.percent || 0}%`;
  track.appendChild(fill);
  wrap.appendChild(track);

  const meta = document.createElement('div');
  meta.className = 'job-meta';

  const left = document.createElement('span');
  left.className = 'status-tag';
  left.textContent = statusLabel(job);

  const right = document.createElement('span');
  if (job.status === 'downloading') {
    const bits = [];
    if (job.percent) bits.push(`${job.percent.toFixed(1)}%`);
    if (job.speed) bits.push(job.speed);
    if (job.eta) bits.push(`ETA ${job.eta}`);
    right.textContent = bits.join(' · ');
  } else if (job.status === 'error') {
    right.textContent = job.error || '';
  } else if (job.status === 'done') {
    right.textContent = job.size || '';
  }

  meta.appendChild(left);
  meta.appendChild(right);
  wrap.appendChild(meta);

  return wrap;
}

async function refreshJobs() {
  try {
    const res = await fetch('/api/jobs');
    const jobs = await res.json();
    jobsEl.innerHTML = '';
    jobs.forEach((job) => jobsEl.appendChild(renderJob(job)));
  } catch (err) {
    // Server not reachable; leave existing UI as-is
  }
}

async function checkCookies() {
  try {
    const res = await fetch('/api/cookies-status');
    const data = await res.json();
    cookieWarning.hidden = !!data.present;
  } catch (err) {
    // ignore
  }
}

checkCookies();
refreshJobs();
setInterval(refreshJobs, 1500);
