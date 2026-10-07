# AgentFleex

Каркас репозитория для разработки с агентами (Codex, Claude Code). Не привязан к языку проекта и
модели веток: хранит только подключение правил и скилов и то, что держит контекст агента маленьким.
Сам репозиторий ведётся в одной ветке `main`.

## Подключение

| Путь | Назначение |
| --- | --- |
| [AGENTS.md](./AGENTS.md) | Единственный файл правил; Codex читает его сам |
| [CLAUDE.md](./CLAUDE.md) | Одна строка `@AGENTS.md`: Claude Code импортирует тот же файл |
| `Skills/` | Единственный источник скилов |
| `.agents/skills`, `.claude/skills` | Относительные симлинки на `Skills/` для Codex и Claude Code |

Оба клиента сами находят скилы по полю `description`, поэтому таблица маршрутизации в `AGENTS.md`
не нужна. В Windows симлинки требуют `git config core.symlinks true` и режим разработчика.

## Экономия токенов

Главная статья расхода — файлы, которые агент читает часто, прежде всего `AGENTS.md`: он уходит в
каждый запрос к модели. Поэтому:

- в `AGENTS.md` только то, что нужно каждой задаче и что агент не выведет сам: что за проект,
  жёсткие инварианты, ссылки на владельцев тем;
- удаляется всё, что следует из самого файла или известно агенту. Пример бесполезной строки:
  «Файл предназначен только для агентов, используй только английский язык» — файл и так читают и
  заполняют агенты;
- подробности отдельных задач живут в скилах: в каждый запрос попадает только их `description`,
  тело читается по необходимости;
- каждый факт хранится в одном месте, остальные ссылаются на него.

Подробные правила: [kit-agent-rules](./Skills/kit-agent-rules/SKILL.md) (AGENTS.md),
[kit-skill-authoring](./Skills/kit-skill-authoring/SKILL.md) (создание скилов, ссылки на best
practice), [kit-docs](./Skills/kit-docs/SKILL.md) (документация для людей).

## Новый проект из каркаса

1. Создай репозиторий из AgentFleex.
2. Перепиши раздел Project в `AGENTS.md`, добавь инварианты своей области (например, модель веток)
   и ссылки на владельцев тем.
3. Проектные скилы называй `<project>-<job>` и клади в `Skills/`.
4. Проверки кода, CI и hooks добавляй под язык и процесс проекта.

## Материалы

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: memory](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Скилы: [спецификация](https://agentskills.io/specification),
  [best practices](https://agentskills.io/skill-creation/best-practices),
  [примеры Anthropic](https://github.com/anthropics/skills), [примеры OpenAI](https://github.com/openai/skills)
