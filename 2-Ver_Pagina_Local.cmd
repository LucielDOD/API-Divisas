@echo off
title Servidor Visor de Divisas
echo =======================================================
echo Levantando servidor local para evitar bloqueos del navegador (CORS)...
echo =======================================================
echo.
echo Abre tu navegador en la siguiente direccion:
echo http://localhost:8000
echo.
echo (Esta ventana debe mantenerse abierta mientras ves la pagina)
echo.

start http://localhost:8000
python -m http.server 8000
