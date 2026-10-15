# TODO

[English](../../TODO.md) · **Русский**

Состояния: `- [ ]` открыта, `- [-]` отклонена.
Теги: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P1 — безопасность

- [ ] Не выполнять Poetry при обнаружении проверок #security
  - Poetry 2 может ставить плагины из `pyproject.toml`
    ([checks.py:166-176](../../skills/fleex-hygiene/scripts/checks.py#L166-L176)).
- [ ] Экранировать `%` в генерируемых командах проверок на Windows #security
  - `shell_path()` оставляет `%VAR%` без экранирования; cmd раскроет его при выполнении команды
    ([checks.py:292-296](../../skills/fleex-hygiene/scripts/checks.py#L292-L296)).
- [ ] Закрепить версии дефолтных `uvx ruff` / `uvx mypy` #security
  - Без версии результат проверок меняется со временем.

- [ ] Включить на GitHub приватные сообщения об уязвимостях #security
  - [SECURITY.md](../../.github/SECURITY.md) отправляет сообщения на **Report a vulnerability**,
    но в репозитории это выключено
    (`gh api repos/Duby67/AgentFleex/private-vulnerability-reporting` возвращает
    `"enabled":false`). Settings → Code security → Private vulnerability reporting.

## P3 — возможности

- [ ] Создать скилл `fleex-repo`: аудит и шаблоны служебных файлов репозитория #feature
  - Комбинированный режим: аудит сообщает об отсутствии обязательных файлов как об ошибке, а
    рекомендованных — как о предложении; находки можно заносить в `TODO.md` через `fleex-todo`.
  - Решить состав списков. Предложение, обязательные: `README.md`, `LICENSE`, `.gitignore`,
    `.gitattributes`, `AGENTS.md`; рекомендованные: `.editorconfig`, `SECURITY.md`,
    `CONTRIBUTING.md`, `CODEOWNERS`, шаблоны issue и PR, Dependabot, соглашения CI (экшены по
    SHA, минимальные `permissions`).
  - Платформы: GitHub полностью; GitLab только для маленьких проектов с минимумом файлов.
  - Редкие задачи — в `references/` этого скилла, читаемые по необходимости, а не отдельные
    скиллы.
- [ ] Создать скилл `fleex-release` на основе механизма релизов этого репозитория #feature
  - Версия в манифестах, проверка pre-commit
    ([.pre-commit-config.yaml](../../.pre-commit-config.yaml)), `CHANGELOG.md` с
    `## [x.y.z](ссылка на тег)` и кратким списком, CI ставит тег и выпускает релиз только для
    новой версии ([ci.yml](../../.github/workflows/ci.yml)).
  - Решить для GitLab: релиз через CI или только теги.
- [ ] Добавить в `fleex-hygiene` настройки по умолчанию для Markdown, YAML, JSON и
  `.editorconfig` #feature
  - Сейчас они есть только для Ruff, mypy и ShellCheck
    ([checks.py:258-289](../../skills/fleex-hygiene/scripts/checks.py#L258-L289)).
- [ ] Расширить экономию чтения за пределы инструмента Read #tokens
  - Хук срабатывает только на `Read` ([hooks.json:6](../../hooks/hooks.json#L6)); `cat`,
    `grep -r` и длинный вывод Bash его обходят.
- [ ] Автоматизировать проверку срабатывания скиллов #tests
  - [fleex-skills](../../skills/fleex-skills/SKILL.md#L97) описывает около десяти ручных
    запросов на скилл; проверить, подходит ли `claude plugin eval`.
- [ ] Добавить в CI проверку бюджета всегда загружаемых токенов #tokens
  - `AGENTS.md` и описания всех скиллов; защищает от роста, а не текущий размер.
- [ ] Обновить README и описания в манифестах под новый охват #docs
  - Там всё ещё сказано, что плагин держит короткими `AGENTS.md`, скиллы и документацию
    ([README.md:5-6](../../README.md#L5-L6)).

## P4 — сопровождение

- [ ] Устранить дублирование логики `check.sh` и `check.ps1` или добавить тест на эквивалентность #chore
- [ ] Почистить `.gitignore` #chore
  - Опечатка `/.agetns/`.
- [ ] Решить, как переводить `.github/SECURITY.md` #docs
  - Документы для людей переводятся на ru, но `check.sh` и `fleex-i18n` принимают переводы только
    корневых файлов и страниц `docs/`; перенести файл в корень или расширить правило.
- [ ] Добавить регрессионные тесты команд Windows и проверок скиллов на чистом клоне #tests
  - Экранирование команд Windows, включая `%VAR%` в путях.
  - `check.sh` на чистом клоне.
