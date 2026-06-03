## Summary

<!-- What does this PR do? 1-3 bullet points. -->

-
-

## Type of change

- [ ] Bug fix
- [ ] New feature / agent
- [ ] Refactor
- [ ] Documentation
- [ ] Tests

## Checklist

- [ ] `python -m pytest` passes (0 failures)
- [ ] `python manage.py check` reports 0 issues
- [ ] No secrets committed
- [ ] AI calls go through `agents/utils.agent_chat()` only — no direct provider calls
- [ ] FKs use `'bredbound.BusinessInstance'` (not `'hub.BusinessInstance'`)
- [ ] New ViewSets have `queryset = Model.objects.none()`
- [ ] New agent has a `README.md` in its folder

## Test plan

<!-- How did you verify this works? -->

## Related issues

<!-- Closes #XXX -->
