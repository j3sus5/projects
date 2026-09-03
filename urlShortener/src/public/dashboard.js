const form = document.getElementById('shorten-form');
const input = document.getElementById('url-input');
const result = document.getElementById('result');
const errorBox = document.getElementById('error');
const linksBody = document.getElementById('links-body');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  result.classList.remove('visible');
  result.innerHTML = '';
  errorBox.textContent = '';

  try {
    const res = await fetch('/api/shorten', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: input.value }),
    });
    const data = await res.json();

    if (!res.ok) {
      errorBox.textContent = data.error || 'Something went wrong.';
      return;
    }

    result.innerHTML = `
      <a href="${data.short_url}" target="_blank">${data.short_url}</a>
      <button type="button" id="copy-btn">Copy</button>
    `;
    result.classList.add('visible');

    document.getElementById('copy-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(data.short_url);
      const btn = document.getElementById('copy-btn');
      btn.textContent = 'Copied';
      setTimeout(() => (btn.textContent = 'Copy'), 1200);
    });

    input.value = '';
    loadLinks();
  } catch (err) {
    errorBox.textContent = 'Network error — is the server running?';
  }
});

async function loadLinks() {
  try {
    const res = await fetch('/api/links');
    const { links } = await res.json();

    if (!links.length) {
      linksBody.innerHTML = '<tr><td colspan="3" class="empty">No links yet.</td></tr>';
      return;
    }

    linksBody.innerHTML = links
      .map(
        (l) => `
      <tr>
        <td><a href="/${l.short_code}" target="_blank">/${l.short_code}</a></td>
        <td class="url-cell" title="${l.long_url}">${l.long_url}</td>
        <td class="clicks-cell">${l.clicks}</td>
      </tr>`
      )
      .join('');
  } catch (err) {
    linksBody.innerHTML = '<tr><td colspan="3" class="empty">Failed to load links.</td></tr>';
  }
}

loadLinks();
window.addEventListener('focus', loadLinks);