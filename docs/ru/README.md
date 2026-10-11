# AgentFleex

[English](../../README.md) · **Русский**

Плагин для Claude Code и Codex, который держит `AGENTS.md`, скиллы репозитория и документацию
короткими и согласованными.

## Установка

Claude Code:

```bash
claude plugin marketplace add Duby67/AgentFleex
claude plugin install agentfleex@agentfleex
```

Codex:

```bash
codex plugin marketplace add Duby67/AgentFleex
codex plugin add agentfleex@agentfleex
```

## Что плагин настраивает в репозитории

| Путь | Назначение |
| --- | --- |
| `AGENTS.md` | Единственный файл правил и единственная точка входа; Codex читает его сам |
| `.claude/CLAUDE.md` | Только для Claude Code: одна строка `@../AGENTS.md`, которая импортирует тот же файл |
| Источник скиллов | Одна папка, первая подходящая: собственная `skills/` репозитория; `.agents/skills/` для нескольких агентов; папка самого агента (`.claude/skills/`, `.cursor/skills/`) для одного |
| `.agents/skills`, `.claude/skills` | Относительные симлинки на источник, только для используемых агентов: Codex читает `.agents/skills`, Claude Code — `.claude/skills` |

Папка агента (`.claude/`, `.cursor/`) создаётся, только если репозиторий использует этого агента.

Общие скиллы `fleex-*` приходят из плагина и не копируются в репозиторий. Оба клиента находят скиллы
по полю `description`, поэтому `AGENTS.md` не нужна таблица маршрутизации.

Файлы для агентов (`AGENTS.md`, скиллы, документация для агентов) пишутся на английском.
Документация для людей тоже пишется на английском. Переводы появляются, только когда их просит
пользователь или `AGENTS.md` уже перечисляет языки, и все лежат в `docs/<код>/`: `README.md` — как
`docs/ru/README.md`, страница из `docs/` — по тому же пути внутри `docs/ru/`; в каждом файле набора
под заголовком стоит одна строка-переключатель языка. `AGENTS.md` перечисляет языки
(`translated to: ru`); удаление языка удаляет его файлы и больше ничего не переносит. В чате агент
отвечает на языке вопроса.

## Устройство репозитория

Корень репозитория — это корень плагина; скиллы лежат в `skills/`. Манифесты: `.claude-plugin/` и
`.codex-plugin/` (плагин), `.claude-plugin/marketplace.json` и `.agents/plugins/marketplace.json`
(маркетплейсы). Чтобы попробовать изменения скиллов, запустите Claude Code с
`claude --plugin-dir .`; в Codex переустановите плагин из локального маркетплейса. Тесты скриптов
скиллов лежат в `tests/` и запускаются командой `python3 -m unittest discover -s tests`; CI гоняет
их на Linux, macOS и Windows с Python 3.9 и последним Python, с Universal Ctags и без, а также
Ruff, mypy и ShellCheck. Установленные плагины подхватывают изменения только после повышения
`version` в обоих манифестах. Лицензия — [MIT](../../LICENSE).

## Экономия токенов

Главная статья расходов — файлы, которые агент читает часто, и прежде всего `AGENTS.md`: он
попадает в каждый запрос к модели. Поэтому:

- `AGENTS.md` содержит только то, что нужно в каждой задаче и что агент не выведет сам: что это за
  проект, жёсткие инварианты, указатели на владельцев;
- всё, что файл уже подразумевает или агент и так знает, удаляется;
- детали задач живут в скиллах: в каждый запрос попадает только их `description`, а тело читается
  по необходимости;
- каждый факт живёт в одном месте, всё остальное ссылается на него.

Каждый скилл владеет своими файлами: [fleex-agents](../../skills/fleex-agents/SKILL.md) владеет
`AGENTS.md`, `.claude/CLAUDE.md` и единым каталогом общих правил;
[fleex-skills](../../skills/fleex-skills/SKILL.md) — скиллами, их подключением и ссылками на лучшие
практики; [fleex-docs](../../skills/fleex-docs/SKILL.md) — документацией для людей;
[fleex-i18n](../../skills/fleex-i18n/SKILL.md) — её переводами;
[fleex-index](../../skills/fleex-index/SKILL.md) — скрипт навигации без зависимостей (map, outline,
show, find, refs), чтобы агенты читали только нужные строки;
[fleex-hygiene](../../skills/fleex-hygiene/SKILL.md) находит и запускает настроенные в репозитории
линтеры, форматтеры и проверки типов, чтобы каждое изменение сохраняло единый стиль. Существующая
конфигурация всегда в приоритете; если её нет, действуют настройки плагина по умолчанию из
`skills/fleex-hygiene/assets/`. Этот репозиторий тоже их использует: `ruff.toml` расширяет
конфигурацию Ruff по умолчанию, а `.vscode/settings.json` направляет mypy редактора на конфигурацию
mypy по умолчанию. Правила, однажды записанные в `AGENTS.md` репозитория, принадлежат его владельцу
и не синхронизируются с каталогом.

## Ссылки

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: память](https://docs.claude.com/en/docs/claude-code/memory)
- [Лучшие практики Claude Code](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Эффективная работа с контекстом](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Скиллы: [спецификация](https://agentskills.io/specification),
  [лучшие практики](https://agentskills.io/skill-creation/best-practices),
  [примеры Anthropic](https://github.com/anthropics/skills), [примеры OpenAI](https://github.com/openai/skills)
