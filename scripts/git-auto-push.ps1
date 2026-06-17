$repoDir = "C:\Users\3580188\Documents\opencode\controle almoxarifado"
$env:Path = "C:\Program Files\Git\bin;C:\Program Files\Git\cmd;$env:Path"

Set-Location $repoDir
$date = Get-Date -Format "yyyy-MM-dd HH:mm"
git add -A
$status = git status --porcelain
if ($status) {
    git commit -m "Auto-commit $date"
    git push origin main
} else {
    Write-Output "Nothing to commit"
}
