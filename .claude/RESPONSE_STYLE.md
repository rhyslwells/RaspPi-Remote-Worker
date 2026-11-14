# Response Style

## When proposing changes

- Explain reasoning briefly and concretely
- Reference code by file and line
- Say what else is affected: sheet layout, live Config rows, the Pi service, `uv.lock`
- Prefer concrete implementation over abstract discussion

## Implementation principles

- **Do not over-engineer.** This is a small personal tool; no frameworks, plugin systems or config layers beyond what the task needs
- **Smallest change in the right place.** Script first, `ControlPanel` second, runner last
- **Validate at boundaries:** sheet parameters and network results, not internal state
- **Prefer deletion** of dead code over leaving stubs
- **Follow repository patterns** over generic best practice

## Safety

- Treat `credentials.json`, `.raspi-config` and the Pi as private and live. Do not read, print or contact them without being asked
- Flag anything that would alter the live sheet or the running service before doing it
- Be explicit about what was actually run versus only reasoned about; there is no test suite, so say how a change was verified

## The repository-first rule

When repository code differs from general best practice (for example `oauth2client`, hard-coded column indexes, in-process script execution):

1. Follow the existing pattern
2. Mention the alternative separately if it is materially better
3. Do not rewrite it as a side effect of another task
