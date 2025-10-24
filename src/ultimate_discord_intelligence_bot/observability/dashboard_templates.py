"""Dashboard HTML Templates for Enhanced Metrics API.

This module provides HTML templates for the web-based metrics dashboard.
"""

from __future__ import annotations


def get_base_template() -> str:
    """Get the main dashboard template."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Discord Intelligence Bot - Metrics Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .header p {
            color: #718096;
            text-align: center;
            font-size: 1.1rem;
        }
        
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            justify-content: center;
        }
        
        .nav-tab {
            background: rgba(255, 255, 255, 0.9);
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            color: #4a5568;
        }
        
        .nav-tab:hover, .nav-tab.active {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #4a5568;
            font-weight: 500;
        }
        
        .metric-value {
            color: #2d3748;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background: #48bb78; }
        .status-warning { background: #ed8936; }
        .status-error { background: #f56565; }
        .status-inactive { background: #a0aec0; }
        
        .tools-table {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
        }
        
        .tools-table h3 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        th {
            background: #f7fafc;
            font-weight: 600;
            color: #4a5568;
        }
        
        .tool-name {
            font-weight: 600;
            color: #2d3748;
        }
        
        .success-rate {
            font-weight: 600;
        }
        
        .success-rate.high { color: #48bb78; }
        .success-rate.medium { color: #ed8936; }
        .success-rate.low { color: #f56565; }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #718096;
        }
        
        .error {
            background: #fed7d7;
            color: #c53030;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 20px 0;
        }
        
        .refresh-btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .nav-tabs {
                flex-wrap: wrap;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Ultimate Discord Intelligence Bot</h1>
            <p>Real-time Metrics Dashboard & System Health Monitor</p>
        </div>
        
        <div class="nav-tabs">
            <a href="/" class="nav-tab active">📊 Dashboard</a>
            <a href="/simple" class="nav-tab">🔍 Simple View</a>
            <a href="/api/metrics/health" class="nav-tab">❤️ Health</a>
            <a href="/api/metrics/export" class="nav-tab">📥 Export</a>
        </div>
        
        <div id="dashboard-content">
            <div class="loading">
                <h3>🔄 Loading metrics...</h3>
                <p>Fetching real-time data from the system</p>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh Data</button>
        </div>
    </div>
    
    <script>
        async function loadDashboard() {
            const content = document.getElementById('dashboard-content');
            content.innerHTML = '<div class="loading"><h3>🔄 Loading metrics...</h3><p>Fetching real-time data from the system</p></div>';
            
            try {
                // Load system metrics
                const systemResponse = await fetch('/api/metrics/system');
                const systemData = await systemResponse.json();
                
                // Load tool metrics
                const toolsResponse = await fetch('/api/metrics/tools');
                const toolsData = await toolsResponse.json();
                
                // Load analytics
                const analyticsResponse = await fetch('/api/metrics/analytics');
                const analyticsData = await analyticsResponse.json();
                
                // Render dashboard
                renderDashboard(systemData, toolsData, analyticsData);
                
            } catch (error) {
                content.innerHTML = `
                    <div class="error">
                        <h3>❌ Error Loading Dashboard</h3>
                        <p>Failed to fetch metrics data: ${error.message}</p>
                        <p>Please check that the metrics API is running and accessible.</p>
                    </div>
                `;
            }
        }
        
        function renderDashboard(systemData, toolsData, analyticsData) {
            const content = document.getElementById('dashboard-content');
            
            if (systemData.status !== 'success' || toolsData.status !== 'success') {
                content.innerHTML = `
                    <div class="error">
                        <h3>❌ API Error</h3>
                        <p>Failed to load metrics data from the API.</p>
                    </div>
                `;
                return;
            }
            
            const system = systemData.data;
            const tools = toolsData.data.tools;
            const analytics = analyticsData.data;
            
            content.innerHTML = `
                <div class="dashboard-grid">
                    <div class="card">
                        <h3>📈 System Overview</h3>
                        <div class="metric">
                            <span class="metric-label">Total Tool Calls</span>
                            <span class="metric-value">${system.total_tool_calls || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Active Tools</span>
                            <span class="metric-value">${system.active_tools || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">System Uptime</span>
                            <span class="metric-value">${system.system_uptime || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Health Score</span>
                            <span class="metric-value">${Math.round(system.health_score || 0)}%</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>⚡ Performance</h3>
                        <div class="metric">
                            <span class="metric-label">Total Execution Time</span>
                            <span class="metric-value">${(system.total_execution_time || 0).toFixed(2)}s</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Memory Usage</span>
                            <span class="metric-value">${(system.memory_usage_mb || 0).toFixed(1)} MB</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">CPU Usage</span>
                            <span class="metric-value">${(system.cpu_usage_percent || 0).toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Last Updated</span>
                            <span class="metric-value">${system.last_updated ? new Date(system.last_updated).toLocaleTimeString() : 'N/A'}</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🔍 Analytics</h3>
                        <div class="metric">
                            <span class="metric-label">Average Success Rate</span>
                            <span class="metric-value">${((analytics.performance_insights?.average_success_rate || 0) * 100).toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Average Execution Time</span>
                            <span class="metric-value">${(analytics.performance_insights?.average_execution_time || 0).toFixed(2)}s</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Critical Issues</span>
                            <span class="metric-value">${analytics.bottleneck_analysis?.critical_issues || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Issues</span>
                            <span class="metric-value">${analytics.bottleneck_analysis?.total_issues || 0}</span>
                        </div>
                    </div>
                </div>
                
                <div class="tools-table">
                    <h3>🛠️ Tool Performance</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Tool Name</th>
                                <th>Status</th>
                                <th>Success Rate</th>
                                <th>Avg Time</th>
                                <th>Total Calls</th>
                                <th>Health</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(tools).map(([name, tool]) => `
                                <tr>
                                    <td class="tool-name">${name}</td>
                                    <td>
                                        <span class="status-indicator status-${tool.health_status || 'inactive'}"></span>
                                        ${tool.health_status || 'inactive'}
                                    </td>
                                    <td class="success-rate ${getSuccessRateClass(tool.success_rate || 0)}">
                                        ${((tool.success_rate || 0) * 100).toFixed(1)}%
                                    </td>
                                    <td>${(tool.average_execution_time || 0).toFixed(2)}s</td>
                                    <td>${tool.total_calls || 0}</td>
                                    <td>${tool.health_status || 'unknown'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        function getSuccessRateClass(rate) {
            if (rate >= 0.9) return 'high';
            if (rate >= 0.7) return 'medium';
            return 'low';
        }
        
        // Auto-refresh every 30 seconds
        setInterval(loadDashboard, 30000);
        
        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', loadDashboard);
    </script>
</body>
</html>
"""


