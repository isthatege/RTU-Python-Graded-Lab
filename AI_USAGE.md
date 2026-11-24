# AI Usage Disclosure

<!--
Fill in this file before you submit. Submissions without it are not graded.
If you used no AI tools, delete everything below and write only:
No AI tools were used.
-->

## Tools used

- Tool and version (e.g. ChatGPT GPT-5, Claude, GitHub Copilot):
- Claude Sonnet 5.5

## Conversation links

- Link 1:https://claude.ai/share/d44c6a5f-b69d-4fdc-b2b7-8aeb8de7ea53


## What I used them for
- Explaining regex patterns for ASCII-only string validation
- Understanding datetime format validation edge cases in Python
- Learning how to check if float values are finite (not nan/inf)

- e.g. explaining argparse, debugging the date validation, generating test data

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- |------------------| --- |
| validator.py | Flight ID validation pattern | Explained - learned about re.fullmatch() and explicit ASCII character classes vs \w |
| validator.py | Datetime format validation | Explained - confirmed need for both regex format check AND strptime parsing to catch all edge cases |
| validator.py | Price finiteness check | Explained - learned about math.isfinite() for detecting nan/inf values from CSV input |

## Key prompts

1. "How do I validate that a string matches exactly 2-8 ASCII alphanumeric characters in Python? I need to reject non-ASCII letters like 'Ā' or 'é'."
2. "In Python, what's the difference between using datetime.strptime() alone versus combining it with regex format checking for date validation?"
3. "How do I check if a float value is finite (not nan or inf) in Python? I'm validating prices from CSV input."

## What I changed or verified myself
- Tried both the regex way and isascii() + isalnum() for flight IDs to see which worked better
- Made sure re.fullmatch() actually rejects strings with trailing newlines (the ^...$ approach didn't)
- Ran our test suite to confirm the combined regex + strptime approach catches all bad datetime formats
- Tested edge cases manually like leap years, dates without zero-padding, and Unicode digits
- Checked that price validation handles nan, inf, -inf, and really large/small numbers correctly with math.isfinite()