function Kill-Port($port) {
    $line = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING" | Select-Object -First 1
    if ($line) {
        $pid_ = ($line.ToString().Trim() -split '\s+')[-1]
        taskkill /PID $pid_ /F 2>$null | Out-Null
    }
}

function Wait-Server($port) {
    Write-Host "  Waiting for port $port ..." -NoNewline
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("localhost", $port)
            $tcp.Close()
            Write-Host " ready."
            return
        } catch {}
        Write-Host "." -NoNewline
        Start-Sleep 1
    }
    Write-Host " timeout!"
}

function Restart-Servers {
    Write-Host ""
    Write-Host "--- Restarting servers to reset rate limits ---"
    Kill-Port 3001
    Kill-Port 3002
    Start-Sleep 3
    Start-Process powershell -ArgumentList "-Command", "Set-Location node-express; node server.js" -WindowStyle Normal
    Start-Process powershell -ArgumentList "-Command", "Set-Location python-flask; python app.py" -WindowStyle Normal
    Wait-Server 3001
    Wait-Server 3002
    Write-Host ""
}

Write-Host "Running attack tests..."
Write-Host ""

Restart-Servers

python attack-tests/03_nosql_injection.py
Write-Host ""
python attack-tests/06_ip_spoofing.py

Restart-Servers

python attack-tests/07_password_spray.py

Restart-Servers

python attack-tests/08_jwt_session_persistence.py
Write-Host ""
python attack-tests/09_oversized_input.py
Write-Host ""
python attack-tests/10_cors_headers.py
Write-Host ""
python attack-tests/02_jwt_attacks.py
Write-Host ""
python attack-tests/05_reset_token.py

Restart-Servers

python attack-tests/01_brute_force.py
Write-Host ""
python attack-tests/04_enumeration.py
Write-Host ""
Write-Host "Done."
Read-Host "Press Enter to close"
