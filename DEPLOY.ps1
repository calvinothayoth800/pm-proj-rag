$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Deploying Prompt Fix to HF Spaces" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "d:\pm proj\pm-proj-rag"

Write-Host "Committing prompt improvements..." -ForegroundColor Yellow
git add -A
git commit -m "Fix prompt to extract specific fund data instead of generic definitions" 2>$null

Write-Host ""
Write-Host "Pushing to HF Spaces..." -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Gray
Write-Host ""

git push hf main --force 2>&1 | Out-String

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "SUCCESS! Deploying prompt fix..." -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
    Write-Host "Your Space: " -NoNewline -ForegroundColor White
    Write-Host "https://huggingface.co/spaces/calvinothayoth/pm-proj-rag" -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Green
    Write-Host "Rebuild takes ~2-3 minutes." -ForegroundColor Gray
    Write-Host "====================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "Push failed. Check error above." -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
