require('dotenv').config();
const express = require('express');
const connectDB = require('./config/db');

// Route imports
const fintechRoutes     = require('./routes/fintechRoutes');
const identityRoutes    = require('./routes/identityRoutes');
const accountRoutes     = require('./routes/accountRoutes');
const transactionRoutes = require('./routes/transactionRoutes');

const app = express();

// ── Middleware ────────────────────────────────────────────────────────────────
app.use(express.json()); // Parse incoming JSON request bodies
app.use(express.static('public')); // Serve the frontend UI

// ── Database ──────────────────────────────────────────────────────────────────
connectDB();

// ── Routes ────────────────────────────────────────────────────────────────────
app.use('/api', fintechRoutes);
app.use('/api', identityRoutes);
app.use('/api', accountRoutes);
app.use('/api', transactionRoutes);

// ── Health check ──────────────────────────────────────────────────────────────
app.get('/', (req, res) => {
  res.json({ message: 'NIBSS by Phoenix API is running ✅' });
});

// ── Start server ──────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
