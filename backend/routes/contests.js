const express = require('express');
const Contest = require('../models/Contest');
const router = express.Router();

// GET all contests
router.get('/', async (req, res) => {
    try {
        const contests = await Contest.find();
        res.status(200).json(contests);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch contests' });
    }
});

// GET a specific contest by ID
router.get('/:id', async (req, res) => {
    try {
        const contest = await Contest.findById(req.params.id);
        if (!contest) return res.status(404).json({ error: 'Contest not found' });
        res.status(200).json(contest);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch contest' });
    }
});

module.exports = router;