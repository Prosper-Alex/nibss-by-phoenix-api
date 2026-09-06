const mongoose = require('mongoose');

const ninSchema = new mongoose.Schema(
  {
    nin: {
      type: String,
      required: true,
      unique: true,
      trim: true,
    },
    firstName: { type: String, required: true, trim: true },
    lastName:  { type: String, required: true, trim: true },
    dob:       { type: Date,   required: true },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Nin', ninSchema);
