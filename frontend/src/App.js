import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ContestTable from './components/ContestTable';
import QuestionPage from './components/QuestionPage';
import './styles/global.css';

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<ContestTable />} />
                <Route path="/questions/:questionId" element={<QuestionPage />} />
            </Routes>
        </Router>
    );
};

export default App;