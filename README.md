# AgentFleex

Каркас репозитория для разработки с агентами (Codex, Claude Code): правила для агентов, общие
скилы, Git-процесс с защитой ключевых веток и проверки, которые держат всё это согласованным.
От языка проекта не зависит: проверки написаны на Python и запускаются через `uv run`, отдельный
Python-проект для них не нужен.

## Что внутри

| Путь | Назначение |
| --- | --- |
| [AGENTS.md](./AGENTS.md) | Маршрутизатор для агентов: инварианты, источники истины, выбор скилов, отчёт |
| `CLAUDE.md` | Подключает AGENTS.md для Claude Code |
| `Skills/` | Скилы; `.agents/skills` и `.claude/skills` — симлинки на этот каталог |
| `Scripts/` | Проверки правил, скилов, документации, рабочей ветки и установка hooks |
| `.githooks/pre-push` | Запрет push в `integration`, `dev`, `production` |
| `.github/workflows/` | CI с проверкой направления PR и аудит push в ключевые ветки |
| [Docs/README.md](./Docs/README.md) | Документация, в том числе Git-процесс |
| [Tests/README.md](./Tests/README.md) | Тесты проверок |
| [TODO.md](./TODO.md) | Backlog |

Общие скилы с префиксом `kit-` переносимы между проектами: `kit-agent-rules` (правила и
маршрутизация), `kit-skill-authoring` (создание скилов), `kit-docs` (документация).

## Новый проект из каркаса

1. Создай репозиторий из AgentFleex и переименуй ветку по умолчанию в `integration`.
2. Установи hooks: `uv run Scripts/setup_git_hooks.py`.
3. В `AGENTS.md` перепиши раздел Project, добавь инварианты предметной области и владельцев в
   таблицу источников истины. Файл читается при каждом запросе к модели, поэтому держи его коротким.
4. Проектные скилы называй с префиксом проекта (`<project>-<job>`) и добавляй в таблицу
   маршрутизации `AGENTS.md`; порядок описан в `Skills/kit-skill-authoring/SKILL.md`.
5. Добавь в CI проверки кода проекта рядом с заданием проверок каркаса.

## Проверки

```bash
uv run Scripts/check_docs.py
uv run Scripts/check_agent_rules.py
uv run Scripts/check_skills.py Skills
uv run --no-project --with pytest --with pyyaml python -m pytest -q Tests
```

## Соглашения

- `AGENTS.md` и `Skills/**` пишутся на английском, документация для людей — на русском.
- Агент не делает commit, push, PR и merge; это делает разработчик.
- Правила веток и версии описаны в [Docs/GIT_WORKFLOW.md](./Docs/GIT_WORKFLOW.md).
