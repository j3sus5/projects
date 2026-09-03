const express = require('express');
const crypto = require('crypto');
const geoip = require('geoip-lite');
const db = require('../db');
const cache = require('../cache');

const router = express.Router();

const findByCode = db.prepare(`SELECT long_url FROM urls WHERE short_code = ?`);
const insertClick = db.prepare(
  `INSERT INTO clicks (short_code, referrer, user_agent, ip_hash, country, city)
   VALUES (?, ?, ?, ?, ?, ?)`
);

function hashIp(ip) {
  return crypto.createHash('sha256').update(ip).digest('hex').slice(0, 16);
}

router.get('/:code', async (req, res, next) => {
  const { code } = req.params;

  if (code === 'favicon.ico' || code.startsWith('api')) return next();

  let longUrl = await cache.get(code);

  if (!longUrl) {
    const row = findByCode.get(code);
    if (!row) return res.status(404).send('Short link not found.');
    longUrl = row.long_url;
    await cache.set(code, longUrl);
  }

  const ip = req.ip || '';
  const geo = geoip.lookup(ip.replace('::ffff:', ''));
  try {
    insertClick.run(
      code,
      req.get('referrer') || null,
      req.get('user-agent') || null,
      hashIp(ip),
      geo?.country || null,
      geo?.city || null
    );
  } catch (err) {
    console.error('Failed to log click:', err.message);
  }

  res.redirect(302, longUrl);
});

module.exports = router;