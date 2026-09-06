const express = require('express');
const router = express.Router();
const authenticate = require('../middleware/authenticate');
const { transfer, getTransaction } = require('../controllers/transactionController');

router.post('/transfer', authenticate, transfer);
router.get('/transaction/:transactionId', authenticate, getTransaction);

module.exports = router;
