# AgentFleex

[English](../../README.md) · **Русский**

Плагин для Claude Code и Codex, который настраивает репозитории единообразно: правила агентов,
скиллы, документация и переводы, проверки стиля, файлы и настройки GitHub, релизы, а также дешёвая
навигация по коду для агента.

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

## Скиллы

Оба клиента находят скилл по его `description`, который попадает в каждый запрос; тело и
справочники читаются только при использовании скилла. Скиллы с явным вызовом запускаются только как
`$<skill>` (Codex) или `/<skill>` (Claude Code), поэтому их описания не занимают контекст.

| Скилл | Чем владеет | Вызов |
| --- | --- | --- |
| [fleex-agents](../../skills/fleex-agents/SKILL.md) | `AGENTS.md`, `.claude/CLAUDE.md` и [каталог общих правил](../../skills/fleex-agents/references/rules.md) | автоматически |
| [fleex-skills](../../skills/fleex-skills/SKILL.md) | Скиллы проекта, их подключение и ссылки на лучшие практики | автоматически |
| [fleex-docs](../../skills/fleex-docs/SKILL.md) | Документация для людей, [переводы](../../skills/fleex-docs/references/i18n.md) и [бэклог `TODO.md`](../../skills/fleex-docs/references/todo.md) | автоматически; переводы по запросу |
| [fleex-hygiene](../../skills/fleex-hygiene/SKILL.md) | Линтеры, форматтеры, проверки типов, pre-commit, uv, `.editorconfig` | автоматически, по запросу или перед PR |
| [fleex-index](../../skills/fleex-index/SKILL.md) | Скрипт навигации без зависимостей: map, outline, show, find, refs | автоматически |
| [fleex-repo](../../skills/fleex-repo/SKILL.md) | Аудит и настройка файлов и параметров Git и GitHub, механизм релизов | явно |
| [fleex-vscode](../../skills/fleex-vscode/SKILL.md) | Игнорируемая `.vscode/` проекта | явно |

Проверки и переводы никогда не запускаются после каждой правки или ответа; контрольными точками
остаются pre-commit и CI. Существующая конфигурация всегда приоритетнее настроек плагина по
умолчанию.

## Устройство репозитория

