# M0 收尾：归档旧项目（移动而非删除，可逆）

$ErrorActionPreference = 'Stop'
$root    = 'F:\Samuel\football recruitment'
$src     = Join-Path $root 'final project'
$archive = Join-Path $root 'archive\msc-inter-departure-2025'

Write-Output "=== 步骤 1：校验源目录 ==="
if (-not (Test-Path $src)) { throw "源目录不存在: $src" }
if (Test-Path $archive) { throw "归档目标已存在，中止以免覆盖: $archive" }

# 待移动的顶层条目（排除 venv / IDE / 工具配置，它们在 README 中说明）
$exclude = @('venv', '.idea', '.claude', 'claude-code', '111.txt')
$items = Get-ChildItem -Path $src -Force | Where-Object { $exclude -notcontains $_.Name }
Write-Output ("待移动顶层条目数 = {0}（已排除: {1}）" -f $items.Count, ($exclude -join ', '))

Write-Output "`n=== 步骤 2：归档前统计（用于事后校验） ==="
$before = Get-ChildItem -Path $src -Recurse -Force -File |
          Where-Object { $_.FullName -notmatch '\\venv\\' }
$beforeCount = $before.Count
$beforeBytes = ($before | Measure-Object -Property Length -Sum).Sum
Write-Output ("归档前文件数 = {0}, 总字节 = {1:N0}" -f $beforeCount, $beforeBytes)

Write-Output "`n=== 步骤 3：创建归档目录并移动 ==="
New-Item -ItemType Directory -Path $archive -Force | Out-Null
foreach ($it in $items) {
    Move-Item -LiteralPath $it.FullName -Destination $archive -Force
    Write-Output ("  已移动: {0}" -f $it.Name)
}

Write-Output "`n=== 步骤 4：归档后校验 ==="
$after = Get-ChildItem -Path $archive -Recurse -Force -File |
         Where-Object { $_.FullName -notmatch '\\venv\\' }
$afterCount = $after.Count
$afterBytes = ($after | Measure-Object -Property Length -Sum).Sum
Write-Output ("归档后文件数 = {0}, 总字节 = {1:N0}" -f $afterCount, $afterBytes)

if ($afterCount -eq $beforeCount -and $afterBytes -eq $beforeBytes) {
    Write-Output "`n[OK] 校验通过：文件数与总字节完全一致，无丢失。"
} else {
    Write-Output ("`n[警告] 不一致！ 文件数差 {0}, 字节差 {1:N0}" -f ($afterCount-$beforeCount), ($afterBytes-$beforeBytes))
}

Write-Output "`n=== 步骤 5：生成 SHA256 清单（可追溯性） ==="
$manifest = Join-Path $archive 'MANIFEST_SHA256.txt'
$after | Where-Object { $_.Extension -ne '.pyc' } |
    Sort-Object FullName |
    ForEach-Object {
        $h = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        "{0}  {1}" -f $h, $_.FullName.Substring($archive.Length + 1)
    } | Set-Content -LiteralPath $manifest -Encoding UTF8
Write-Output ("已写入清单: {0}（{1} 条）" -f $manifest, ((Get-Content $manifest) | Measure-Object).Count)

Write-Output "`n=== 步骤 6：源目录残留检查 ==="
$left = Get-ChildItem -Path $src -Force
Write-Output ("final project 目录剩余条目: {0}" -f (($left | ForEach-Object { $_.Name }) -join ', '))
