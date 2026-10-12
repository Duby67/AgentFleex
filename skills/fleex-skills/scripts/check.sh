#!/usr/bin/env bash
# Validate agent wiring, skill packages, $skill references, and relative Markdown links in the
# git repository of the current directory; this plugin's own skills count as known references and
# are validated too when the repository is the plugin itself.
# Prints one "path: problem" line per error and exits 1; prints "check: ok" otherwise.
set -u

plugin_skills=$(cd "$(dirname "$0")/../.." && pwd -P) || exit 2
root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "check: run inside the git repository" >&2
  exit 2
}
cd "$root" || exit 2

here=$(pwd -P)
dirs=()
[ "$plugin_skills" = "$here/skills" ] && dirs+=(skills)
fail=0
err() { echo "$1: $2" >&2; fail=1; }

# Value of a single-line frontmatter field, without surrounding quotes.
field() {
  sed -n '2,/^---$/p' "$1" | sed -n "s/^$2:[[:space:]]*//p" | head -n1 |
    sed -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

# AGENTS.md is the only entry point; Claude Code, when used, imports it from .claude/CLAUDE.md.
[ -e CLAUDE.md ] && err CLAUDE.md "move to .claude/CLAUDE.md containing exactly '@../AGENTS.md'"
if [ -d .claude ]; then
  [ "$(cat .claude/CLAUDE.md 2>/dev/null)" = "@../AGENTS.md" ] ||
    err .claude/CLAUDE.md "must contain exactly '@../AGENTS.md'"
  [ -f AGENTS.md ] || err AGENTS.md "missing; .claude/CLAUDE.md imports it"
fi
# A plugin repository ships one version to both clients.
version() { sed -n 's/^ *"version": *"\([^"]*\)".*/\1/p' "$1" 2>/dev/null; }
if [ -f .claude-plugin/plugin.json ] && [ -f .codex-plugin/plugin.json ] &&
  [ "$(version .claude-plugin/plugin.json)" != "$(version .codex-plugin/plugin.json)" ]; then
  err .codex-plugin/plugin.json "version must match .claude-plugin/plugin.json"
fi

# Project skills live in skills/; agent paths link to it.
candidates=(skills .*/skills)
source=""
for path in "${candidates[@]}"; do
  # Bash before 5.2 (macOS ships 3.2) also matches . and .. with .*
  case $path in ./skills | ../skills) continue ;; esac
  [ -e "$path" ] || [ -L "$path" ] || continue
  if [ "$path" != skills ]; then
    if ! { [ -L "$path" ] && [ "$(readlink "$path")" = ../skills ]; }; then
      err "$path" "must be a relative symlink '../skills' to root skills/"
    fi
  fi
  target=$(cd "$path" 2>/dev/null && pwd -P) || { err "$path" "broken symlink"; continue; }
  if [ -z "$source" ]; then
    source=$target
  elif [ "$target" != "$source" ]; then
    err "$path" "duplicate skills directory; make it a relative symlink to ${source#"$here"/}"
  fi
done
if [ -n "$source" ]; then
  rel=${source#"$here"/}
  [ "$source" = "$here/skills" ] ||
    err "$rel" "move project skills to skills/ and link agent paths to it"
  # Only local, untracked content shows an agent in use; committed plugin metadata does not.
  for agent in .agents .claude .cursor; do
    [ -d "$agent" ] && [ ! -e "$agent/skills" ] && [ ! -L "$agent/skills" ] &&
      [ -n "$(git ls-files --others -- "$agent")" ] &&
      err "$agent/skills" "agent is used; make it a relative symlink '../skills'"
  done
  [ "$source" = "$plugin_skills" ] || dirs+=("$rel")
fi

names=" "
for dir in "$plugin_skills"/*/; do
  [ -f "$dir/SKILL.md" ] && dir=${dir%/} && names="$names${dir##*/} "
done
# Arrays stay safe under set -u on bash 3.2 (macOS) through the ${a[@]+"${a[@]}"} form.
packages=()
for base in ${dirs[@]+"${dirs[@]}"}; do
  for dir in "$base"/*/; do [ -d "$dir" ] && packages+=("$dir"); done
done
for dir in ${packages[@]+"${packages[@]}"}; do
  dir=${dir%/}
  id=${dir##*/}
  file=$dir/SKILL.md
  [ -f "$file" ] || { err "$dir" "missing SKILL.md"; continue; }
  names="$names$id "

  [ "$(head -n1 "$file")" = "---" ] || err "$file" "must start with YAML frontmatter"
  name=$(field "$file" name)
  desc=$(field "$file" description)
  [ "$name" = "$id" ] || err "$file" "name '$name' must match directory '$id'"
  if ! echo "$name" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$' || [ ${#name} -gt 64 ]; then
    err "$file" "name must be 1-64 characters of a-z, 0-9, and single inner hyphens"
  fi
  echo "$name" | grep -Eq 'claude|anthropic' &&
    err "$file" "name must not contain the reserved words 'claude' or 'anthropic'"
  case $desc in '' | '>'* | '|'*) desc="" ;; esac
  if [ -z "$desc" ] || [ ${#desc} -gt 1024 ]; then
    err "$file" "description must be one line of 1-1024 characters"
  fi
  [ "$(wc -l <"$file")" -le 200 ] || err "$file" "must stay under 200 lines"

  gated=no
  [ "$(field "$file" disable-model-invocation)" = true ] && gated=yes
  yaml=$dir/agents/openai.yaml
  if [ -f "$yaml" ]; then
    grep -oE '\$[a-z0-9]+(-[a-z0-9]+)*' "$yaml" | grep -qx "\$$id" ||
      err "$yaml" "default_prompt must mention \$$id"
    implicit=yes
    grep -Eq 'allow_implicit_invocation:[[:space:]]*false' "$yaml" && implicit=no
    if [ $gated = yes ] && [ $implicit = yes ]; then
      err "$yaml" "user-gated skill needs policy.allow_implicit_invocation: false"
    elif [ $gated = no ] && [ $implicit = no ]; then
      err "$file" "implicit invocation is off in Codex; set disable-model-invocation: true"
    fi
  elif [ $gated = yes ]; then
    err "$file" "user-gated skill needs agents/openai.yaml with policy.allow_implicit_invocation: false"
  fi
done

scan=()
for path in AGENTS.md ${dirs[@]+"${dirs[@]}"}; do [ -e "$path" ] && scan+=("$path"); done
while IFS=: read -r file ref; do
  case $names in *" ${ref#\$} "*) ;; *) err "$file" "unknown skill reference $ref" ;; esac
