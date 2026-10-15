# Changelog

[English](../../CHANGELOG.md) · **Русский**

## Unreleased

- Заметки о релизе теперь описывают решённые проблемы и итоговое поведение без учёта операций
  со списком задач.
- Добавлен скилл `fleex-vscode`: рекомендации расширений и настройки VS Code по наборам,
  сливаемые в игнорируемую `.vscode/` проекта; он может посоветовать другие расширения, не
  предлагает удалять установленные и по запросу синхронизирует установленные расширения с наборами,
  удаляя лишние отдельным шагом после подтверждения.
- `.vscode/settings.json` больше не отслеживается; `.vscode/` в игноре.
- В каталог правил `AGENTS.md` добавлена модель веток: `develop` для работы, `staging` для
  тестирования, `main` для релизов.
- Разработка перенесена в `develop`: пуш в неё запускает тесты и pre-commit, pull request в
  `main` добавляет проверку релиза, а пуш в `main` выпускает релиз.
- Ruff, mypy, ShellCheck и проверки файлов работают как хуки pre-commit; `fleex-hygiene` делает
  pre-commit средством гигиены каждого репозитория и проверяет перечисленный в нём инструмент только
  через него.
- Каждое слияние в `main` — релиз: CI отклоняет версию не выше последнего тега, а
  `.github/scripts/release.py` содержит проверки версии и changelog для CI и pre-commit.

## [0.3.2](https://github.com/Duby67/AgentFleex/releases/tag/0.3.2)

- Добавлен скилл `fleex-todo` для бэклога `TODO.md`.
- Добавлены `CHANGELOG.md`, `.github/SECURITY.md` и `.gitattributes`.
- `VERSION` и `version.py` заменены проверкой версий манифестов в pre-commit.
- CI выпускает релиз для версии манифеста, у которой ещё нет релиза на GitHub, с заметками из
  `CHANGELOG.md`; изменения ждут релиза в `## Unreleased`, а переводы свёрнуты под названиями
  языков.
- Исправлена проверка скиллов, падавшая на чистом клоне из-за закоммиченных метаданных плагина в
  `.agents/` и на macOS, где bash 3.2 принимал `./skills` за путь скиллов агента.

## [0.3.1](https://github.com/Duby67/AgentFleex/releases/tag/0.3.1)

- Добавлены корневой `VERSION` и скрипт синхронизации версий манифестов.
- Скиллы проекта перенесены в корневой `skills/`, для агентов — симлинки.

## [0.3.0](https://github.com/Duby67/AgentFleex/releases/tag/0.3.0)

- Добавлен скилл `fleex-i18n`.
- Добавлены хуки: проверки стиля перед остановкой агента и outline для длинных файлов.
- Добавлены CI на Linux, macOS и Windows и Dependabot.

## [0.2.0](https://github.com/Duby67/AgentFleex/releases/tag/0.2.0)

- Добавлены скиллы `fleex-index` и `fleex-hygiene`.
- `fleex-agents-md` переименован в `fleex-agents`.

## [0.1.0](https://github.com/Duby67/AgentFleex/releases/tag/0.1.0)

- Создан плагин со скиллами `fleex-agents-md`, `fleex-docs` и `fleex-skills`.
