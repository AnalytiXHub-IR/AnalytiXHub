# Start OPENCHAIN IR v4.0

Write-Host "Starting OPENCHAIN IR..." -ForegroundColor Green

# Start Redis (if not running)
Write-Host "Checking Redis..." -ForegroundColor Yellow
try {
    $redis = Get-Process redis-server -ErrorAction SilentlyContinue
    if ($null -eq $redis) {
        Write-Host "Starting Redis..." -ForegroundColor Yellow
        Start-Process redis-server
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "Redis not found - using Docker fallback" -ForegroundColor Yellow
    docker run -d -p 6379:6379 redis:latest | Out-Null
    Start-Sleep -Seconds 2
}

# Start PostgreSQL
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
Start-Service -Name postgresql-x64-15 -ErrorAction SilentlyContinue

# Install/upgrade dependencies
Write-Host "Updating dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Start Flask app
Write-Host "Starting Flask app..." -ForegroundColor Green
python app.py