| Путь | Назначение |
| --- | --- |
| `AGENTS.md` | Единственный файл правил и единственная точка входа; Codex читает его сам |
| `.claude/CLAUDE.md` | Только для Claude Code: одна строка `@../AGENTS.md`, которая импортирует тот же файл |
| `skills/` | Скиллы проекта, если они есть; `.agents/skills` и `.claude/skills` — относительные симлинки на него, только для используемых агентов |
| `README.md`, `LICENSE`, `.gitignore`, `.gitattributes`, `.editorconfig`, `.pre-commit-config.yaml` | Единственные файлы в корне, кроме манифестов пакетов |
| `docs/` | Документация для людей: `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `TODO.md` и переводы в `docs/<code>/` |
| `.github/` | Формы issue, шаблон PR, Dependabot, CI и скрипт релиза |

Каталоги агентов (`.claude/`, `.cursor/`) создаются только для используемых агентов и игнорируются
Git; нужные метаданные распространения плагина отслеживаются через явное исключение. Общие скиллы
`fleex-*` приходят из плагина и не копируются в репозиторий.

Файлы для агентов пишутся на английском. Документация для людей пишется на английском и
переводится на языки, перечисленные в `AGENTS.md` (`translated to: ru`): `README.md` как
`docs/ru/README.md`, страница `docs/` по тому же пути внутри `docs/ru/`, у каждого файла набора
одна строка переключателя языков под заголовком. Во время разработки переводы могут отставать с
пометкой об этом и синхронизируются по запросу, в том числе перед PR.

## Ветки и релизы

`develop`, ветка по умолчанию, — рабочая ветка, от которой начинаются и в которую направляются все
ветки и PR, а `main` хранит релизы. Pull request'ы в `develop` сливаются через squash, а `develop`
сливается в `main` обычным merge-коммитом. Репозиторий с деплоем на тестовый сервер добавляет
`staging`: `develop` сливается в неё для деплоя, её ошибки исправляются в `develop`, и только
`staging` сливается в `main`. Ветки задач называются `<type>/<description>`. Репозиторий сохраняет
свои имена веток, если их называет пользователь.

Каждое слияние в `main` — релиз с новой версией по семантическому версионированию: CI проверяет
версию и changelog, ставит тег и публикует релиз GitHub с заметками из `docs/CHANGELOG.md`.

## Хуки

Плагин поставляет только хук `PreToolUse` для инструмента `Read` в Claude Code. Первое чтение
целиком файла длиннее 400 строк отклоняется с outline из fleex-index; повторное чтение разрешает
весь файл. Диапазоны, короткие и бинарные файлы пропускаются. Строки считаются блоками ограниченного
размера; атомарные маркеры предотвращают повторные отказы при параллельных чтениях.

Хукам нужен `python3` или `python` в `PATH`, а также `CLAUDE_PLUGIN_DATA` или `PLUGIN_DATA`,
указывающий на приватный каталог данных плагина. Общий временный каталог не используется. В Codex
нужно одобрить хуки в `/hooks`, но этот matcher не перехватывает команды оболочки и другие
инструменты чтения.

## VS Code

Вызовите `$fleex-vscode`, чтобы подготовить рабочее пространство VS Code под задачу: скилл выбирает
наборы из `skills/fleex-vscode/assets/` по задаче и файлам проекта и сливает их рекомендации
расширений и настройки в `.vscode/` проекта, которая остаётся в игноре Git. На новой машине весь
набор ставится разом: `Extensions: Show Recommended Extensions`, затем кнопка Install Workspace
Recommended Extensions. Агент может посоветовать другие расширения под задачу, но не предлагает
удалять ваши и сам ничего не устанавливает. Только если вы попросите синхронизировать установленные
расширения с рекомендациями, он ставит недостающие, а затем отдельным шагом, после вашего
подтверждения, удаляет лишние.

| Набор | Когда |
| --- | --- |
| `default` | Всегда: редактор, Git, Markdown, YAML, TOML, EditorConfig |
| `personal` | Всегда: тема и раскладка интерфейса |
| `python` | Проекты на Python |
| `cpp` | Проекты на C и C++ |
| `infrastructure` | Docker, CI, shell-скрипты, удалённые хосты |
| `tools` | REST, draw.io, hex, CSV, XML, Inno Setup, npm |

Горячие клавиши и настройки уровня приложения или машины работают только в профиле пользователя;
держите их там, например через Settings Sync.

## Экономия токенов

Главная стоимость — то, что попадает в каждый запрос: `AGENTS.md` и описания скиллов. В
`AGENTS.md` только то, что нужно каждой задаче и что агент не выведет сам; редкие задачи живут в
справочниках скиллов или в скиллах с явным вызовом; каждый факт живёт в одном месте, всё остальное
ссылается на него. Правила, однажды записанные в `AGENTS.md` репозитория, принадлежат его владельцу
и не синхронизируются с каталогом.

## Участие в разработке

Окружение, проверки, ветки, pull request и релизы: [CONTRIBUTING.md](CONTRIBUTING.md). Сообщения
об уязвимостях: [SECURITY.md](SECURITY.md). Лицензия — [MIT](../../LICENSE).

## Ссылки

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: память](https://docs.claude.com/en/docs/claude-code/memory)
- [Лучшие практики Claude Code](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Эффективная работа с контекстом](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Скиллы: [спецификация](https://agentskills.io/specification),
  [лучшие практики](https://agentskills.io/skill-creation/best-practices),
  [примеры Anthropic](https://github.com/anthropics/skills), [примеры OpenAI](https://github.com/openai/skills)
