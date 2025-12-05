import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
    const [stats, setStats] = useState(null);
    const [jobs, setJobs] = useState([]);
    const [deadLetters, setDeadLetters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [statsRes, jobsRes, deadLettersRes] = await Promise.all([
                axios.get(`${API_URL}/api/v1/stats`),
                axios.get(`${API_URL}/api/v1/jobs?limit=20`),
                axios.get(`${API_URL}/api/v1/dead-letters?limit=10`),
            ]);

            setStats(statsRes.data);
            setJobs(jobsRes.data);
            setDeadLetters(deadLettersRes.data.items || []);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        const colors = {
            pending: '#FFA500',
            running: '#2196F3',
            completed: '#4CAF50',
            failed: '#F44336',
            cancelled: '#9E9E9E',
            retrying: '#FF9800',
        };
        return colors[status] || '#000';
    };

    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    return (
        <div className="App">
            <header className="header">
                <h1>🚀 Distributed Job Queue Dashboard</h1>
                <p className="subtitle">Real-time monitoring and management</p>
            </header>

            <div className="tabs">
                <button
                    className={activeTab === 'overview' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('overview')}
                >
                    Overview
                </button>
                <button
                    className={activeTab === 'jobs' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('jobs')}
                >
                    Jobs
                </button>
                <button
                    className={activeTab === 'deadletters' ? 'tab active' : 'tab'}
                    onClick={() => setActiveTab('deadletters')}
                >
                    Dead Letters
                </button>
            </div>

            {activeTab === 'overview' && stats && (
                <div className="overview">
                    <div className="stats-grid">
                        <div className="stat-card">
                            <h3>Pending Jobs</h3>
                            <div className="stat-value">{stats.pending_jobs}</div>
                            <div className="stat-breakdown">
                                <span>High: {stats.queue_breakdown.high}</span>
                                <span>Med: {stats.queue_breakdown.medium}</span>
                                <span>Low: {stats.queue_breakdown.low}</span>
                            </div>
                        </div>

                        <div className="stat-card running">
                            <h3>Running Jobs</h3>
                            <div className="stat-value">{stats.running_jobs}</div>
                        </div>

                        <div className="stat-card completed">
                            <h3>Completed Jobs</h3>
                            <div className="stat-value">{stats.completed_jobs}</div>
                        </div>

                        <div className="stat-card failed">
                            <h3>Failed Jobs</h3>
                            <div className="stat-value">{stats.failed_jobs}</div>
                        </div>

                        <div className="stat-card workers">
                            <h3>Active Workers</h3>
                            <div className="stat-value">{stats.active_workers}</div>
                        </div>

                        <div className="stat-card dead-letters">
                            <h3>Dead Letters</h3>
                            <div className="stat-value">{stats.dead_letter_count}</div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'jobs' && (
                <div className="jobs-list">
                    <h2>Recent Jobs</h2>
                    <table className="jobs-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Type</th>
                                <th>Priority</th>
                                <th>Status</th>
                                <th>Retries</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map(job => (
                                <tr key={job.job_id}>
                                    <td className="job-id">{job.job_id.substring(0, 8)}...</td>
                                    <td>{job.job_type}</td>
                                    <td>
                                        <span className={`priority-badge ${job.priority}`}>
                                            {job.priority}
                                        </span>
                                    </td>
                                    <td>
                                        <span
                                            className="status-badge"
                                            style={{ backgroundColor: getStatusColor(job.status) }}
                                        >
                                            {job.status}
                                        </span>
                                    </td>
                                    <td>{job.retry_count} / {job.max_retries}</td>
                                    <td>{new Date(job.created_at).toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {activeTab === 'deadletters' && (
                <div className="dead-letters-list">
                    <h2>Dead Letter Queue</h2>
                    {deadLetters.length === 0 ? (
                        <p className="empty-state">No dead letters found ✨</p>
                    ) : (
                        <table className="jobs-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Job Type</th>
                                    <th>Attempts</th>
                                    <th>Failure Reason</th>
                                    <th>Failed At</th>
                                </tr>
                            </thead>
                            <tbody>
                                {deadLetters.map(dl => (
                                    <tr key={dl.id}>
                                        <td className="job-id">{dl.job_id.substring(0, 8)}...</td>
                                        <td>{dl.job_type}</td>
                                        <td>{dl.total_attempts}</td>
                                        <td className="error-message">{dl.failure_reason}</td>
                                        <td>{new Date(dl.final_failure_at).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}

            <footer className="footer">
                <p>Last updated: {new Date().toLocaleTimeString()}</p>
            </footer>
        </div>
    );
}

export default App;
