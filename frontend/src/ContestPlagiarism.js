import React, { useState, useEffect } from "react";
import axios from "axios";

function ContestPlagiarism() {
    const [contests, setContests] = useState([]);
    const [plagiarismData, setPlagiarismData] = useState([]);

    // Fetch contests when the component mounts
    useEffect(() => {
        async function fetchContests() {
            try {
                const response = await axios.get("http://localhost:5000/api/contests");
                setContests(response.data); // Set the contests state with data from the API
            } catch (error) {
                console.error("Error fetching contests:", error);
            }
        }

        fetchContests();
    }, []);

    // Fetch plagiarism data for each contest once contests are fetched
    useEffect(() => {
        if (contests.length > 0) {
            // Loop through each contest to fetch plagiarism data
            contests.forEach(async (contest) => {
                try {
                    const response = await axios.get(
                        `http://localhost:5000/api/plagiarism/${contest.contestSlug}`
                    );
                    setPlagiarismData((prevData) => [
                        ...prevData,
                        { contestSlug: contest.contestSlug, plagiarismData: response.data },
                    ]);
                } catch (error) {
                    console.error(`Error fetching plagiarism data for ${contest.contestSlug}:`, error);
                }
            });
        }
    }, [contests]);

    return (
        <div>
            <h1>Contests and Plagiarism Data</h1>

            {/* Display all contests */}
            {contests.length > 0 ? (
                contests.map((contest) => (
                    <div key={contest._id} className="contest-card">
                        <h2>{contest.contestName}</h2>
                        <p>Slug: {contest.contestSlug}</p>

                        {/* Display plagiarism data for this contest */}
                        {plagiarismData
                            .filter((data) => data.contestSlug === contest.contestSlug)
                            .map((data, index) => (
                                <div key={index}>
                                    <h3>Plagiarism Data</h3>
                                    {data.plagiarismData.length > 0 ? (
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>Plagiarist</th>
                                                    <th>Plagiarized From</th>
                                                    <th>Confidence Score</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {data.plagiarismData.map((item, idx) => (
                                                    <tr key={idx}>
                                                        <td>{item.plagiarist}</td>
                                                        <td>{item.plagiarizedFrom}</td>
                                                        <td>{item.confidenceScore}%</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    ) : (
                                        <p>No plagiarism data available.</p>
                                    )}
                                </div>
                            ))}
                    </div>
                ))
            ) : (
                <p>Loading contests...</p>
            )}
        </div>
    );
}

export default ContestPlagiarism;