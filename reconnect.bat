@echo off
REM Reconnect face-detection to Forge network
echo Connecting face-detection to Forge network...
ssh truenas_admin@10.0.0.120 "sudo docker network connect ix-forge_default $(sudo docker ps -qf name=face-detection) 2>/dev/null || echo 'Already connected'"
echo Done!
pause
