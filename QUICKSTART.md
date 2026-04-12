# Quick Start Guide

## 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## 2. Validate Setup

```bash
python validate.py
```

You should see all checks pass.

## 3. Configure API Keys

### Get API Keys

1. **Brave Search API**: https://api.search.brave.com/
   - Click "Sign Up" → Create account
   - Copy API key from dashboard

2. **Firecrawl API**: https://www.firecrawl.dev/
   - Click "Get Started" → Create account  
   - Copy API key from dashboard

### Set Environment Variables

**Windows (Command Prompt):**
```bash
set BRAVE_API_KEY=your_brave_key_here
set FIRECRAWL_API_KEY=your_firecrawl_key_here
```

**Windows (PowerShell):**
```powershell
$env:BRAVE_API_KEY="your_brave_key_here"
$env:FIRECRAWL_API_KEY="your_firecrawl_key_here"
```

**macOS/Linux:**
```bash
export BRAVE_API_KEY=your_brave_key_here
export FIRECRAWL_API_KEY=your_firecrawl_key_here
```

## 4. Test With Example Config

```bash
# Generate example configuration
python main.py example-config

# View the example
cat config.example.yaml

# Run pipeline with debug logging
python main.py run --config config.example.yaml --log-level DEBUG
```

## 5. Run Full Pipeline

```bash
# Process all companies
python main.py run

# Process specific companies
python main.py run --company ubs --company gs

# Run with custom config
python main.py run --config my_config.yaml
```

## 6. Generate Coverage Report

```bash
python main.py report
```

View the report in `output/coverage.json`.

---

## Directory Structure After Running

```
output/
├── ubs/
│   ├── Q1-2024/
│   │   ├── html/           (Downloaded HTML files)
│   │   ├── pdf/            (Downloaded PDFs)
│   │   └── md/             (Converted Markdown)
│   └── _meta/
│       ├── manifest.json   (File listing)
│       └── discovery.json  (URLs discovered)
├── gs/
│   ├── Q1-2024/
│   ├── Q2-2024/
│   └── _meta/
└── coverage.json           (Overall report)
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pipeline'"

```bash
# Ensure you're in the project root directory
pwd  # or "cd" to project directory

# Reinstall dependencies
pip install -r requirements.txt
```

### "No API key configured"

```bash
# Check if keys are set
echo %BRAVE_API_KEY%           # Windows
echo $BRAVE_API_KEY             # Linux/Mac

# If empty, set them again
set BRAVE_API_KEY=your_key
```

### "HTTP 401 Unauthorized"

- Check API key is correct
- Verify you copied the entire key with no spaces
- Try in a fresh terminal

### "No URLs discovered"

1. Check company website is accessible
2. Verify keywords are relevant
3. Run with `--log-level DEBUG` to see search queries

---

## Common Commands

```bash
# Run full pipeline
python main.py run

# Run single company
python main.py run --company ubs

# Debug mode
python main.py run --log-level DEBUG

# Generate report
python main.py report

# Get example config
python main.py example-config

# Show help
python main.py --help
```

---

## Next Steps

1. **Customize Config**: Edit `config.yaml` to add your companies
2. **Monitor Logs**: Check `pipeline.log` for details
3. **Review Output**: Check files in `output/` directory
4. **Check Report**: View `output/coverage.json`

---

## Need Help?

See `README.md` for comprehensive documentation.
