# Tool Selection Policy

Workers choose their own tools to accomplish goals, subject to role permissions.

Preferred order:
1. API or SDK.
2. CLI or deterministic programmatic tool.
3. Structured browser automation.
4. Visual computer use.

Use the highest layer that is reliable for the task. Visual computer use is a universal fallback, not the default.

For every consequential state-changing action:
- inspect current state;
- run policy check;
- execute;
- verify the external result;
- log the action and evidence.

Never infer success solely from a click, command submission or HTTP request being attempted.
