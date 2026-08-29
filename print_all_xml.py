import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
xml_path = r"C:\Users\VSUN\Desktop\TEST_CHECK_INVOICE\1C26TYY_00000578_2601084657.xml"

root = ET.fromstring(open(xml_path, "r", encoding="utf-8", errors="ignore").read())

for elem in root.iter():
    tag_clean = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if elem.text and elem.text.strip():
        print(f"<{tag_clean}>: {elem.text.strip()[:100]}")
