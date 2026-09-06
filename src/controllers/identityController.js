const Bvn = require('../models/Bvn');
const Nin = require('../models/Nin');

// ─── POST /api/insertBvn ──────────────────────────────────────────────────────
const insertBvn = async (req, res) => {
  try {
    const { bvn, firstName, lastName, dob, phone } = req.body;

    // Validate BVN format: exactly 11 digits
    if (!bvn || !/^\d{11}$/.test(bvn)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid BVN format. BVN must be exactly 11 digits.',
      });
    }

    if (!firstName || !lastName || !dob || !phone) {
      return res.status(400).json({
        success: false,
        message: 'Invalid BVN format. BVN must be exactly 11 digits.',
      });
    }

    // Check for duplicate
    const existing = await Bvn.findOne({ bvn });
    if (existing) {
      return res.status(409).json({
        success: false,
        message: 'BVN already exists in the system.',
      });
    }

    const record = await Bvn.create({ bvn, firstName, lastName, dob, phone });

    return res.status(201).json({
      success: true,
      message: 'BVN record created successfully.',
      data: {
        bvn: record.bvn,
        firstName: record.firstName,
        lastName: record.lastName,
        dob: record.dob,
        phone: record.phone,
        createdAt: record.createdAt,
      },
    });
  } catch (error) {
    console.error('insertBvn error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── POST /api/insertNin ──────────────────────────────────────────────────────
const insertNin = async (req, res) => {
  try {
    const { nin, firstName, lastName, dob } = req.body;

    if (!nin || !firstName || !lastName || !dob) {
      return res.status(400).json({ error: 'All fields are required' });
    }

    // Validate NIN format: exactly 11 digits
    if (!/^\d{11}$/.test(nin)) {
      return res.status(400).json({ error: 'NIN must have ONLY 11 digits' });
    }

    const existing = await Nin.findOne({ nin });
    if (existing) {
      return res.status(400).json({
        error: 'NIN already exists for another user, Please provide a different one',
      });
    }

    const record = await Nin.create({ nin, firstName, lastName, dob });

    return res.status(201).json({
      message: 'NIN record created successfully',
      nin: record.nin,
    });
  } catch (error) {
    console.error('insertNin error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── POST /api/validateBvn ────────────────────────────────────────────────────
const validateBvn = async (req, res) => {
  try {
    const { bvn } = req.body;

    if (!bvn || !/^\d{11}$/.test(bvn)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid BVN format. BVN must be exactly 11 digits.',
      });
    }

    const record = await Bvn.findOne({ bvn });
    if (!record) {
      return res.status(404).json({
        success: false,
        message: 'BVN not found in the system.',
      });
    }

    return res.status(200).json({
      success: true,
      message: 'BVN validation successful.',
      data: {
        bvn: record.bvn,
        firstName: record.firstName,
        lastName: record.lastName,
        dob: record.dob,
        phone: record.phone,
      },
    });
  } catch (error) {
    console.error('validateBvn error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── POST /api/validateNin ────────────────────────────────────────────────────
const validateNin = async (req, res) => {
  try {
    const { nin } = req.body;

    if (!nin) {
      return res.status(400).json({ error: 'NIN must be provided' });
    }

    if (!/^\d{11}$/.test(nin)) {
      return res.status(400).json({ error: 'NIN must have ONLY 11 digits' });
    }

    const record = await Nin.findOne({ nin });
    if (!record) {
      return res.status(400).json({
        error: 'NIN is not registered. Kindly register your NIN',
      });
    }

    return res.status(200).json({
      valid: true,
      nin: record.nin,
      firstName: record.firstName,
      lastName: record.lastName,
      dob: record.dob,
    });
  } catch (error) {
    console.error('validateNin error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

module.exports = { insertBvn, insertNin, validateBvn, validateNin };
