// ===== NAV =====
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.style.boxShadow = window.scrollY > 20 ? '0 2px 24px rgba(0,0,0,0.35)' : 'none';
}, { passive: true });

const hamburger = document.getElementById('hamburger');
const navMobile = document.getElementById('nav-mobile');
hamburger.addEventListener('click', () => navMobile.classList.toggle('open'));
navMobile.querySelectorAll('a').forEach(a =>
  a.addEventListener('click', () => navMobile.classList.remove('open'))
);

// ===== JOB TYPE TOGGLE =====
document.querySelectorAll('.job-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.job-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('job-type').value = btn.dataset.val;
  });
});

// ===== CALENDAR =====
const MONTHS = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
];
const SLOTS = [
  '9:00 AM','10:00 AM','11:00 AM','12:00 PM',
  '1:00 PM','2:00 PM','3:00 PM','4:00 PM'
];

const today = new Date();
today.setHours(0, 0, 0, 0);

let calYear  = today.getFullYear();
let calMonth = today.getMonth();
let selDate  = null;
let selTime  = null;

function renderCal() {
  document.getElementById('cal-month-label').textContent =
    `${MONTHS[calMonth]} ${calYear}`;

  const firstDay   = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const grid = document.getElementById('cal-grid');

  let html = '';
  for (let i = 0; i < firstDay; i++) {
    html += '<div class="cal-cell blank"></div>';
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dt      = new Date(calYear, calMonth, d);
    const isPast  = dt < today;
    const isSel   = selDate && selDate.getTime() === dt.getTime();
    const isTodayCell = dt.getTime() === today.getTime();

    let cls = 'cal-cell';
    if (isPast)      cls += ' disabled';
    if (isSel)       cls += ' selected';
    if (isTodayCell && !isSel) cls += ' is-today';

    html += `<div class="${cls}"${!isPast ? ` data-ts="${dt.getTime()}"` : ''}>${d}</div>`;
  }
  grid.innerHTML = html;

  grid.querySelectorAll('.cal-cell:not(.disabled):not(.blank)').forEach(cell => {
    cell.addEventListener('click', () => {
      selDate = new Date(parseInt(cell.dataset.ts));
      selTime = null;
      document.getElementById('input-date').value = '';
      document.getElementById('input-time').value = '';
      renderCal();
      renderTimes();
    });
  });
}

function renderTimes() {
  const wrap = document.getElementById('time-wrap');
  const grid = document.getElementById('time-grid');
  if (!selDate) { wrap.style.display = 'none'; return; }

  wrap.style.display = 'block';
  grid.innerHTML = SLOTS.map(t =>
    `<button type="button" class="time-slot${selTime === t ? ' selected' : ''}" data-t="${t}">${t}</button>`
  ).join('');

  grid.querySelectorAll('.time-slot').forEach(btn => {
    btn.addEventListener('click', () => {
      selTime = btn.dataset.t;
      document.getElementById('input-date').value =
        selDate.toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' });
      document.getElementById('input-time').value = selTime;
      renderTimes();
    });
  });
}

// Month navigation — don't allow going before current month
document.getElementById('cal-prev').addEventListener('click', () => {
  if (calMonth === 0) { calMonth = 11; calYear--; } else calMonth--;
  const minYear = today.getFullYear(), minMonth = today.getMonth();
  if (calYear < minYear || (calYear === minYear && calMonth < minMonth)) {
    calYear = minYear; calMonth = minMonth;
  }
  renderCal();
});

document.getElementById('cal-next').addEventListener('click', () => {
  if (calMonth === 11) { calMonth = 0; calYear++; } else calMonth++;
  renderCal();
});

// ===== FORM SUBMIT =====
const form        = document.getElementById('quote-form');
const formSuccess = document.getElementById('form-success');
const formError   = document.getElementById('form-error');

form.addEventListener('submit', async e => {
  e.preventDefault();
  if (!selDate || !selTime) {
    formError.textContent = 'Please select a date and time before submitting.';
    formError.style.display = 'block';
    formError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }
  formError.style.display = 'none';

  const submitBtn = form.querySelector('.btn-submit');
  submitBtn.textContent = 'Sending…';
  submitBtn.disabled = true;

  try {
    const payload = {
      name:             form.querySelector('[name="name"]').value,
      phone:            form.querySelector('[name="phone"]').value,
      address:          form.querySelector('[name="address"]').value,
      details:          form.querySelector('[name="details"]').value,
      job_type:         form.querySelector('[name="job_type"]').value,
      job_done_by_date: form.querySelector('[name="job_done_by_date"]').value,
      preferred_time:   form.querySelector('[name="preferred_time"]').value,
    };

    const res = await fetch('/api/quote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (!res.ok || !result.success) throw new Error('Submission failed');

  } catch (_) {
    submitBtn.textContent = 'GET A FREE QUOTE →';
    submitBtn.disabled = false;
    formError.textContent = 'Something went wrong — please call (620) 291-4583 or email us@creekpressurewashing.com.';
    formError.style.display = 'block';
    return;
  }

  document.getElementById('success-msg').innerHTML = 'We will contact you within 24 hours.';
  form.style.display = 'none';
  formSuccess.style.display = 'block';
});

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});

// Init calendar
renderCal();
