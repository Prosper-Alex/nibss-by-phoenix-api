const mongoose = require('mongoose');

const accountSchema = new mongoose.Schema(
  {
    accountNumber: {
      type: String,
      required: true,
      unique: true,
      trim: true,
    },
    accountName: {
      type: String,
      required: true,
    },
    // Links the account to its owning fintech (security + ownership queries)
    fintechId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Fintech',
      required: true,
    },
    // Stored for fast interbank routing without extra DB lookup
    bankCode: {
      type: String,
      required: true,
    },
    bankName: {
      type: String,
      required: true,
    },
    balance: {
      type: Number,
      default: 15000, // Starting balance as seen in documentation
    },
    kycType: {
      type: String,
      enum: ['bvn', 'nin'],
      required: true,
      lowercase: true,
    },
    kycID: {
      type: String,
      required: true,
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Account', accountSchema);
