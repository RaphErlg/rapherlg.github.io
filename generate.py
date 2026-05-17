import os
import re
from datetime import date

COURS_DIR = "cours"
ICON = "data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📓</text></svg>"
MONTHS = ["janvier","février","mars","avril","mai","juin",
          "juillet","août","septembre","octobre","novembre","décembre"]

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def extract_tag(html, tag):
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None

def extract_meta(html, name):
    m = re.search(rf'<meta\s+name="{name}"\s+content="(.*?)"', html, re.IGNORECASE)
    return m.group(1).strip() if m else None

def format_date(raw):
    """'17-05-2026 03:23 PM' → 'mai 2026'"""
    if not raw:
        return ""
    parts = raw.split(" ")[0].split("-")
    if len(parts) == 3:
        return f"{MONTHS[int(parts[1]) - 1]} {parts[2]}"
    return raw

def today_fr():
    d = date.today()
    return f"{MONTHS[d.month - 1]} {d.year}"

def get_course_title(course_path):
    """Read title from existing index.html, stripping the ' — Synthèses' suffix."""
    index_path = os.path.join(course_path, "index.html")
    if os.path.exists(index_path):
        title = extract_tag(read_file(index_path), "title")
        if title:
            return title.replace(" — Synthèses", "").strip()
    # Fallback: format folder name
    return os.path.basename(course_path).replace("-", " ").capitalize()

def get_synthesis_info(filepath):
    """Return (title, date) for a Notesnook HTML file."""
    html = read_file(filepath)
    title = extract_tag(html, "title") or os.path.basename(filepath).replace(".html", "")
    title = title[0].upper() + title[1:]  # capitalize first letter
    raw_date = extract_meta(html, "updated-at")
    return title, format_date(raw_date)

def generate_synthesis_item(filename, title, syn_date):
    return f"""\
      <li class="synthesis-item">
        <a href="{filename}">
          <svg class="synthesis-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M3 2h7l3 3v9H3V2z"/>
            <path d="M10 2v3h3"/>
          </svg>
          <span class="synthesis-title">{title}</span>
          <span class="synthesis-date">{syn_date}</span>
        </a>
      </li>"""

def generate_course_index(course_title, syntheses):
    items = "\n".join(generate_synthesis_item(*s) for s in syntheses)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{course_title} — Synthèses</title>
  <link rel="stylesheet" href="../../style.css">
  <link rel="icon" href="{ICON}">
</head>
<body>
  <div class="container">

    <nav class="breadcrumb">
      <a href="../../">Accueil</a>
      <span class="breadcrumb-sep">/</span>
      <span>{course_title}</span>
    </nav>

    <header class="site-header">
      <h1 class="site-title">{course_title}</h1>
      <p class="site-tagline">Synthèses du cours de {course_title.lower()}.</p>
    </header>

    <p class="section-label">Synthèses</p>

    <ul class="synthesis-list">

{items}

    </ul>

    <footer class="site-footer">
      <span><a href="../../">← Retour à l'accueil</a></span>
      <span>Mis à jour : {today_fr()}</span>
    </footer>

  </div>
</body>
</html>
"""

def generate_course_item(number, course_name, course_title, count):
    label = "1 synthèse" if count == 1 else f"{count} synthèses"
    return f"""\
      <li class="course-item">
        <a class="course-link" href="cours/{course_name}/">
          <span class="course-number">{number:02d}</span>
          <span class="course-name">{course_title}<span class="course-arrow">→</span></span>
          <span class="course-meta">{label}</span>
        </a>
      </li>"""

def generate_home(courses):
    items = "\n".join(generate_course_item(i + 1, *c) for i, c in enumerate(courses))
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Synthèses — Mes notes de cours</title>
  <meta name="description" content="Synthèses de cours partagées avec mes camarades.">
  <link rel="stylesheet" href="style.css">
  <link rel="icon" href="{ICON}">
</head>
<body>
  <div class="container">

    <header class="site-header">
      <h1 class="site-title">Mes <em>synthèses</em></h1>
      <p class="site-tagline">Notes de cours organisées, exportées depuis Notesnook. Servez-vous, mais relisez quand même votre cours.</p>
    </header>

    <p class="section-label">Cours</p>

    <ul class="course-list">

{items}

    </ul>

    <footer class="site-footer">
      <span>Dernière mise à jour : {today_fr()}</span>
      <span><a href="https://github.com/" target="_blank" rel="noopener">Source sur GitHub</a></span>
    </footer>

  </div>
</body>
</html>
"""

# --- Main ---

courses = []

for course_name in sorted(os.listdir(COURS_DIR)):
    course_path = os.path.join(COURS_DIR, course_name)
    if not os.path.isdir(course_path):
        continue

    course_title = get_course_title(course_path)

    syntheses = []
    for filename in sorted(os.listdir(course_path)):
        if not filename.endswith(".html") or filename == "index.html":
            continue
        filepath = os.path.join(course_path, filename)
        title, syn_date = get_synthesis_info(filepath)
        syntheses.append((filename, title, syn_date))
        print(f"  [{course_name}] {filename} -> \"{title}\" ({syn_date})")

    write_file(os.path.join(course_path, "index.html"), generate_course_index(course_title, syntheses))
    print(f"  OK cours/{course_name}/index.html genere ({len(syntheses)} synthese(s))")

    courses.append((course_name, course_title, len(syntheses)))

write_file("index.html", generate_home(courses))
print(f"\nOK index.html genere ({len(courses)} cours)")
