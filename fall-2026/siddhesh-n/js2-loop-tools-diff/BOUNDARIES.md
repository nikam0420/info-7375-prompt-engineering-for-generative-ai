# Permission boundaries

Predictions were encoded before the first execution of the boundary suite. Each case uses either the actual request guard or the actual persistence function. Filesystem cases use a temporary directory. Network cases test the guard without sending requests.

| Case | Expected before run |
|---|---|
| GET to exact listing URL | Allow |
| POST to that URL | Deny |
| GET on example.com | Deny |
| HTTP to otherwise identical URL | Deny |
| HTTPS with user info | Deny |
| HTTPS with explicit alternate authority port | Deny |
| Allow-listed host with a different path | Deny |
| Fresh jobs/report.json | Allow |
| jobs/../escape.json | Deny |
| jobs-evil/escape.json | Deny |
| Absolute destination | Deny |
| File symlink to sibling directory | Deny and preserve target |
| Fresh raw file without approval | Deny and create nothing |
| Fresh raw file with approval | Allow |
| Overwrite even with approval | Deny and preserve existing bytes |
| Symlink in place of jobs directory | Deny and create nothing in target |

Evidence is in `evidence/baseline-tests.txt`. Both boundary methods passed there. For a personal rerun use the same test command in the README. The network guard runs before curl. Redirects are disabled by leaving curl's redirect-following option off and suppressing startup config. A real redirect response and hostile proxy are outside the tested cases.
