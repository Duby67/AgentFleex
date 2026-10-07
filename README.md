# AgentFleex

Каркас репозитория для разработки с агентами. Хранит только правила и скилы.

## Подключение

| Путь | Назначение |
| --- | --- |
| [AGENTS.md](./AGENTS.md) | Единственный файл правил; Codex читает его сам |
| [CLAUDE.md](./CLAUDE.md) | Одна строка `@AGENTS.md`: Claude Code импортирует тот же файл |
| `.agents/skills/` | Единственный источник скилов; Codex читает его сам |
| `.claude/skills` | Относительный симлинк на `.agents/skills/` для Claude Code |

Оба клиента сами находят скилы по полю `description`, поэтому таблица маршрутизации в `AGENTS.md`
не нужна.

## Экономия токенов

Главная статья расхода — файлы, которые агент читает часто, прежде всего `AGENTS.md`: он уходит в
каждый запрос к модели. Поэтому:

- в `AGENTS.md` только то, что нужно каждой задаче и что агент не выведет сам: что за проект,
  жёсткие инварианты, ссылки на владельцев;
- удаляется всё, что следует из самого файла или известно агенту;
- подробности отдельных задач живут в скилах: в каждый запрос попадает только их `description`,
  тело читается по необходимости;
- каждый факт хранится в одном месте, остальные ссылаются на него.

Подробные правила: [fleex-agents-md](./.agents/skills/fleex-agents-md/SKILL.md) (AGENTS.md),
[fleex-skills](./.agents/skills/fleex-skills/SKILL.md) (создание скилов, ссылки на best
practice), [fleex-docs](./.agents/skills/fleex-docs/SKILL.md) (документация для людей).

## Материалы

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: memory](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Скилы: [спецификация](https://agentskills.io/specification),
  [best practices](https://agentskills.io/skill-creation/best-practices),
  [примеры Anthropic](https://github.com/anthropics/skills), [примеры OpenAI](https://github.com/openai/skills)
