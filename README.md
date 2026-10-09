# AgentFleex

Плагин для Claude Code и Codex: скилы репозитория и документацию так, чтобы они были короткими и согласованными.

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

Изменения плагина подхватываются в новой сессии.

После установки достаточно попросить агента, например, «перепиши AGENTS.md» или «создай скил для
деплоя»: нужный скил подключится по своему `description`. Если в репозитории нет `AGENTS.md`,
агент начнёт с [шаблона](./skills/fleex-agents-md/assets/AGENTS.template.md).

## Что плагин настраивает в репозитории

| Путь | Назначение |
| --- | --- |
| `AGENTS.md` | Единственный файл правил; Codex читает его сам |
| `CLAUDE.md` | Одна строка `@AGENTS.md`: Claude Code импортирует тот же файл |
| `.agents/skills/` | Единственный источник скилов проекта; Codex читает его сам |
| `.claude/skills` | Относительный симлинк на `.agents/skills/` для Claude Code |

Общие скилы `fleex-*` приходят из плагина и в репозиторий не копируются. Оба клиента сами находят
скилы по полю `description`, поэтому таблица маршрутизации в `AGENTS.md` не нужна.

## Устройство этого репозитория

Корень репозитория — корень плагина. Скилы лежат в `skills/`; `.agents/skills` и `.claude/skills` —
симлинки на него, чтобы агенты пользовались ими и при работе над самим плагином. Манифесты:
`.claude-plugin/` и `.codex-plugin/` (плагин), `.claude-plugin/marketplace.json` и
`.agents/plugins/marketplace.json` (маркетплейсы).

## Экономия токенов

Главная статья расхода — файлы, которые агент читает часто, прежде всего `AGENTS.md`: он уходит в
каждый запрос к модели. Поэтому:

- в `AGENTS.md` только то, что нужно каждой задаче и что агент не выведет сам: что за проект,
  жёсткие инварианты, ссылки на владельцев;
- удаляется всё, что следует из самого файла или известно агенту;
- подробности отдельных задач живут в скилах: в каждый запрос попадает только их `description`,
  тело читается по необходимости;
- каждый факт хранится в одном месте, остальные ссылаются на него.

Подробные правила: [fleex-agents-md](./skills/fleex-agents-md/SKILL.md) (AGENTS.md),
[fleex-skills](./skills/fleex-skills/SKILL.md) (создание скилов, ссылки на best
practice), [fleex-docs](./skills/fleex-docs/SKILL.md) (документация для людей).

## Материалы

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: memory](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Скилы: [спецификация](https://agentskills.io/specification),
  [best practices](https://agentskills.io/skill-creation/best-practices),
  [примеры Anthropic](https://github.com/anthropics/skills), [примеры OpenAI](https://github.com/openai/skills)
