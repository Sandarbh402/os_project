@echo off
REM Windows CLI wrapper invoking Docker in WSL2 with root privileges
wsl -u root docker %*
