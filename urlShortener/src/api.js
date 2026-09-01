const express = require('express');
const rateLimit = require('express-rate-limit');
const validUrl = require('valid-url');
const db = require('../db');
const cache = require('../cache');
const { encode } = require('../base62');

const router = express.Router();

const shortenLimiter = rateLimit({
  windowMs: Number(process.env.RATE_LIMIT_WINDOW_MS) || 60_000,
  max: Number(process.env.RATE_LIMIT_MAX) || 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many links created from this IP. Try again shortly.' },
});

const insertUrl = db.prepare(
  `INSERT INTO urls (short_code, long_url, creator_ip) VALUES (?, ?, ?)`
);
const setPlaceholder = db.prepare(`UPDATE urls SET short_code = ? WHERE id = ?`);
const findByCode = db.prepare(`SELECT * FROM urls WHERE short_code = ?`);
const findByLongUrl = db.prepare(`SELECT * FROM urls WHERE long_url = ? ORDER BY id LIMIT 1`);

router.post('/shorten', shortenLimiter, (req, res) => {
  const { url, custom_code } = req.body || {};

  if (!url || !validUrl.isWebUri(url)) {
    return res.status(400).json({ error: 'Please provide a valid http(s) URL.' });
  }

  const existing = findByLongUrl.get(url);
  if (existing && !custom_code) {
    return res.json({
      short_code: existing.short_code,
      short_url: `${process.env.BASE_URL}/${existing.short_code}`,
      long_url: existing.long_url,
      created: false,
    });
  }

  if (custom_code) {
    if (!/^[a-zA-Z0-9_-]{3,20}$/.test(custom_code)) {
      return res.status(400).json({ error: 'Custom code must be 3-20 alphanumeric characters.' });
    }
    if (findByCode.get(custom_code)) {
      return res.status(409).json({ error: 'That custom code is already taken.' });
    }
    insertUrl.run(custom_code, url, req.ip);
    return res.status(201).json({
      short_code: custom_code,
      short_url: `${process.env.BASE_URL}/${custom_code}`,
      long_url: url,
      created: true,
    });
  }

  const info = insertUrl.run('__pending__', url, req.ip);
  const shortCode = encode(info.lastInsertRowid);
  setPlaceholder.run(shortCode, info.lastInsertRowid);

  res.status(201).json({
    short_code: shortCode,
    short_url: `${process.env.BASE_URL}/${shortCode}`,
    long_url: url,
    created: true,
  });
});

module.exports = router;