# TODO

[English](../../TODO.md) · **Русский**

Состояния: `- [ ]` открыта, `- [-]` отклонена.
Теги: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P0 — блокирует релиз

- [ ] Починить красный CI на `main`: `check.sh` требует симлинк `.agents/skills` #ci #bug
  - `.agents/` есть в каждом клоне из-за tracked `.agents/plugins/marketplace.json`, а `.gitignore`
    исключает `/.agents/*`; проверка в [check.sh:61-64](../../skills/fleex-skills/scripts/check.sh#L61-L64)
    и `check.ps1` падает на чистом клоне.
  - Решить: коммитить симлинк или ослабить проверку. Релиз 0.3.2 из-за этого не вышел.
- [ ] Stop-хук молча теряет файлы с не-ASCII именами #bug
  - `changed()` вызывает `git diff`/`ls-files` без `-z`, git экранирует имя, `is_file()` ложен
    ([agentfleex.py:92-99](../../hooks/agentfleex.py#L92-L99)). В `index.py` `-z` уже используется.

## P1 — безопасность

- [ ] Привязать согласие к содержимому конфигов, а не только к набору инструментов #security
  - Изменённый после `pull` `eslint.config.js` или плагин mypy выполнится без вопроса
    ([agentfleex.py:168-169](../../hooks/agentfleex.py#L168-L169)).
- [ ] Не давать агенту записывать согласие без пользователя #security
  - Сейчас хук выдаёт агенту готовую команду `consent yes`; гарантия держится на послушании агента.
- [ ] Не запускать `poetry env info` до согласия #security
  - Poetry 2 может ставить плагины из `pyproject.toml`
    ([checks.py:166-176](../../skills/fleex-hygiene/scripts/checks.py#L166-L176)).
- [ ] Убрать fallback данных в общий `/tmp/agentfleex` #security
  - Без `CLAUDE_PLUGIN_DATA`/`PLUGIN_DATA` другой пользователь машины может подложить
    `consent.json` ([agentfleex.py:69-71](../../hooks/agentfleex.py#L69-L71)).
- [ ] Экранировать `%` в именах файлов на Windows #security
  - При `shell=True` cmd раскроет `%VAR%` из имени файла
    ([agentfleex.py:112](../../hooks/agentfleex.py#L112)).
- [ ] Закрепить версии дефолтных `uvx ruff` / `uvx mypy` #security
  - Без версии результат проверок меняется со временем.

- [ ] Включить на GitHub приватные сообщения об уязвимостях #security
  - [SECURITY.md](../../.github/SECURITY.md) отправляет сообщения на **Report a vulnerability**,
    но в репозитории это выключено
    (`gh api repos/Duby67/AgentFleex/private-vulnerability-reporting` возвращает
    `"enabled":false`). Settings → Code security → Private vulnerability reporting.

## P2 — надёжность

- [ ] Согласовать таймауты: 120 с на команду при 600 с на весь stop-хук #reliability
  - При многих инструментах хук убьют без внятной ошибки.
- [ ] Обработать невалидный `package.json` в stop-хуке #reliability #bug
  - `checks.rows` бросает `SystemExit`, хук падает с кодом 1, проверки не идут
    ([checks.py:311](../../skills/fleex-hygiene/scripts/checks.py#L311)).
- [ ] Не читать файл целиком в память в Read-хуке для подсчёта строк #reliability
  - [agentfleex.py:263](../../hooks/agentfleex.py#L263).
- [ ] Защитить JSON состояния сессии от параллельной записи #reliability
  - Параллельные Read-хуки теряют записи, outline показывается повторно.

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
- [ ] Добавить в `fleex-skills` правило: редкая задача уходит в `references/` смежного скилла
  #feature
  - Держит число всегда загружаемых описаний малым; текущие ~700 токенов на 7 описаний приняты.
- [ ] Добавить в `fleex-hygiene` настройки по умолчанию для Markdown, YAML, JSON и
  `.editorconfig` #feature
  - Сейчас они есть только для Ruff, mypy и ShellCheck
    ([checks.py:258-289](../../skills/fleex-hygiene/scripts/checks.py#L258-L289)).
- [ ] Расширить экономию чтения за пределы инструмента Read #tokens
  - Хук срабатывает только на `Read` ([hooks.json:17](../../hooks/hooks.json#L17)); `cat`,
    `grep -r` и длинный вывод Bash его обходят.
- [ ] Сократить сообщения stop-хука #tokens
  - Каждая упавшая проверка возвращает до 4000 символов вывода
    ([agentfleex.py:50](../../hooks/agentfleex.py#L50)).
- [ ] Автоматизировать проверку срабатывания скиллов #tests
  - [fleex-skills](../../skills/fleex-skills/SKILL.md#L94) описывает около десяти ручных
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
  - `.vscode/` игнорируется при tracked `.vscode/settings.json`.
- [ ] Решить, как переводить `.github/SECURITY.md` #docs
  - Документы для людей переводятся на ru, но `check.sh` и `fleex-i18n` принимают переводы только
    корневых файлов и страниц `docs/`; перенести файл в корень или расширить правило.
- [ ] Добавить тесты, которые поймали бы задачи P0 #tests
  - Имена с пробелами и юникодом в stop-хуке.
  - Экранирование команд на Windows.
  - `check.sh` на чистом клоне.
