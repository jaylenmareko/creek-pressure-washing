// GA4 Analytics — Creek Pressure Washing LLC
// Replace G-XXXXXXXXXX with your Measurement ID from analytics.google.com
const GA_ID = 'G-XXXXXXXXXX';

(function () {
  const s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  document.head.appendChild(s);
})();

window.dataLayer = window.dataLayer || [];
function gtag() { dataLayer.push(arguments); }
window.gtag = gtag;
gtag('js', new Date());
gtag('config', GA_ID, { anonymize_ip: true });

window.trackEvent = function (name, params) {
  if (typeof window.gtag === 'function') {
    window.gtag('event', name, params || {});
  }
};
