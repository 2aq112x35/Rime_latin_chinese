# 安装「带调拼音」到小狼毫 / Rime 用户目录，并重新部署
#
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -RimeDir "D:\Rime" -NoDeploy
#
param(
    [string]$RimeDir = "$env:APPDATA\Rime",
    [string]$WeaselDeployer = "C:\Program Files\Rime\weasel-0.17.4\WeaselDeployer.exe",
    [switch]$NoDeploy
)

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path -LiteralPath $RimeDir -PathType Container)) {
    throw "找不到 Rime 用户目录: $RimeDir（小狼毫一般是 %APPDATA%\Rime）"
}
Write-Host "目标用户目录: $RimeDir"

# 1. 复制方案文件
Copy-Item -LiteralPath (Join-Path $Here "pinyin_tone.schema.yaml") -Destination $RimeDir -Force
Copy-Item -LiteralPath (Join-Path $Here "rime.lua") -Destination $RimeDir -Force
New-Item -ItemType Directory -Force -Path (Join-Path $RimeDir "lua") | Out-Null
Copy-Item -LiteralPath (Join-Path $Here "lua\pinyin_tone.lua") -Destination (Join-Path $RimeDir "lua") -Force
Copy-Item -LiteralPath (Join-Path $Here "lua\pinyin_tone_data.lua") -Destination (Join-Path $RimeDir "lua") -Force
Write-Host "已复制: pinyin_tone.schema.yaml, rime.lua, lua\pinyin_tone.lua, lua\pinyin_tone_data.lua"

# 2. 把方案登记进 default.custom.yaml 的 schema_list（已有则跳过）
$DefaultCustom = Join-Path $RimeDir "default.custom.yaml"
$nl = "`n"
if (Test-Path -LiteralPath $DefaultCustom) {
    $raw = [IO.File]::ReadAllText($DefaultCustom)
    if ($raw.Contains("`r`n")) { $nl = "`r`n" }
} else {
    $raw = ""
}

if ($raw -match "pinyin_tone") {
    Write-Host "default.custom.yaml 里已经有 pinyin_tone，跳过改写"
} else {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    if ($raw.Length -gt 0) {
        Copy-Item -LiteralPath $DefaultCustom -Destination "$DefaultCustom.bak-$stamp" -Force
        Write-Host "已备份: default.custom.yaml.bak-$stamp"
    }

    $line = "    - {schema: pinyin_tone}"
    # 按行处理，避免正则 \s*/$ 在 CRLF 上踩坑
    $lines = @($raw -split "\r?\n")
    $idx = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^[ \t]*schema_list:[ \t]*$') { $idx = $i; break }
    }
    if ($idx -ge 0) {
        $out = New-Object System.Collections.Generic.List[string]
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $out.Add($lines[$i])
            if ($i -eq $idx) { $out.Add($line) }
        }
        $new = ($out -join $nl)
    } elseif ($raw.Trim().Length -gt 0 -and ($lines -match '^patch:').Count -gt 0) {
        # 有 patch 但还没 schema_list：补一段
        $new = ($lines -join $nl).TrimEnd() + $nl + $nl + "  schema_list:" + $nl + $line + $nl
    } else {
        $new = "patch:" + $nl + "  schema_list:" + $nl + $line + $nl
    }
    [IO.File]::WriteAllText($DefaultCustom, $new, (New-Object Text.UTF8Encoding($false)))
    Write-Host "已登记到 schema_list: pinyin_tone"
}

# 3. 重新部署
if ($NoDeploy) {
    Write-Host "-NoDeploy 已指定，跳过部署。请自己右键小狼毫图标「重新部署」。"
} elseif (Test-Path -LiteralPath $WeaselDeployer) {
    Write-Host "正在重新部署: $WeaselDeployer /deploy"
    & $WeaselDeployer /deploy
    Start-Sleep -Seconds 2
    $build = Join-Path $RimeDir "build\pinyin_tone.schema.yaml"
    if (Test-Path -LiteralPath $build) {
        Write-Host "部署完成，build\pinyin_tone.schema.yaml 已生成"
    } else {
        Write-Host "部署命令已执行，但没看到 build\pinyin_tone.schema.yaml。"
        Write-Host "若方案面板里没有「带调拼音」，试试再部署一次，或看日志: $env:TEMP\rime.weasel"
    }
} else {
    Write-Host "没找到 WeaselDeployer: $WeaselDeployer"
    Write-Host "请手动右键小狼毫图标「重新部署」，或用 -WeaselDeployer 指定路径。"
}

Write-Host ""
Write-Host "装好了。切方案：右键小狼毫图标 →「方案选单」选「带调拼音」，或按 Ctrl+`` 循环切换。"
