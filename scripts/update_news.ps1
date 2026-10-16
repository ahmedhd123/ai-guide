# تحديث أخبار ai.watnia.com من هذا الجهاز (بديل GitHub Actions).
# يشغّله Task Scheduler أسبوعياً: يسحب آخر نسخة، يحدّث news.json، ويدفعه إن تغيّر.
$ErrorActionPreference = 'Stop'
$Repo   = Split-Path -Parent $PSScriptRoot
$Python = 'C:\Users\ahmed\AppData\Local\Programs\Python\Python311\python.exe'
$Git    = 'C:\Program Files\Git\cmd\git.exe'
$Log    = Join-Path $Repo 'scripts\update_news.log'
$env:PYTHONIOENCODING = 'utf-8'

function Write-Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg" | Out-File -FilePath $Log -Append -Encoding utf8
}

try {
    Set-Location $Repo
    Write-Log '--- بدء التحديث ---'
    & $Git pull --rebase --quiet origin main 2>&1 | ForEach-Object { Write-Log "git: $_" }
    & $Python (Join-Path $Repo 'scripts\fetch_news.py') 2>&1 | ForEach-Object { Write-Log "fetch: $_" }

    & $Git diff --quiet -- news.json
    if ($LASTEXITCODE -eq 0) { Write-Log 'لا جديد — لا دفع'; exit 0 }

    & $Git add news.json
    & $Git -c user.name='Ahmed' -c user.email='ahmedhd123@gmail.com' commit --quiet -m 'chore: تحديث الأخبار (من الجهاز المحلي)'
    & $Git push --quiet origin main 2>&1 | ForEach-Object { Write-Log "git: $_" }
    if ($LASTEXITCODE -ne 0) { throw "git push فشل ($LASTEXITCODE)" }
    Write-Log 'تم الدفع'
}
catch {
    Write-Log "خطأ: $_"
    exit 1
}
