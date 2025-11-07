from datetime import datetime
from datetime import datetime as _dt

from profcalc.cli.tools import bounds as b
from profcalc.common.bmap_io import format_date_for_bmap

# simulate raw date inputs and entries
raws = ["2024-10-26", "26OCT2024", "", "04/01/2025", None]
entries = []
for raw in raws:
    if raw:
        date_norm = format_date_for_bmap(raw) or str(raw)
    else:
        date_norm = ""
    # date_key parse
    date_key = None
    if raw:
        try:
            date_key = datetime.fromisoformat(str(raw))
        except Exception:
            try:
                date_key = datetime.strptime(str(raw).upper(), "%d%b%Y")
            except Exception:
                try:
                    date_key = datetime.strptime(str(raw), "%m/%d/%Y")
                except Exception:
                    date_key = None
    entries.append(("P1", date_norm, date_key, 1.0,5.0,None,None))
# add another profile with dates
entries.append(("P2", format_date_for_bmap("2023-03-15") or "", datetime.fromisoformat("2023-03-15"),2.0,6.0, None, None))
entries.append(("P1","",None,2.0,6.0,None,None))

entries.sort(key=lambda e: (e[0], 0 if e[2] is not None else 1, e[2] or _dt.max))
entries.sort(key=lambda e: (e[0], 0 if e[2] is not None else 1, e[2] or _dt.max))

# build display rows
display_rows = [(p, d or "", xmin, xmax, ymin, ymax) for p,d,dk,xmin,xmax,ymin,ymax in entries]
print(b._format_survey_csv_combined(display_rows))
print()
print(b._format_survey_table_combined(display_rows))
