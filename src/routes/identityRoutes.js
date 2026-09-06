const express = require('express');
const router = express.Router();
const { insertBvn, insertNin, validateBvn, validateNin } = require('../controllers/identityController');

// Based on Grok's live API investigation: these routes are PUBLIC (no JWT required)
// This contradicts sections 5.9-5.12 of the docs but matches the Endpoint Summary
// table (Section 7) and the actual live API behaviour.
router.post('/insertBvn', insertBvn);
router.post('/insertNin', insertNin);
router.post('/validateBvn', validateBvn);
router.post('/validateNin', validateNin);

module.exports = router;
