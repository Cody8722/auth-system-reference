@echo off
echo 執行攻防測試...
echo 請確認兩個 server 已啟動（start.bat）
echo.

python attack-tests/01_brute_force.py
echo.
python attack-tests/02_jwt_attacks.py
echo.
python attack-tests/03_nosql_injection.py
echo.
python attack-tests/04_enumeration.py
echo.
python attack-tests/05_reset_token.py
echo.
echo 全部完成。
pause
