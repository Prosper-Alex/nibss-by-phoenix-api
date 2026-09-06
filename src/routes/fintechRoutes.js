const express = require('express');
const router = express.Router();
const { onboardFintech, loginFintech } = require('../controllers/fintechController');

router.post('/fintech/onboard', onboardFintech);
router.post('/auth/token', loginFintech);

module.exports = router;
