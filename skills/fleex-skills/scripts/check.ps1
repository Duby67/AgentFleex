# Validate agent wiring, skill packages, $skill references, and relative Markdown links in the
# git repository of the current directory; this plugin's own skills count as known references and
# are validated too when the repository is the plugin itself.
# Prints one "path: problem" line per error and exits 1; prints "check: ok" otherwise.
$ErrorActionPreference = 'Stop'

$pluginSkills = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path

$root = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $root) {
    [Console]::Error.WriteLine('check: run inside the git repository')
    exit 2
}
Set-Location $root

$here = (Get-Location).Path
$dirs = @()
if ($pluginSkills -eq (Join-Path $here 'skills')) { $dirs += 'skills' }
$script:fail = $false
function Err($path, $message) {
    [Console]::Error.WriteLine("${path}: $message")
    $script:fail = $true
}

# Value of a single-line frontmatter field, without surrounding quotes.
function Get-Field($lines, $name) {
    for ($i = 1; $i -lt $lines.Count -and $lines[$i] -ne '---'; $i++) {
        if ($lines[$i] -match "^${name}:\s*(.*?)\s*$") {
            return $Matches[1] -replace '^"(.*)"$', '$1' -replace "^'(.*)'$", '$1'
        }
    }
    return ''
}

# AGENTS.md is the only entry point; Claude Code, when used, imports it from .claude/CLAUDE.md.
if (Test-Path CLAUDE.md) {
    Err 'CLAUDE.md' "move to .claude/CLAUDE.md containing exactly '@../AGENTS.md'"
}
if (Test-Path .claude -PathType Container) {
    if (-not (Test-Path .claude/CLAUDE.md) -or
        (Get-Content -Raw .claude/CLAUDE.md).TrimEnd() -ne '@../AGENTS.md') {
        Err '.claude/CLAUDE.md' "must contain exactly '@../AGENTS.md'"
    }
    if (-not (Test-Path AGENTS.md)) { Err 'AGENTS.md' 'missing; .claude/CLAUDE.md imports it' }
}
# A plugin repository ships one version to both clients.
if ((Test-Path .claude-plugin/plugin.json) -and (Test-Path .codex-plugin/plugin.json) -and
    (Get-Content -Raw .claude-plugin/plugin.json | ConvertFrom-Json).version -ne
    (Get-Content -Raw .codex-plugin/plugin.json | ConvertFrom-Json).version) {
    Err '.codex-plugin/plugin.json' 'version must match .claude-plugin/plugin.json'
}
# Final target of a path through any chain of symlinks (PowerShell 7.2+).
function Get-RealPath($path) {
    $item = Get-Item -Force $path -ErrorAction SilentlyContinue
    if (-not $item) { return $null }
    $target = $item.ResolveLinkTarget($true)
    if ($target) { $target.FullName } else { $item.FullName }
}
# A path inside the repository as repository-relative with forward slashes; others unchanged.
function Get-RepoPath($path) {
    if ($path.StartsWith($here + [IO.Path]::DirectorySeparatorChar)) {
        return $path.Substring($here.Length + 1) -replace '\\', '/'
    }
    return $path
}

# Project skills live in skills/; agent paths link to it.
$candidates = @('skills') + @(Get-ChildItem -Force -Directory |
    Where-Object { $_.Name.StartsWith('.') } | ForEach-Object { "$($_.Name)/skills" })
