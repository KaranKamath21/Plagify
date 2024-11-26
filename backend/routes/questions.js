const express = require('express');
const mongoose = require('mongoose');
const router = express.Router();

// GET question data by question ID
router.get('/:questionId', async (req, res) => {
    try {
        const questionModel = mongoose.model(req.params.questionId, require('../models/Question').schema);
        const questionData = await questionModel.find();
        res.status(200).json(questionData);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch question data' });
    }
});

module.exports = router;