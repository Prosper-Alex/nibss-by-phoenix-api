const mongoose = require('mongoose');

const bvnSchema = new mongoose.Schema(
  {
    bvn: {
      type: String,
      required: true,
      unique: true,
      trim: true,
    },
    firstName: { type: String, required: true, trim: true },
    lastName:  { type: String, required: true, trim: true },
    dob:       { type: Date,   required: true },
    phone:     { type: String, required: true, trim: true },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Bvn', bvnSchema);
