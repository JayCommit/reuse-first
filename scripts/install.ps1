# Copy the reuse-first skill into host skill directories.
# Windows counterpart of install.sh. macOS/Bash is the primary installer.
# SKILL.md lands at the destination root; scripts/ stays beside it.
# This file is not executed by the Linux release check.

$ErrorActionPreference = "Stop"

function Show-Usage {
    @"
Usage: install.ps1 [--host HOST] [--scope SCOPE]

Copy this skill so SKILL.md is the destination root and scripts/pattern_index.py
stays beside it. Existing copies are replaced in place and are not nested again.

--host HOST    grok | grok-bot | cursor | openai | antigravity | claude | all
               (default: all)
--scope SCOPE  user | project
               (default: user)

User scope writes under `$HOME. Project scope writes under the current directory.
"@
}

function Fail([string]$Message) {
    [Console]::Error.WriteLine("error: $Message")
    exit 2
}

if (-not $PSScriptRoot) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$Source = Split-Path -Parent $PSScriptRoot
$WorkRoot = (Get-Location).Path

$HostChoice = "all"
$Scope = "user"
$index = 0
while ($index -lt $args.Count) {
    $arg = [string]$args[$index]
    if ($arg -eq "--help" -or $arg -eq "-h") {
        Show-Usage
        exit 0
    }
    elseif ($arg -eq "--host" -or $arg -eq "--scope") {
        if ($index + 1 -ge $args.Count) {
            Fail "missing value for $arg"
        }
        $value = [string]$args[$index + 1]
        if ($arg -eq "--host") { $HostChoice = $value } else { $Scope = $value }
        $index += 2
        continue
    }
    elseif ($arg.StartsWith("--host=")) {
        $HostChoice = $arg.Substring(7)
        $index += 1
        continue
    }
    elseif ($arg.StartsWith("--scope=")) {
        $Scope = $arg.Substring(8)
        $index += 1
        continue
    }
    else {
        Fail "unknown argument: $arg"
    }
}

$validHosts = @("grok", "grok-bot", "cursor", "openai", "antigravity", "claude", "all")
$validScopes = @("user", "project")
$hostOk = $false
foreach ($item in $validHosts) {
    if ($item -ceq $HostChoice) { $hostOk = $true }
}
if (-not $hostOk) { Fail "unknown host: $HostChoice" }
$scopeOk = $false
foreach ($item in $validScopes) {
    if ($item -ceq $Scope) { $scopeOk = $true }
}
if (-not $scopeOk) { Fail "unknown scope: $Scope" }

$skillFile = Join-Path $Source "SKILL.md"
if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
    [Console]::Error.WriteLine("error: SKILL.md not found in $Source")
    exit 1
}

$items = @("SKILL.md", "agents", "references", "scripts", "tests", "README.md", "LICENSE")
foreach ($item in $items) {
    $from = Join-Path $Source $item
    if (-not (Test-Path -LiteralPath $from)) {
        [Console]::Error.WriteLine("error: missing $from")
        exit 1
    }
}

function Join-Skill([string]$Root, [string]$Tail) {
    $result = $Root
    foreach ($part in ($Tail -split "[\\/]+")) {
        if ($part) {
            $result = Join-Path -Path $result -ChildPath $part
        }
    }
    return $result
}

$destinations = New-Object System.Collections.Generic.List[string]
function Add-Dest([string]$Path) {
    foreach ($existing in $destinations) {
        if ($existing -ceq $Path) { return }
    }
    [void]$destinations.Add($Path)
}

function Selected([string]$Name) {
    return ($HostChoice -ceq "all" -or $HostChoice -ceq $Name)
}

if ($Scope -ceq "user") {
    if (-not $HOME) { Fail "HOME is not set" }
    if ((Selected "grok") -or (Selected "grok-bot")) {
        Add-Dest (Join-Skill $HOME ".grok/skills/reuse-first")
    }
    if (Selected "cursor") {
        Add-Dest (Join-Skill $HOME ".cursor/skills/reuse-first")
    }
    if (Selected "openai") {
        Add-Dest (Join-Skill $HOME ".agents/skills/reuse-first")
    }
    if (Selected "antigravity") {
        Add-Dest (Join-Skill $HOME ".gemini/config/skills/reuse-first")
        Add-Dest (Join-Skill $HOME ".gemini/antigravity-cli/skills/reuse-first")
    }
    if (Selected "claude") {
        Add-Dest (Join-Skill $HOME ".claude/skills/reuse-first")
    }
}
else {
    if ((Selected "grok") -or (Selected "grok-bot")) {
        Add-Dest (Join-Skill $WorkRoot ".grok/skills/reuse-first")
    }
    if (Selected "cursor") {
        Add-Dest (Join-Skill $WorkRoot ".cursor/skills/reuse-first")
    }
    if ((Selected "openai") -or (Selected "antigravity")) {
        Add-Dest (Join-Skill $WorkRoot ".agents/skills/reuse-first")
    }
    if (Selected "claude") {
        Add-Dest (Join-Skill $WorkRoot ".claude/skills/reuse-first")
    }
}

function Install-SkillFolder([string]$Dest) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    foreach ($item in $items) {
        $from = Join-Path $Source $item
        $target = Join-Path $Dest $item
        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
        Copy-Item -LiteralPath $from -Destination $target -Recurse -Force
    }
    Get-ChildItem -LiteralPath $Dest -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
    Write-Output $Dest
}

Write-Output "Installed reuse-first ($HostChoice, $Scope)"
if ($destinations.Count -eq 0) {
    [Console]::Error.WriteLine("error: no destination for host=$HostChoice scope=$Scope")
    exit 1
}
foreach ($dest in $destinations) {
    Install-SkillFolder $dest
}

if ($HostChoice -ceq "grok-bot" -or $HostChoice -ceq "all") {
    Write-Output ""
    Write-Output "Grok Bot paste-in prompt:"
    Write-Output "Install the reuse-first skill on this computer. Clone https://github.com/JayCommit/reuse-first and copy that checkout so SKILL.md is at ~/.grok/skills/reuse-first/SKILL.md, with scripts/ beside SKILL.md. Do not nest another reuse-first directory inside it. Use that same SKILL.md. Invoke /reuse-first."
}
