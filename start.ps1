Write-Host "Starting Auth System..."

Start-Process powershell -ArgumentList "-Command", "Set-Location node-express; node server.js" -WindowStyle Normal
Start-Process powershell -ArgumentList "-Command", "Set-Location python-flask; python app.py" -WindowStyle Normal

Write-Host "Servers started."
Write-Host "  Node.js  http://localhost:3001"
Write-Host "  Python   http://localhost:3002"
