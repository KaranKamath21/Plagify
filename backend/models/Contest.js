const mongoose = require('mongoose');

const contestSchema = new mongoose.Schema({
    contest_link: { type: String, required: true },
    contest_name: { type: String, required: true },
    contest_date: { type: String, required: true },
    question_3: { type: String, required: true },
    question_4: { type: String, required: true },
    // Add more question fields as needed
}, { timestamps: true });

module.exports = mongoose.model('Contest', contestSchema);