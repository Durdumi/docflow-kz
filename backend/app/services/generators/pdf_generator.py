from datetime import datetime
from jinja2 import Environment, BaseLoader


REPORT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
  h1 { color: #1677ff; border-bottom: 2px solid #1677ff; padding-bottom: 10px; }
  .meta { color: #666; font-size: 12px; margin-bottom: 30px; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; }
  th { background: #1677ff; color: white; padding: 10px; text-align: left; }
  td { padding: 8px 10px; border-bottom: 1px solid #eee; }
  tr:nth-child(even) { background: #f9f9f9; }
  .footer { margin-top: 40px; font-size: 11px; color: #999; text-align: center; }
</style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="meta">
    Тип: {{ type }} |
    Период: {{ period_from }} — {{ period_to }} |
    Сформирован: {{ generated_at }}
  </div>

  {% if data %}
  <table>
    <thead>
      <tr>{% for col in columns %}<th>{{ col }}</th>{% endfor %}</tr>
    </thead>
    <tbody>
      {% for row in data %}
      <tr>{% for col in columns %}<td>{{ row.get(col, '') }}</td>{% endfor %}</tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>Данные для отчёта отсутствуют.</p>
  {% endif %}

  <div class="footer">DocFlow KZ — автоматически сформированный отчёт</div>
</body>
</html>
"""


def generate_pdf(report_data: dict) -> bytes:
    from weasyprint import HTML
    env = Environment(loader=BaseLoader())
    template = env.from_string(REPORT_HTML_TEMPLATE)
    html_content = template.render(
        title=report_data.get("title", "Отчёт"),
        type=report_data.get("type", ""),
        period_from=report_data.get("period_from", "—"),
        period_to=report_data.get("period_to", "—"),
        generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
        columns=report_data.get("columns", []),
        data=report_data.get("data", []),
    )
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
