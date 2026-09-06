const express = require('express');
const router = express.Router();
const authenticate = require('../middleware/authenticate');
const {
  createAccount,
  getAllAccounts,
  nameEnquiry,
  getBalance,
} = require('../controllers/accountController');

// All account routes require a valid JWT
router.post('/account/create', authenticate, createAccount);
router.get('/accounts', authenticate, getAllAccounts);
router.get('/account/name-enquiry/:accountNumber', authenticate, nameEnquiry);
router.get('/account/balance/:accountNumber', authenticate, getBalance);

module.exports = router;
