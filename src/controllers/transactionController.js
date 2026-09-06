const Account = require('../models/Account');
const Transaction = require('../models/Transaction');

// Generate TSQ transaction ID — format matches live API: TX + timestamp
const generateTransactionId = () => `TX${Date.now()}`;

// ─── POST /api/transfer ───────────────────────────────────────────────────────
const transfer = async (req, res) => {
  try {
    const { from, to, amount } = req.body;
    const { fintechId } = req.fintech;

    // ── Field validation ──────────────────────────────────────────────────────
    if (!from || !to) {
      return res.status(400).json({
        message: 'Both sender (from) and receiver (to) account numbers are required',
      });
    }

    if (from === to) {
      return res.status(400).json({ message: 'You cannot transfer to the same account' });
    }

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount)) {
      return res.status(400).json({ message: 'Invalid amount' });
    }
    if (parsedAmount <= 0) {
      return res.status(400).json({ message: 'Amount must be greater than zero' });
    }

    // ── Sender validation ─────────────────────────────────────────────────────
    // The sender MUST belong to the authenticated fintech
    const senderAccount = await Account.findOne({ accountNumber: from, fintechId });
    if (!senderAccount) {
      return res.status(404).json({ message: 'Invalid account' });
    }

    // ── Funds check ───────────────────────────────────────────────────────────
    if (senderAccount.balance < parsedAmount) {
      return res.status(400).json({ message: 'Insufficient funds' });
    }

    // ── Recipient validation (global — can be any bank) ───────────────────────
    const recipientAccount = await Account.findOne({ accountNumber: to });
    if (!recipientAccount) {
      return res.status(404).json({ message: 'Invalid account' });
    }

    // ── Execute transfer atomically ───────────────────────────────────────────
    senderAccount.balance -= parsedAmount;
    recipientAccount.balance += parsedAmount;

    await senderAccount.save();
    await recipientAccount.save();

    // ── Record the transaction ────────────────────────────────────────────────
    const transactionId = generateTransactionId();
    await Transaction.create({
      transactionId,
      from,
      to,
      amount: parsedAmount,
      status: 'SUCCESS',
    });

    return res.status(200).json({
      message: 'Transfer successful',
      transactionId,
      amount: parsedAmount,
      from,
      to,
      status: 'SUCCESS',
    });
  } catch (error) {
    console.error('transfer error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

// ─── GET /api/transaction/:transactionId ──────────────────────────────────────
const getTransaction = async (req, res) => {
  try {
    const { transactionId } = req.params;

    const transaction = await Transaction.findOne({ transactionId });
    if (!transaction) {
      return res.status(404).json({ message: 'Not found' });
    }

    return res.status(200).json({
      transactionId: transaction.transactionId,
      status: transaction.status,
      amount: transaction.amount,
      from: transaction.from,
      to: transaction.to,
      timestamp: transaction.timestamp,
    });
  } catch (error) {
    console.error('getTransaction error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
};

module.exports = { transfer, getTransaction };