$source = $null
foreach ($path in $candidates) {
    if (-not (Get-Item -Force $path -ErrorAction SilentlyContinue)) { continue }
    if ($path -ne 'skills') {
        $item = Get-Item -Force $path
        if ($item.LinkType -ne 'SymbolicLink' -or $item.LinkTarget -ne '../skills') {
            Err $path "must be a relative symlink '../skills' to root skills/"
        }
    }
    $target = Get-RealPath $path
    if (-not (Test-Path $target -PathType Container)) { Err $path 'broken symlink'; continue }
    if (-not $source) {
        $source = $target
    } elseif ($target -ne $source) {
        $to = Get-RepoPath $source
        Err $path "duplicate skills directory; make it a relative symlink to $to"
    }
}
if ($source) {
    $sourceRel = Get-RepoPath $source
    if ($source -ne (Join-Path $here 'skills')) {
        Err $sourceRel 'move project skills to skills/ and link agent paths to it'
    }
    foreach ($agent in @('.agents', '.claude', '.cursor')) {
        if ((Test-Path $agent -PathType Container) -and
            -not (Get-Item -Force "$agent/skills" -ErrorAction SilentlyContinue)) {
            Err "$agent/skills" "agent is used; make it a relative symlink '../skills'"
        }
    }
    if ($source -ne $pluginSkills) { $dirs += $sourceRel }
}

$names = @(Get-ChildItem -Directory $pluginSkills |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object Name)
$packages = @()
if ($dirs) { $packages = Get-ChildItem -Directory $dirs -ErrorAction SilentlyContinue }
foreach ($dir in $packages) {
    $id = $dir.Name
    $rel = (Resolve-Path -Relative $dir.FullName) -replace '\\', '/' -replace '^\./', ''
    $file = "$rel/SKILL.md"
    if (-not (Test-Path $file)) { Err $rel 'missing SKILL.md'; continue }
    $names += $id
    $lines = @(Get-Content $file)

    if ($lines[0] -ne '---') { Err $file 'must start with YAML frontmatter' }
    $name = Get-Field $lines 'name'
    $desc = Get-Field $lines 'description'
    if ($name -cne $id) { Err $file "name '$name' must match directory '$id'" }
    if ($name -cnotmatch '^[a-z0-9]+(-[a-z0-9]+)*$' -or $name.Length -gt 64) {
        Err $file 'name must be 1-64 characters of a-z, 0-9, and single inner hyphens'
    }
    if ($name -match 'claude|anthropic') {
        Err $file "name must not contain the reserved words 'claude' or 'anthropic'"
    }
    if (-not $desc -or $desc -match '^[>|]' -or $desc.Length -gt 1024) {
        Err $file 'description must be one line of 1-1024 characters'
    }
    if ($lines.Count -gt 200) { Err $file 'must stay under 200 lines' }

    $gated = (Get-Field $lines 'disable-model-invocation') -eq 'true'
    $yaml = "$rel/agents/openai.yaml"
    if (Test-Path $yaml) {
        $text = Get-Content -Raw $yaml
        $refs = [regex]::Matches($text, '\$[a-z0-9]+(-[a-z0-9]+)*') | ForEach-Object Value
        if ($refs -cnotcontains "`$$id") { Err $yaml "default_prompt must mention `$$id" }
        $implicit = $text -notmatch 'allow_implicit_invocation:\s*false'
        if ($gated -and $implicit) {
            Err $yaml 'user-gated skill needs policy.allow_implicit_invocation: false'
        } elseif (-not $gated -and -not $implicit) {
            Err $file 'implicit invocation is off in Codex; set disable-model-invocation: true'
        }
    } elseif ($gated) {
        Err $file 'user-gated skill needs agents/openai.yaml with policy.allow_implicit_invocation: false'
    }
}

