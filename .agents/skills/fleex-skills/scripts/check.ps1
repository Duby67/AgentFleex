# Validate agent wiring, skill packages, $skill references, and relative Markdown links.
# Prints one "path: problem" line per error and exits 1; prints "check: ok" otherwise.
$ErrorActionPreference = 'Stop'

$root = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $root) {
    [Console]::Error.WriteLine('check: run inside the git repository')
    exit 2
}
Set-Location $root

$skills = '.agents/skills'
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

if (-not (Test-Path CLAUDE.md) -or (Get-Content -Raw CLAUDE.md).TrimEnd() -ne '@AGENTS.md') {
    Err 'CLAUDE.md' "must contain exactly '@AGENTS.md'"
}
$link = Get-Item -Force .claude/skills -ErrorAction SilentlyContinue
$skillsFull = (Resolve-Path $skills).Path
if (-not $link -or -not $link.LinkType -or
    (Resolve-Path .claude/skills -ErrorAction SilentlyContinue).Path -ne $skillsFull) {
    Err '.claude/skills' "must be a symlink that resolves to $skills"
}

$names = @()
foreach ($dir in Get-ChildItem -Directory $skills) {
    $id = $dir.Name
    $rel = "$skills/$id"
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

$refFiles = @('AGENTS.md') + (Get-ChildItem -Recurse -File $skills -Include *.md, *.yaml |
    ForEach-Object { (Resolve-Path -Relative $_.FullName) -replace '\\', '/' -replace '^\./', '' })
foreach ($f in $refFiles) {
    $refs = [regex]::Matches((Get-Content -Raw $f), '\$[a-z][a-z0-9]*(-[a-z0-9]+)*') |
        ForEach-Object Value | Sort-Object -Unique
    foreach ($ref in $refs) {
        if ($names -cnotcontains $ref.Substring(1)) { Err $f "unknown skill reference $ref" }
    }
}

foreach ($md in git ls-files -co --exclude-standard '*.md') {
    $base = Split-Path -Parent $md
    foreach ($m in [regex]::Matches((Get-Content -Raw $md), '\]\(([^)#\s]+)')) {
        $target = $m.Groups[1].Value
        if ($target -match ':') { continue }
        $path = if ($target.StartsWith('/')) { ".$target" } elseif ($base) { "$base/$target" } else { $target }
        if (-not (Test-Path $path)) { Err $md "broken link $target" }
    }
}

if ($script:fail) { exit 1 }
'check: ok'
