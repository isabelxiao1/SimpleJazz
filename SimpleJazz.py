import json
import streamlit as st
import pandas as pd


### Chord Symbol Formatting

def format_chord_symbol(chord):
    chord = chord.replace('maj7', 'Δ7')
    chord = chord.replace('min', '-')
    chord = chord.replace('m7b5', 'ø7')
    chord = chord.replace('m6', '-6')
    chord = chord.replace('m7', '-7')
    chord = chord.replace('b', '♭')
    return chord



### Cross-reference ii-V-Is


def build_iivi_lookup(df):
    lookup = set()
    for _, row in df.iterrows():
        ii = format_chord_symbol(row[0].strip())
        V  = format_chord_symbol(row[1].strip())
        I  = format_chord_symbol(row[2].strip())
        lookup.add((ii, V, I))
    return lookup


# Load your ii–V–I CSVs here:
iiVIMaj = pd.read_csv("major_iivi.csv")  
iiVIMin = pd.read_csv("minor_iivi.csv")

lookup_major = build_iivi_lookup(iiVIMaj)
lookup_minor = build_iivi_lookup(iiVIMin)

def parse_bars(chord_str):
    """
    Preserve bars EXACTLY as written.
    Also create:
      - flat_chords: all chord symbols individually
      - bar_map: which flat-chord indices belong to each bar
    """
    bar_strings = [b.strip() for b in chord_str.split("|")]

    flat_chords = []
    bar_map = []

    for bar in bar_strings:
        parts = [p.strip() for p in bar.split(",") if p.strip()]
        indices = []
        for p in parts:
            formatted = format_chord_symbol(p)
            indices.append(len(flat_chords))
            flat_chords.append(formatted)
        bar_map.append(indices)

    return bar_strings, flat_chords, bar_map



def detect_iivi_labels_flat(chords):
    n = len(chords)
    labels = [" "] * n

    for i in range(n - 2):
        seq = (chords[i], chords[i+1], chords[i+2])

        if seq in lookup_major:
            labels[i], labels[i+1], labels[i+2] = "ii", "V", "I"
        elif seq in lookup_minor:
            labels[i], labels[i+1], labels[i+2] = "ii", "V", "i"

    return labels


### Combine chords& labels into display lines


def rebuild_label_bars_fixed(bar_strings, flat_labels, bar_map):
    """
    For each bar, compute the label text for that bar (comma-separated),
    then return two aligned lists:
      - bar_cells: the printed chord text for each bar (unchanged)
      - label_cells: the label text padded/centered to the same width as the bar cell
    This ensures labels show exactly under their chords.
    """
    bar_cells = []
    label_cells = []

    for bar, mapping in zip(bar_strings, bar_map):
        # chord_parts: original pieces within bar (keeps commas/spacing logic)
        chord_parts = [p.strip() for p in bar.split(",") if p.strip()]

        # build label parts corresponding to those chord_parts
        lbl_parts = []
        for part, idx in zip(chord_parts, mapping):
            # convert single-space-only labels to empty string (so we don't show " ")
            lab = flat_labels[idx].strip() if flat_labels[idx] and flat_labels[idx].strip() else ""
            lbl_parts.append(lab)

        # join with comma+space to mirror chord part separation visually
        label_text = ", ".join(lbl_parts)
        chord_text = ", ".join(chord_parts)

        # compute a fixed width for the cell: use max of chord_text length and label length
        width = max(len(chord_text), len(label_text), 1)

        # center the label into the width so it sits under the chord visually
        label_cell = label_text.center(width)
        chord_cell = chord_text.center(width)

        bar_cells.append(chord_cell)
        label_cells.append(label_cell)

    return bar_cells, label_cells


def format_chord_string(chord_str, bars_per_line=4):
    # Step 1: parse bars
    bar_strings, flat_chords, bar_map = parse_bars(chord_str)

    # Step 2: detect ii–V–i on flat chords
    flat_labels = detect_iivi_labels_flat(flat_chords)

    # Step 3: rebuild labels for each bar as fixed-width cells
    bar_cells, label_cells = rebuild_label_bars_fixed(bar_strings, flat_labels, bar_map)

    # Step 4: group into display lines of bars_per_line, preserving alignment
    out_lines = []
    n = len(bar_cells)
    for i in range(0, n, bars_per_line):
        group_bars = bar_cells[i:i+bars_per_line]
        group_labels = label_cells[i:i+bars_per_line]

        # join bars with " | " exactly as you print chords
        chord_line = " | ".join(group_bars)
        label_line = " | ".join(group_labels)

        # add them as a single code block section
        out_lines.append(chord_line + "\n" + label_line)

    # separate groups with blank lines for readability (as before)
    return "\n\n".join(out_lines)




### Load JSON & build chart

def safe(x, default="Unknown"):
    """Return a safe string for metadata that might be missing or None."""
    if x is None:
        return default
    try:
        s = str(x)
    except Exception:
        return default
    return s if s.strip() else default


def get_jazz_chart(title, json_path='JazzStandards.json'):
    
    # Open Jazz JSON file, JazzStandards.json
    with open(json_path, 'r', encoding='utf-8') as f:
        tunes = json.load(f)

    # Search lowercase
    tune = next((t for t in tunes if t["Title"].lower() == title.lower()), None)
    if not tune:
        return f"❌ '{title}' not found.", {}
    
    meta = {
        "title": tune["Title"],
        "composer": safe(tune.get("Composer")),
        "key": safe(tune.get("Key")),
        "rhythm": safe(tune.get("Rhythm")),
        "time": safe(tune.get("TimeSignature"))
    }
    



    # Markdown output
    output = ''
    

    for section in tune["Sections"]:
        # Optional labels (A, B, etc.)
        if "Label" in section:
            output += f"**{section['Label']}**\n\n"

        output += "```\n"
        output += format_chord_string(section["MainSegment"]["Chords"])
        output += "\n```\n\n"

        # Optional endings
        if "Endings" in section:
            for i, ending in enumerate(section["Endings"], start=1):
                output += f"Ending {i}:\n```\n"
                output += format_chord_string(ending["Chords"])
                output += "\n```\n\n"
                

    return output, meta



### Testing

### Read json as dataframe

df = pd.read_json("JazzStandards.json")
print(df.head())


### Testing

get_jazz_chart('Autumn Leaves')


### Dashboard!

with open("JazzStandards.json", "r", encoding="utf-8") as f:
    tunes = json.load(f)

titles = [t["Title"] for t in tunes]


st.title("🎷 Jazz Standards Chord Viewer")

search_query = st.text_input("Search for a tune:", "")
filtered = [t for t in tunes if search_query.lower() in t["Title"].lower()]

if not filtered and search_query:
    st.warning("No tunes found.")
elif filtered:
    selected = st.selectbox("Select tune:", [t["Title"] for t in filtered])
    chart_text, meta = get_jazz_chart(selected)

    # Display metadata separately so Streamlit can’t swallow it into a code block
    st.markdown(f"## {meta['title']}")
    st.write(f"**Composer:** {meta['composer']}")
    st.write(f"**Key:** {meta['key']}")
    st.write(f"**Rhythm:** {meta['rhythm']}")
    st.write(f"**Time Signature:** {meta['time']}")
    st.markdown("---")

    # Now show the chord chart
    st.markdown(chart_text)

else:
    st.info("Type a tune name above to begin 🎵")

