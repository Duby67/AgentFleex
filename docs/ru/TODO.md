# TODO

[English](../TODO.md) · **Русский**

Состояния: `- [ ]` открыта, `- [-]` отклонена.
Теги: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P3 — возможности

- [ ] Расширить экономию чтения за пределы инструмента Read #tokens
  - Хук срабатывает только на `Read` ([hooks.json:6](../../hooks/hooks.json#L6)); `cat`,
    `grep -r` и длинный вывод Bash его обходят.
- [ ] Автоматизировать проверку срабатывания скиллов #tests
  - [fleex-skills](../../skills/fleex-skills/SKILL.md#L98) описывает около десяти ручных
    запросов на скилл; проверить, подходит ли `claude plugin eval`.
