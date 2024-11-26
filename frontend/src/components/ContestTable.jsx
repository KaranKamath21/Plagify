import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import ReactPaginate from 'react-paginate';
import './ContestTable.css';
import '../styles/global.css';

const ContestTable = () => {
    const [contests, setContests] = useState([]);
    const [currentPage, setCurrentPage] = useState(0);
    const [sortConfig, setSortConfig] = useState({ key: null, direction: null });
    const [searchTerm, setSearchTerm] = useState('');
    const contestsPerPage = 10;

    useEffect(() => {
        const fetchContests = async () => {
            try {
                const response = await axios.get('http://localhost:5000/api/contests');
                setContests(response.data);
            } catch (error) {
                console.error('Error fetching contests:', error);
            }
        };
        fetchContests();
    }, []);

    const sortedContests = () => {
        if (!sortConfig.key) return contests;
        
        return [...contests].sort((a, b) => {
            if (a[sortConfig.key] < b[sortConfig.key]) {
                return sortConfig.direction === 'ascending' ? -1 : 1;
            }
            if (a[sortConfig.key] > b[sortConfig.key]) {
                return sortConfig.direction === 'ascending' ? 1 : -1;
            }
            return 0;
        });
    };

    const filteredContests = sortedContests().filter(contest =>
        contest.contest_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const offset = currentPage * contestsPerPage;
    const currentContests = filteredContests.slice(offset, offset + contestsPerPage);

    const handlePageClick = ({ selected }) => {
        setCurrentPage(selected);
    };

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    return (
        <div>
            <header className="header">
                <h1>Plagify</h1>
                <h2>Leetcode Plagiarism Detector</h2>
            </header>

            <div className="contest-table-container">
                
                <div className="home-button-container">
                    <button className="home-button">
                        <Link to="/" className="home-link">Home</Link>
                    </button>
                </div>

                <div className="search-container">
                    <input
                        type="text"
                        placeholder="Search contest..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <table>
                    <thead>
                        <tr>
                            <th onClick={() => requestSort('contest_name')}>Contest Name</th>
                            <th onClick={() => requestSort('contest_date')}>Contest Date</th>
                            <th>Contest Link</th>
                            <th>Question 3</th>
                            <th>Question 4</th>
                        </tr>
                    </thead>
                    <tbody>
                        {currentContests.map((contest) => (
                            <tr key={contest._id}>
                                <td>{contest.contest_name}</td>
                                <td>{contest.contest_date}</td>
                                <td>
                                    <a href={contest.contest_link} target="_blank" rel="noopener noreferrer">
                                        View Contest
                                    </a>
                                </td>
                                <td>
                                    <Link to={`/questions/${contest.question_3}`}>Question 3</Link>
                                </td>
                                <td>
                                    <Link to={`/questions/${contest.question_4}`}>Question 4</Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="records-info">
                Displaying {offset + 1} to {Math.min(offset + contestsPerPage, filteredContests.length)} of {filteredContests.length} Records
            </div>

            <ReactPaginate
                previousLabel={"← Previous"}
                nextLabel={"Next →"}
                pageCount={Math.ceil(filteredContests.length / contestsPerPage)}
                onPageChange={handlePageClick}
                containerClassName={"pagination"}
                previousLinkClassName={"pagination__link"}
                nextLinkClassName={"pagination__link"}
                disabledClassName={"pagination__link--disabled"}
                activeClassName={"pagination__link--active"}
            />

            <footer className="footer">
                <div className="social-links">
                    <a href="https://github.com/yourusername" target="_blank" rel="noopener noreferrer">GitHub</a>
                    <a href="https://linkedin.com/in/yourusername" target="_blank" rel="noopener noreferrer">LinkedIn</a>
                </div>
                <p>
                    If You Want Plagiarism Script or any Query Regarding Report: Drop a Message at{' '}
                    <a href="https://linkedin.com/in/yourusername" target="_blank" rel="noopener noreferrer">
                        Karan Kamath
                    </a>
                </p>
            </footer>
        </div>
    );
};

export default ContestTable;