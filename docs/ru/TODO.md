# TODO

[English](../../TODO.md) · **Русский**

Состояния: `- [ ]` открыта, `- [-]` отклонена.
Теги: `#bug`, `#security`, `#reliability`, `#ci`, `#tests`, `#chore`.

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

## P3 — сопровождение

- [ ] Устранить дублирование логики `check.sh` и `check.ps1` или добавить тест на эквивалентность #chore
- [ ] Почистить `.gitignore` #chore
  - Опечатка `/.agetns/`.
  - `.vscode/` игнорируется при tracked `.vscode/settings.json`.
- [ ] Добавить тесты, которые поймали бы задачи P0 #tests
  - Имена с пробелами и юникодом в stop-хуке.
  - Экранирование команд на Windows.
  - `check.sh` на чистом клоне.
