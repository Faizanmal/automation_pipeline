"""Simple web dashboard for viewing pipeline results."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

try:
    from flask import Flask, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class PipelineDashboard:
    """Dashboard for pipeline results visualization."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize dashboard with output directory."""
        self.output_dir = Path(output_dir)
    
    def get_coverage_summary(self) -> Dict[str, Any]:
        """Get coverage summary from coverage.json."""
        coverage_path = self.output_dir / "coverage.json"
        if not coverage_path.exists():
            return {}
        
        with open(coverage_path) as f:
            return json.load(f)
    
    def get_company_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for each company."""
        stats = []
        
        for company_dir in self.output_dir.iterdir():
            if not company_dir.is_dir() or company_dir.name.startswith("_"):
                continue
            
            company_slug = company_dir.name
            meta_dir = company_dir / "_meta"
            
            if not meta_dir.exists():
                continue
            
            # Load manifest
            manifest_path = meta_dir / "manifest.json"
            discovery_path = meta_dir / "discovery.json"
            
            manifest_data = []
            discovery_data = {}
            
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest_data = json.load(f)
            
            if discovery_path.exists():
                with open(discovery_path) as f:
                    discovery_data = json.load(f)
            
            # Compute stats
            total_files = len(manifest_data)
            pdfs = sum(1 for r in manifest_data if r.get("file_type") == "pdf")
            htmls = sum(1 for r in manifest_data if r.get("file_type") == "html")
            total_size = sum(r.get("size_bytes", 0) for r in manifest_data)
            
            stats.append({
                "company": company_slug,
                "total_files": total_files,
                "pdfs": pdfs,
                "htmls": htmls,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "urls_discovered": len(discovery_data.get("urls", [])),
                "last_updated": discovery_data.get("timestamp", "N/A"),
            })
        
        return sorted(stats, key=lambda x: x["total_files"], reverse=True)
    
    def to_html(self) -> str:
        """Generate HTML dashboard."""
        if not FLASK_AVAILABLE:
            return "<h1>Flask not installed. Install with: pip install flask</h1>"
        
        self.get_coverage_summary()
        companies = self.get_company_stats()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pipeline Dashboard</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                h1 {
                    color: #333;
                    border-bottom: 3px solid #0078d4;
                    padding-bottom: 10px;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .stat-card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .stat-value {
                    font-size: 32px;
                    font-weight: bold;
                    color: #0078d4;
                }
                .stat-label {
                    color: #666;
                    margin-top: 5px;
                    font-size: 14px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                th {
                    background: #0078d4;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }
                td {
                    padding: 12px;
                    border-bottom: 1px solid #eee;
                }
                tr:hover {
                    background: #f9f9f9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Pipeline Dashboard</h1>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{{ companies_count }}</div>
                        <div class="stat-label">Companies</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ total_files }}</div>
                        <div class="stat-label">Files Downloaded</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ total_size_gb|round(2) }} GB</div>
                        <div class="stat-label">Total Size</div>
                    </div>
                </div>
                
                <h2>Company Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Files</th>
                            <th>PDFs</th>
                            <th>HTML</th>
                            <th>Size (MB)</th>
                            <th>URLs Discovered</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for company in companies %}
                        <tr>
                            <td><strong>{{ company.company }}</strong></td>
                            <td>{{ company.total_files }}</td>
                            <td>{{ company.pdfs }}</td>
                            <td>{{ company.htmls }}</td>
                            <td>{{ company.total_size_mb }}</td>
                            <td>{{ company.urls_discovered }}</td>
                            <td>{{ company.last_updated }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <p style="margin-top: 30px; color: #999; font-size: 12px;">
                    Last generated: {{ timestamp }}
                </p>
            </div>
        </body>
        </html>
        """
        
        total_files = sum(c["total_files"] for c in companies)
        total_size_gb = sum(c["total_size_mb"] for c in companies) / 1024
        
        from jinja2 import Template
        template = Template(html_template)
        
        return template.render(
            companies_count=len(companies),
            total_files=total_files,
            total_size_gb=total_size_gb,
            companies=companies,
            timestamp=datetime.now().isoformat(timespec='minutes'),
        )


def create_flask_app(output_dir: str = "output"):
    """Create Flask app for dashboard."""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for the dashboard. Install with: pip install flask")
    
    app = Flask(__name__)
    dashboard = PipelineDashboard(output_dir)
    
    @app.route("/")
    def index():
        """Render dashboard."""
        return dashboard.to_html()
    
    @app.route("/api/stats")
    def stats():
        """API endpoint for stats."""
        return jsonify({
            "coverage": dashboard.get_coverage_summary(),
            "companies": dashboard.get_company_stats(),
        })
    
    return app


if __name__ == "__main__":
    app = create_flask_app()
    print("Dashboard available at http://localhost:5000")
    app.run(debug=True, port=5000)
