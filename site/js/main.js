// NAV scroll shadow
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.style.boxShadow = window.scrollY > 20 ? '0 2px 24px rgba(0,0,0,0.4)' : 'none';
}, { passive: true });

// Hamburger menu
const hamburger = document.getElementById('hamburger');
const navMobile = document.getElementById('nav-mobile');
hamburger.addEventListener('click', () => navMobile.classList.toggle('open'));
navMobile.querySelectorAll('a').forEach(a =>
  a.addEventListener('click', () => navMobile.classList.remove('open'))
);

// Quote form — wire up endpoint when ready
const form = document.getElementById('quote-form');
const formSuccess = document.getElementById('form-success');

form.addEventListener('submit', async e => {
  e.preventDefault();
  const btn = form.querySelector('.btn-submit');
  btn.textContent = 'Sending…';
  btn.disabled = true;

  try {
    const payload = {
      name:    form.querySelector('[name="name"]').value,
      phone:   form.querySelector('[name="phone"]').value,
      address: form.querySelector('[name="address"]').value,
      service: form.querySelector('[name="service"]').value,
      details: form.querySelector('[name="details"]').value,
    };

    const res = await fetch('/api/quote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error();
  } catch {
    // Show success state regardless until /api/quote is wired up
  }

  form.style.display = 'none';
  formSuccess.style.display = 'block';
});

// Scroll animations
const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      animObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -48px 0px' });
document.querySelectorAll('[data-animate]').forEach(el => animObserver.observe(el));

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});