done < <(grep -roE --include='*.md' --include='*.yaml' '\$[a-z][a-z0-9]*(-[a-z0-9]+)*' \
  ${scan[@]+"${scan[@]}"} /dev/null | sort -u)

# Relative link targets of a Markdown file, outside fenced and inline code.
links() {
  # shellcheck disable=SC2016 # Backticks are Markdown code spans, not command substitution.
  awk '/^[[:space:]]*(```|~~~)/ { code = !code; next } !code' "$1" | sed 's/`[^`]*`//g' |
    grep -oE '\]\([^)#[:space:]]+' | sed 's/^](//' | grep -v ':'
}
while IFS= read -r md; do
  base=$(dirname "$md")
  while IFS= read -r target; do
    case $target in
      /*) path=.$target ;;
      *) path=$base/$target ;;
    esac
    [ -e "$path" ] || err "$md" "broken link $target"
  done < <(links "$md")
done < <(git ls-files -co --exclude-standard '*.md')

# Translations: AGENTS.md lists the languages as "translated to: ru, zh-CN". Every translation lives
# under docs/<code>/: a root file by name, a docs/ page at its path inside docs/. Each file of a set
# links to all the others.
real() { echo "$(cd "$(dirname "$1")" && pwd -P)/$(basename "$1")"; }
links_to() {
  local base target
  base=$(dirname "$1")
  while IFS= read -r target; do
    [ -f "$base/$target" ] && real "$base/$target"
  done < <(links "$1")
}
codes=$(sed -n 's/.*translated to:[[:space:]]*\([A-Za-z0-9, -]*\).*/\1/p' AGENTS.md 2>/dev/null |
  head -n1 | tr ',' ' ')
pairs=""
for code in $codes; do
  if ! echo "$code" | grep -Eq '^[a-z]{2,3}(-[A-Za-z0-9]+)*$'; then
    err AGENTS.md "'$code' is not a BCP 47 language code"
    continue
  fi
  while IFS= read -r file; do
    err "$file" "translations live in docs/$code/, not beside the original"
  done < <(git ls-files -co --exclude-standard -- "*.$code.md")
  while IFS= read -r file; do
    rest=${file#docs/"$code"/}
    found=()
    [ -f "docs/$rest" ] && found+=("docs/$rest")
    case $rest in */*) ;; *) [ -f "$rest" ] && found+=("$rest") ;; esac
    original=""
    case ${#found[@]} in
      0)
        case $rest in
          */*) err "$file" "no English original docs/$rest" ;;
          *) err "$file" "no English original $rest or docs/$rest" ;;
        esac
        ;;
      1) original=${found[0]} ;;
      *)
        # A root file and a docs/ page share the name; the switcher picks the original.
        targets=$(links_to "$file")
        for candidate in "${found[@]}"; do
          if printf '%s\n' "$targets" | grep -qxF "$(real "$candidate")"; then
            [ -z "$original" ] && original=$candidate || original=ambiguous
          fi
        done
        case $original in "" | ambiguous)
          err "$file" "link exactly one of $rest and docs/$rest as the English original"
          original=""
          ;;
        esac
        ;;
    esac
    [ -n "$original" ] && pairs="$pairs$original	$file
"
  done < <(git ls-files -co --exclude-standard -- "docs/$code/*.md" 2>/dev/null)
done
while IFS= read -r original; do
  [ -n "$original" ] || continue
  members=("$original")
  while IFS= read -r file; do members+=("$file"); done < <(
    printf '%s' "$pairs" | awk -F '\t' -v o="$original" '$1 == o { print $2 }')
  for file in "${members[@]}"; do
    targets=$(links_to "$file")
    for other in "${members[@]}"; do
      [ "$other" = "$file" ] && continue
      printf '%s\n' "$targets" | grep -qxF "$(real "$other")" ||
        err "$file" "language switcher must link to $other"
    done
  done
done < <(printf '%s' "$pairs" | cut -f1 | sort -u)

[ $fail = 0 ] && echo "check: ok"
exit $fail
