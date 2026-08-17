# Contributing

Thank you for contributing to KRecentTracker.

KRecentTracker is a KDE Plasma 6 widget, so contributions should aim to keep the project simple, maintainable, and consistent with the existing architecture and KDE conventions.

## Issues

Before starting a contribution, check the existing issues to make sure the problem or feature has not already been reported.

For larger changes, open an issue before implementing them. This allows the proposed solution to be discussed before significant development work is done.

Issues can be used for:

- Bug reports

- Feature requests

- Improvements

- Questions about the project

- Documentation problems

When reporting a bug, include:

- A clear description of the problem

- Steps to reproduce it

- Expected behaviour

- Actual behaviour

- Relevant error messages or logs

- KDE Plasma and operating system version, when relevant

For feature requests, explain the problem the feature would solve and, when possible, describe the proposed behaviour.

## Development

Fork the repository and create a branch for your change.

Use descriptive branch names following the project's existing convention:

```text
feature/<name>
fix/<name>
docs/<name>
refactor/<name>
```

Examples:

```text
feature/copy-path
feature/pin-widget
fix/recent-items-filter
docs/update-installation
```

Keep each branch focused on a single change. Avoid combining unrelated features, bug fixes, and refactoring in the same branch.

## Commits

Write clear and concise commit messages that describe the change.

Prefer small, logical commits instead of large commits containing several unrelated changes.

Examples:

```text
Add copy path action
Fix blacklisted path detection
Update installation instructions
Refactor recent item extraction
```

Avoid vague commit messages such as:

```text
Update
Fix stuff
Changes
More improvements
```

## Pull Requests

Pull requests should clearly explain what is being changed and why.

Before opening a pull request:

1. Make sure the branch contains only the relevant changes.

2. Test the widget locally.

3. Check that existing functionality still works.

4. Update the README or documentation when necessary.

5. Make sure no debug files, generated files, personal configuration, or credentials are included.

6. Rebase or update the branch if necessary before submitting the pull request.

Keep pull requests focused on one feature, bug fix, or improvement whenever possible.

A pull request description should include:

```text
## What changed

Brief description of the changes.

## Why

Explain the problem or motivation behind the change.

## Testing

Explain how the change was tested.
```

For UI-related changes, screenshots or short recordings are useful when they help demonstrate the result.

## Code and Project Guidelines

Try to follow the existing project structure and coding style.

When modifying the Python backend:

- Keep functions small and focused.

- Prefer clear names over overly compact implementations.

- Avoid unnecessary dependencies.

- Handle filesystem paths carefully.

- Consider different Linux distributions and filesystem layouts.

- Avoid hard-coding user-specific paths.

When modifying the Plasma widget:

- Keep the QML interface consistent with the existing design.

- Avoid unnecessary changes to unrelated UI components.

- Preserve existing functionality unless the change explicitly requires otherwise.

When adding a new feature, consider whether it should also be documented in the README.

## Testing

Test changes on a real KDE Plasma 6 environment whenever possible.

For changes involving filesystem access, recent items, or editor integration, test with different types of paths and applications when applicable.

At minimum, verify that:

- The widget starts correctly.

- Recent files and directories are displayed correctly.

- Existing actions continue to work.

- Invalid or inaccessible paths do not break the widget.

- The widget behaves correctly after restarting Plasma or the widget itself.

## Documentation

Update documentation when a change affects:

- Installation

- Configuration

- Supported applications

- User-facing features

- Dependencies

- Development or testing procedures

Keep the README focused on user-facing information. Detailed development information should be placed in the appropriate documentation files.

## Questions

If you are unsure about an implementation detail, open an issue or discuss the proposed change before submitting a large pull request.

Small fixes and improvements can be submitted directly when their purpose and implementation are clear.