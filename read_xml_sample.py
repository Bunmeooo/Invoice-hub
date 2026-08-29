import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
xml_path = r"C:\Users\VSUN\Desktop\TEST_CHECK_INVOICE\1C26TYY_00000578_2601084657.xml"

with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

print("XML File Length:", len(content))
print("--- FIRST 2000 CHARACTERS ---")
print(content[:2000])

print("\n--- ALL TAGS AND ATTRIBUTES SEARCHING FOR LOOKUP / PORTAL / CODE ---")
root = ET.fromstring(content)
for elem in root.iter():
    tag_clean = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    val = (elem.text or "").strip()
    if any(k in tag_clean.lower() for k in ["tracuu", "portal", "link", "web", "code", "matc", "mccqt", "inv", "custom", "ttkhac", "ext"]):
        print(f"Tag: <{tag_clean}> -> Text: '{val}' -> Attribs: {elem.attrib}")
    elif any(k in val.lower() for k in ["http", "tra-cuu", "tracuu", "meinvoice", "sinvoice", "bkav", "vnpt"]):
        print(f"Tag with URL: <{tag_clean}> -> Text: '{val}'")
