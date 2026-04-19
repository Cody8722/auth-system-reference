@echo off
echo 啟動 Auth System...

start "Node.js :3001" cmd /k "node node-express/server.js"
start "Python  :3002" cmd /k "python python-flask/app.py"

echo 兩個 server 已在新視窗啟動。
echo   Node.js  http://localhost:3001
echo   Python   http://localhost:3002
