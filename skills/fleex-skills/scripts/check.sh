#!/usr/bin/env bash
# Validate agent wiring, skill packages, $skill references, and relative Markdown links in the
# git repository of the current directory; this plugin's own skills count as known references.
# Prints one "path: problem" line per error and exits 1; prints "check: ok" otherwise.
set -u

plugin_skills=$(cd "$(dirname "$0")/../.." && pwd -P) || exit 2
root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "check: run inside the git repository" >&2
  exit 2
}
cd "$root" || exit 2

skills=.agents/skills
fail=0
err() { echo "$1: $2" >&2; fail=1; }

# Value of a single-line frontmatter field, without surrounding quotes.
field() {
  sed -n '2,/^---$/p' "$1" | sed -n "s/^$2:[[:space:]]*//p" | head -n1 |
    sed -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

[ "$(cat CLAUDE.md 2>/dev/null)" = "@AGENTS.md" ] ||
  err CLAUDE.md "must contain exactly '@AGENTS.md'"
if [ -d "$skills" ] && { [ ! -L .claude/skills ] ||
  [ "$(cd .claude/skills 2>/dev/null && pwd -P)" != "$(cd "$skills" && pwd -P)" ]; }; then
  err .claude/skills "must be a symlink that resolves to $skills"
fi

names=" "
for dir in "$plugin_skills"/*/; do
  [ -f "$dir/SKILL.md" ] && dir=${dir%/} && names="$names${dir##*/} "
done
for dir in "$skills"/*/; do
  [ -d "$dir" ] || continue
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

while IFS=: read -r file ref; do
  case $names in *" ${ref#\$} "*) ;; *) err "$file" "unknown skill reference $ref" ;; esac
done < <(grep -roE --include='*.md' --include='*.yaml' '\$[a-z][a-z0-9]*(-[a-z0-9]+)*' \
  $(ls -d AGENTS.md "$skills" 2>/dev/null) /dev/null | sort -u)

while IFS= read -r md; do
  base=$(dirname "$md")
  while IFS= read -r target; do
    case $target in
      *:*) continue ;;
      /*) path=.$target ;;
      *) path=$base/$target ;;
    esac
    [ -e "$path" ] || err "$md" "broken link $target"
  done < <(grep -oE '\]\([^)#[:space:]]+' "$md" | sed 's/^](//')
done < <(git ls-files -co --exclude-standard '*.md')

[ $fail = 0 ] && echo "check: ok"
exit $fail
