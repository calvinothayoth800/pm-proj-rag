@echo off
echo ====================================
echo Deploying UI Updates to HF Spaces
echo ====================================
echo.

cd /d "d:\pm proj\pm-proj-rag"

echo Committing UI improvements...
git add -A
git commit -m "Optimize UI for HF Spaces - cleaner layout, better iframe support" 2>nul

echo.
echo Pushing to HF Spaces...
echo This may take a minute...
echo.

git push hf main --force

if %errorlevel% equ 0 (
    echo.
    echo ====================================
    echo SUCCESS! Deploying now...
    echo Check your Space at:
    echo https://huggingface.co/spaces/calvinothayoth/pm-proj-rag
    echo.
    echo Build takes ~5-10 minutes first time.
    echo ====================================
) else (
    echo.
    echo ====================================
    echo Push failed. Check error above.
    echo ====================================
)

echo.
pause
