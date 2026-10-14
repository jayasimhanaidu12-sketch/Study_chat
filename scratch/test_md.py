import markdown_it

def format_markdown_for_email(text):
    try:
        md = markdown_it.MarkdownIt("commonmark")
        html = md.render(text)
        # Pre blocks
        html = html.replace("<pre>", '<pre style="background: #1e293b; color: #f8fafc; padding: 14px 18px; border-radius: 8px; overflow-x: auto; font-family: Consolas, \'Courier New\', monospace; font-size: 13px; line-height: 1.5; margin: 12px 0; border: 1px solid #334155;">')
        # Fix code inside pre vs inline code
        html = html.replace("<code>", '<code style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: Consolas, \'Courier New\', monospace; font-size: 12.5px;">')
        html = html.replace('border: 1px solid #334155;"><code style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: Consolas, \'Courier New\', monospace; font-size: 12.5px;">', 'border: 1px solid #334155;"><code style="color: #f8fafc; font-family: inherit; font-size: inherit; background: none; padding: 0;">')
        # Style headings
        html = html.replace("<h1>", '<h1 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 16px 0 8px;">')
        html = html.replace("<h2>", '<h2 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 14px 0 6px;">')
        html = html.replace("<h3>", '<h3 style="font-size: 15px; font-weight: 600; color: #0f172a; margin: 12px 0 6px;">')
        # Style lists
        html = html.replace("<ul>", '<ul style="margin: 8px 0 12px 20px; padding: 0; color: #1e293b; line-height: 1.6;">')
        html = html.replace("<ol>", '<ol style="margin: 8px 0 12px 20px; padding: 0; color: #1e293b; line-height: 1.6;">')
        html = html.replace("<li>", '<li style="margin-bottom: 4px;">')
        # Style paragraphs
        html = html.replace("<p>", '<p style="margin: 0 0 10px; line-height: 1.65; color: #1e293b;">')
        return html
    except Exception:
        import html
        escaped = html.escape(str(text))
        return "<p style='margin: 0 0 10px; line-height: 1.6; color: #1e293b;'>" + escaped.replace("\n\n", "</p><p style='margin: 0 0 10px; line-height: 1.6; color: #1e293b;'>").replace("\n", "<br>") + "</p>"

sample = """### Key Takeaways
Here are the main points:
- **Lists** are mutable and ordered.
- **Tuples** are immutable and faster.

```python
grades = [95, 88, 92]
grades.append(100)
print(grades)
```

Use `tuple` when coordinates don't change!
"""

print(format_markdown_for_email(sample))
