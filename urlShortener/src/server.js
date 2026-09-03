require('dotenv').config();
const express = require('express');
const path = require('path');

const apiRoutes = require('./routes/api');
const redirectRoutes = require('./routes/redirect');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

//app.set('trust proxy', true);
app.set('trust proxy', process.env.TRUST_PROXY_HOPS ? Number(process.env.TRUST_PROXY_HOPS) : false);

app.use('/api', apiRoutes);
app.use('/', redirectRoutes);

app.use((req, res) => res.status(404).send('Not found.'));

app.listen(PORT, () => {
  console.log(`URL shortener running on ${process.env.BASE_URL || `http://localhost:${PORT}`}`);
});