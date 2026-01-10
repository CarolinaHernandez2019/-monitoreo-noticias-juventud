@echo off
cd /d "C:\Users\carol\Claude_projects\SDIS\Monitoreo noticias juventud"
python scraper.py >> logs\scraper.log 2>&1
