const mongoose = require('mongoose');

const questionSchema = new mongoose.Schema({
    plagiarist: { type: String, required: true },
    plagiarist_user_id: { type: String, required: true },
    plagiarized_from: { type: String, required: true },
    plagiarized_from_user_id: { type: String, required: true },
    plagiarist_submission_id: { type: Number, required: true },
    plagiarized_submission_id: { type: Number, required: true },
    plagiarist_rank: { type: Number, required: true },
    plagiarized_rank: { type: Number, required: true },
    confidence_score: { type: Number, required: true },
    language: { type: String, required: true },
    question_id: { type: String, required: true }, // Matches schema name
}, { timestamps: true });

module.exports = mongoose.model('Question', questionSchema);