def get_simple_dashboard() -> str:
    """Get the simple dashboard template."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Metrics Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f7fafc;
            margin: 0;
            padding: 20px;
            color: #2d3748;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        
        .header h1 {
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .nav {
            margin-bottom: 20px;
        }
        
        .nav a {
            display: inline-block;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-right: 10px;
        }
        
        .nav a:hover {
            background: #5a67d8;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .metric-card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #718096;
        }
        
        .metric-value {
            font-weight: 600;
            color: #2d3748;
        }
        
        .tools-list {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .tools-list h3 {
            color: #2d3748;
            margin-bottom: 15px;
        }
        
        .tool-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .tool-item:last-child {
            border-bottom: none;
        }
        
        .tool-name {
            font-weight: 600;
            color: #2d3748;
        }
        
        .tool-stats {
            color: #718096;
            font-size: 0.9rem;
        }
        
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-healthy { background: #c6f6d5; color: #22543d; }
        .status-warning { background: #fef5e7; color: #744210; }
        .status-error { background: #fed7d7; color: #742a2a; }
        .status-inactive { background: #e2e8f0; color: #4a5568; }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #718096;
        }
        
        .error {
            background: #fed7d7;
            color: #742a2a;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 20px 0;
        }
        
        .refresh-btn:hover {
            background: #5a67d8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Simple Metrics Dashboard</h1>
            <p>Quick overview of system performance and tool health</p>
        </div>
        
        <div class="nav">
            <a href="/">📊 Full Dashboard</a>
            <a href="/simple">🔍 Simple View</a>
            <a href="/api/metrics/health">❤️ Health</a>
        </div>
        
        <div id="content">
            <div class="loading">
                <h3>🔄 Loading metrics...</h3>
                <p>Fetching system data...</p>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="loadSimpleDashboard()">🔄 Refresh</button>
        </div>
    </div>
    
    <script>
        async function loadSimpleDashboard() {
            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading"><h3>🔄 Loading metrics...</h3><p>Fetching system data...</p></div>';
            
            try {
                const [systemResponse, toolsResponse] = await Promise.all([
                    fetch('/api/metrics/system'),
                    fetch('/api/metrics/tools')
                ]);
                
                const systemData = await systemResponse.json();
                const toolsData = await toolsResponse.json();
                
                renderSimpleDashboard(systemData, toolsData);
                
            } catch (error) {
                content.innerHTML = `
                    <div class="error">
                        <h3>❌ Error Loading Dashboard</h3>
                        <p>Failed to fetch metrics: ${error.message}</p>
                    </div>
                `;
            }
        }
        
        function renderSimpleDashboard(systemData, toolsData) {
            const content = document.getElementById('content');
            
            if (systemData.status !== 'success' || toolsData.status !== 'success') {
                content.innerHTML = `
                    <div class="error">
                        <h3>❌ API Error</h3>
                        <p>Failed to load metrics data.</p>
                    </div>
                `;
                return;
            }
            
            const system = systemData.data;
            const tools = toolsData.data.tools;
            
            content.innerHTML = `
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>📈 System Stats</h3>
                        <div class="metric">
                            <span class="metric-label">Total Calls</span>
                            <span class="metric-value">${system.total_tool_calls || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Active Tools</span>
                            <span class="metric-value">${system.active_tools || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Health Score</span>
                            <span class="metric-value">${Math.round(system.health_score || 0)}%</span>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <h3>⚡ Performance</h3>
                        <div class="metric">
                            <span class="metric-label">Total Time</span>
                            <span class="metric-value">${(system.total_execution_time || 0).toFixed(2)}s</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Memory</span>
                            <span class="metric-value">${(system.memory_usage_mb || 0).toFixed(1)} MB</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">CPU</span>
                            <span class="metric-value">${(system.cpu_usage_percent || 0).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="tools-list">
                    <h3>🛠️ Tool Status</h3>
                    ${Object.entries(tools).map(([name, tool]) => `
                        <div class="tool-item">
                            <div>
                                <div class="tool-name">${name}</div>
                                <div class="tool-stats">
                                    ${tool.total_calls || 0} calls • 
                                    ${((tool.success_rate || 0) * 100).toFixed(1)}% success • 
                                    ${(tool.average_execution_time || 0).toFixed(2)}s avg
                                </div>
                            </div>
                            <span class="status status-${tool.health_status || 'inactive'}">
                                ${tool.health_status || 'inactive'}
                            </span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Auto-refresh every 30 seconds
        setInterval(loadSimpleDashboard, 30000);
        
        // Load on page load
        document.addEventListener('DOMContentLoaded', loadSimpleDashboard);
    </script>
</body>
</html>
"""