$refSources = @()
if ($dirs) {
    $refSources = Get-ChildItem -Recurse -File $dirs -Include *.md, *.yaml `
        -ErrorAction SilentlyContinue
}
$refFiles = @(Get-Item AGENTS.md -ErrorAction SilentlyContinue | ForEach-Object Name) +
    @($refSources |
    ForEach-Object { (Resolve-Path -Relative $_.FullName) -replace '\\', '/' -replace '^\./', '' })
foreach ($f in $refFiles) {
    $refs = [regex]::Matches((Get-Content -Raw $f), '\$[a-z][a-z0-9]*(-[a-z0-9]+)*') |
        ForEach-Object Value | Sort-Object -Unique
    foreach ($ref in $refs) {
        if ($names -cnotcontains $ref.Substring(1)) { Err $f "unknown skill reference $ref" }
    }
}

# Relative link targets of a Markdown file, outside fenced and inline code.
function Get-Links($file) {
    $text = (Get-Content -Raw $file) + ''
    $text = $text -replace '(?ms)^[ \t]*(```|~~~).*?^[ \t]*(```|~~~)[^\n]*', ''
    $text = $text -replace '`[^`\n]*`', ''
    [regex]::Matches($text, '\]\(([^)#\s]+)') | ForEach-Object { $_.Groups[1].Value } |
        Where-Object { $_ -notmatch ':' }
}
foreach ($md in git ls-files -co --exclude-standard '*.md') {
    $base = Split-Path -Parent $md
    foreach ($target in Get-Links $md) {
        $path = if ($target.StartsWith('/')) { ".$target" } elseif ($base) { "$base/$target" } else { $target }
        if (-not (Test-Path $path)) { Err $md "broken link $target" }
    }
}

# Translations: AGENTS.md lists the languages as "translated to: ru, zh-CN". Every translation lives
# under docs/<code>/: a root file by name, a docs/ page at its path inside docs/. Each file of a set
# links to all the others.
function Get-LinkedFiles($file) {
    $base = Split-Path -Parent $file
    foreach ($target in Get-Links $file) {
        $path = if ($base) { Join-Path $base $target } else { $target }
        if (Test-Path $path -PathType Leaf) { (Resolve-Path $path).Path }
    }
}
$codes = @()
if ((Test-Path AGENTS.md) -and
    ((Get-Content -Raw AGENTS.md) -cmatch 'translated to:[ \t]*([A-Za-z0-9, -]*)')) {
    $codes = @($Matches[1] -split '[, ]+' | Where-Object { $_ })
}
$sets = [ordered]@{}
foreach ($code in $codes) {
    if ($code -cnotmatch '^[a-z]{2,3}(-[A-Za-z0-9]+)*$') {
        Err 'AGENTS.md' "'$code' is not a BCP 47 language code"
        continue
    }
    foreach ($file in git ls-files -co --exclude-standard -- "*.$code.md") {
        Err $file "translations live in docs/$code/, not beside the original"
    }
    foreach ($file in git ls-files -co --exclude-standard -- "docs/$code/*.md" 2>$null) {
        $rest = $file.Substring("docs/$code/".Length)
        $found = @()
        if (Test-Path "docs/$rest" -PathType Leaf) { $found += "docs/$rest" }
        if (-not $rest.Contains('/') -and (Test-Path $rest -PathType Leaf)) { $found += $rest }
        $original = $null
        if ($found.Count -eq 0) {
            if ($rest.Contains('/')) { Err $file "no English original docs/$rest" }
            else { Err $file "no English original $rest or docs/$rest" }
        } elseif ($found.Count -eq 1) {
            $original = $found[0]
        } else {
            # A root file and a docs/ page share the name; the switcher picks the original.
            $targets = @(Get-LinkedFiles $file)
            $linked = @($found | Where-Object { $targets -contains (Resolve-Path $_).Path })
            if ($linked.Count -eq 1) { $original = $linked[0] }
            else { Err $file "link exactly one of $rest and docs/$rest as the English original" }
        }
        if ($original) {
            if (-not $sets.Contains($original)) { $sets[$original] = @() }
            $sets[$original] += $file
        }
    }
}
foreach ($original in $sets.Keys) {
    $members = @($original) + $sets[$original]
    foreach ($file in $members) {
        $targets = @(Get-LinkedFiles $file)
        foreach ($other in $members) {
            if ($other -ne $file -and $targets -notcontains (Resolve-Path $other).Path) {
                Err $file "language switcher must link to $other"
            }
        }
    }
}

if ($script:fail) { exit 1 }
'check: ok'
