function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, phone, address, details, job_type, job_done_by_date, preferred_time } = req.body ?? {};

  if (!name || !phone || !address) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  const rows = [
    ['Name',           name],
    ['Phone',          phone],
    ['Address',        address],
    ['Job Type',       job_type],
    ['Preferred Date', job_done_by_date],
    ['Preferred Time', preferred_time],
    ...(details ? [['Details', details]] : []),
  ]
    .map(([k, v]) => `<tr><td style="padding:6px 16px 6px 0;color:#666;white-space:nowrap"><strong>${esc(k)}</strong></td><td style="padding:6px 0">${esc(v)}</td></tr>`)
    .join('');

  const html = `
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto">
      <h2 style="margin-bottom:4px">New Quote Request</h2>
      <p style="color:#666;margin-top:0">Creek Pressure Washing</p>
      <table style="border-collapse:collapse;width:100%">${rows}</table>
    </div>`;

  const resendRes = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'Creek Pressure Washing <us@creekpressurewashing.com>',
      to: ['j7beatss@gmail.com'],
      subject: `New quote request — ${name}`,
      html,
    }),
  });

  if (!resendRes.ok) {
    const text = await resendRes.text();
    console.error('Resend error:', text);
    return res.status(500).json({ error: 'Failed to send' });
  }

  return res.status(200).json({ success: true });
}