def get_health_template() -> str:
    """Get the health check template."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Health Check</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f7fafc;
            margin: 0;
            padding: 20px;
            color: #2d3748;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .health-card {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .health-status {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        
        .health-status.healthy { color: #48bb78; }
        .health-status.warning { color: #ed8936; }
        .health-status.error { color: #f56565; }
        
        .health-details {
            margin-top: 20px;
            text-align: left;
        }
        
        .detail {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .detail:last-child {
            border-bottom: none;
        }
        
        .detail-label {
            color: #718096;
        }
        
        .detail-value {
            font-weight: 600;
            color: #2d3748;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="health-card">
            <div id="health-content">
                <div class="health-status">🔄</div>
                <h2>Checking System Health...</h2>
                <p>Please wait while we verify system status.</p>
            </div>
        </div>
    </div>
    
    <script>
        async function checkHealth() {
            try {
                const response = await fetch('/api/metrics/health');
                const data = await response.json();
                
                const content = document.getElementById('health-content');
                
                if (data.status === 'healthy') {
                    content.innerHTML = `
                        <div class="health-status healthy">✅</div>
                        <h2>System Healthy</h2>
                        <p>All systems are operating normally.</p>
                        <div class="health-details">
                            <div class="detail">
                                <span class="detail-label">Status</span>
                                <span class="detail-value">${data.status}</span>
                            </div>
                            <div class="detail">
                                <span class="detail-label">Service</span>
                                <span class="detail-value">${data.service}</span>
                            </div>
                            <div class="detail">
                                <span class="detail-label">Version</span>
                                <span class="detail-value">${data.version}</span>
                            </div>
                            <div class="detail">
                                <span class="detail-label">Last Check</span>
                                <span class="detail-value">${new Date(data.timestamp).toLocaleString()}</span>
                            </div>
                        </div>
                    `;
                } else {
                    content.innerHTML = `
                        <div class="health-status error">❌</div>
                        <h2>System Issues Detected</h2>
                        <p>Some components may not be functioning properly.</p>
                    `;
                }
                
            } catch (error) {
                const content = document.getElementById('health-content');
                content.innerHTML = `
                    <div class="health-status error">❌</div>
                    <h2>Health Check Failed</h2>
                    <p>Unable to connect to the metrics API.</p>
                    <p>Error: ${error.message}</p>
                `;
            }
        }
        
        // Check health on page load
        document.addEventListener('DOMContentLoaded', checkHealth);
        
        // Auto-refresh every 10 seconds
        setInterval(checkHealth, 10000);
    </script>
</body>
</html>
"""
