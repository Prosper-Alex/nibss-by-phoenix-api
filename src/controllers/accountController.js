const Account = require('../models/Account');
const Bvn = require('../models/Bvn');
const Nin = require('../models/Nin');

// Generate a unique 10-digit account number
const generateAccountNumber = async () => {
  let accountNumber;
  let exists = true;
  while (exists) {
    // 10-digit random number starting from 1000000000
    accountNumber = String(Math.floor(1000000000 + Math.random() * 9000000000));
    exists = await Account.findOne({ accountNumber });
  }
  return accountNumber;
};

// Normalize a date to YYYY-MM-DD string for comparison
const normalizeDob = (date) => {
  const d = new Date(date);
  return d.toISOString().split('T')[0];
};

// ─── POST /api/account/create ─────────────────────────────────────────────────
const createAccount = async (req, res) => {
  try {
    const { kycType, kycID, dob } = req.body;
    const { fintechId, bankCode, bankName } = req.fintech;

    // Validate required fields
    if (!kycType || !kycID || !dob) {
      return res.status(400).json({ message: 'kycType, kycID and DOB are required' });
    }

    const normalizedType = kycType.toLowerCase();
    if (!['bvn', 'nin'].includes(normalizedType)) {
      return res.status(400).json({ message: 'Invalid kycType. Use BVN or NIN' });
    }

    // Check if this KYC ID is already linked to an account under this fintech
    const duplicate = await Account.findOne({ fintechId, kycID, kycType: normalizedType });
    if (duplicate) {
      return res.status(400).json({ message: `${normalizedType} already linked to an account` });
    }

    let identityRecord;
    let accountName;

    if (normalizedType === 'bvn') {
      identityRecord = await Bvn.findOne({ bvn: kycID });
      if (!identityRecord || normalizeDob(identityRecord.dob) !== dob) {
        return res.status(400).json({ message: 'bvn and DOB do not match' });
      }
      accountName = `${identityRecord.firstName} ${identityRecord.lastName}`;
    } else {
      identityRecord = await Nin.findOne({ nin: kycID });
      if (!identityRecord || normalizeDob(identityRecord.dob) !== dob) {
        return res.status(400).json({ message: 'nin and DOB do not match' });
      }
      accountName = `${identityRecord.firstName} ${identityRecord.lastName}`;
    }

    const accountNumber = await generateAccountNumber();

    const account = await Account.create({
      accountNumber,
      accountName,
      fintechId,
      bankCode,
      bankName,
      kycType: normalizedType,
      kycID,
    });

    return res.status(201).json({
      message: 'Account created successfully',
      accountNumber: account.accountNumber,
      bankCode: account.bankCode,
      bankName: account.bankName,
      balance: account.balance,
    });
  } catch (error) {
    console.error('createAccount error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── GET /api/accounts ────────────────────────────────────────────────────────
const getAllAccounts = async (req, res) => {
  try {
    const { fintechId } = req.fintech;

    const accounts = await Account.find({ fintechId }).select(
      'accountNumber accountName balance -_id'
    );

    return res.status(200).json({ accounts });
  } catch (error) {
    console.error('getAllAccounts error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── GET /api/account/name-enquiry/:accountNumber ─────────────────────────────
const nameEnquiry = async (req, res) => {
  try {
    const { accountNumber } = req.params;

    // Name enquiry is global — any fintech can look up any account number
    const account = await Account.findOne({ accountNumber });
    if (!account) {
      return res.status(404).json({ message: 'Account not found' });
    }

    return res.status(200).json({
      accountNumber: account.accountNumber,
      accountName: account.accountName,
      bankName: account.bankName,
    });
  } catch (error) {
    console.error('nameEnquiry error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── GET /api/account/balance/:accountNumber ──────────────────────────────────
const getBalance = async (req, res) => {
  try {
    const { accountNumber } = req.params;
    const { fintechId } = req.fintech;

    // Balance can only be checked for accounts owned by the authenticated fintech
    const account = await Account.findOne({ accountNumber, fintechId });
    if (!account) {
      return res.status(404).json({ message: 'Account not found' });
    }

    return res.status(200).json({
      accountNumber: account.accountNumber,
      balance: account.balance,
    });
  } catch (error) {
    console.error('getBalance error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

module.exports = { createAccount, getAllAccounts, nameEnquiry, getBalance };
