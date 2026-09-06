const crypto = require('crypto');
const Fintech = require('../models/Fintech');
const jwt = require('jsonwebtoken');

// Bank name prefixes for auto-generation
const BANK_PREFIXES = [
  'PHC', 'KAC', 'ACE', 'ZEN', 'OPT', 'NXT', 'FLX', 'ARC', 'VLT', 'PRM',
];
const BANK_SUFFIXES = [
  'Bank', 'Bank Metro', 'Bank Plus', 'Bank Direct', 'Bank Pro',
];

// Generate a random bank code between 100–999 that isn't already taken
const generateUniqueBankCode = async () => {
  let bankCode;
  let exists = true;
  while (exists) {
    bankCode = String(Math.floor(Math.random() * 900) + 100);
    exists = await Fintech.findOne({ bankCode });
  }
  return bankCode;
};

const generateBankName = (prefix) => {
  const suffix = BANK_SUFFIXES[Math.floor(Math.random() * BANK_SUFFIXES.length)];
  return `${prefix} ${suffix}`;
};

// ─── POST /api/fintech/onboard ────────────────────────────────────────────────
const onboardFintech = async (req, res) => {
  try {
    const { name, email } = req.body;

    // Basic validation
    if (!name || !email) {
      return res.status(400).json({ message: 'Name and email are required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ message: 'Invalid email' });
    }

    // Check if fintech already exists — return existing credentials
    const existing = await Fintech.findOne({ email: email.toLowerCase() });
    if (existing) {
      return res.status(400).json({
        apiKey: existing.apiKey,
        apiSecret: existing.apiSecret,
        bankCode: existing.bankCode,
        bankName: existing.bankName,
        message: 'Fintech already onboarded',
      });
    }

    // Generate credentials
    const apiKey = crypto.randomBytes(16).toString('hex');
    const apiSecret = crypto.randomBytes(32).toString('hex');
    const bankCode = await generateUniqueBankCode();
    const prefix = BANK_PREFIXES[Math.floor(Math.random() * BANK_PREFIXES.length)];
    const bankName = generateBankName(prefix);

    // Save to database
    const fintech = await Fintech.create({
      name,
      email,
      apiKey,
      apiSecret,
      bankCode,
      bankName,
    });

    return res.status(201).json({
      apiKey: fintech.apiKey,
      apiSecret: fintech.apiSecret,
      bankCode: fintech.bankCode,
      bankName: fintech.bankName,
    });
  } catch (error) {
    console.error('onboardFintech error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── POST /api/auth/token ─────────────────────────────────────────────────────
const loginFintech = async (req, res) => {
  try {
    const { apiKey, apiSecret } = req.body;

    if (!apiKey || !apiSecret) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Find fintech by apiKey
    const fintech = await Fintech.findOne({ apiKey });
    if (!fintech || fintech.apiSecret !== apiSecret) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Sign the JWT
    const token = jwt.sign(
      {
        fintechId: fintech._id,
        name: fintech.name,
        email: fintech.email,
        bankCode: fintech.bankCode,
        bankName: fintech.bankName,
      },
      process.env.JWT_SECRET,
      { expiresIn: '1h' }
    );

    return res.status(200).json({
      token,
      fintech: {
        name: fintech.name,
        email: fintech.email,
        bankCode: fintech.bankCode,
        bankName: fintech.bankName,
      },
    });
  } catch (error) {
    console.error('loginFintech error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

module.exports = { onboardFintech, loginFintech };
