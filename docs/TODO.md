# TODO

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P3 — features

- [ ] Benchmark and refine fleex-index navigation #tokens #tests
  - Add a repeatable benchmark runner and fixtures under the repository's test and benchmark area.
    Compare native search and bounded reads, fleex-index commands, and the read hook separately.
  - Use representative tasks and repositories. Record correctness, input and output tokens, tool
    calls, and elapsed time. Include cases that bypass the hook and fallback parsing without ctags.
  - Use the measurements to decide which commands, activation guidance, and hook behavior to keep.
- [ ] Automate skill activation tests #tests
  - Check whether `claude plugin eval` can automate representative trigger and near-miss cases.
