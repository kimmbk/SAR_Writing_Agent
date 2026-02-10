"""OWL 파일을 파싱하여 시각화용 JSON 데이터를 추출하는 스크립트"""
import xml.etree.ElementTree as ET
import json

OWL_PATH = r"nuscale_ch5_integrated.owl"
OUTPUT_PATH = r"owl_graph_data.json"

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "nr": "http://nuclear-ontology.org/nuscale/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}

BASE = "http://nuclear-ontology.org/nuscale/"

def short(uri):
    if uri and uri.startswith(BASE):
        return uri[len(BASE):]
    return uri

tree = ET.parse(OWL_PATH)
root = tree.getroot()

nodes = {}
edges = []

# Object properties to track as edges
OBJECT_PROPS = [
    "contains", "parent", "containsItem", "containsTable", "containsFigure",
    "crossReferences", "references", "requires", "governs", "satisfies",
    "validates", "verifiedBy", "isEvaluatedBy", "compliesWith", "partOf",
    "containsComponent", "connectedTo", "interfacesWith", "flowPath",
    "containsCOLItem", "relatedCOLItem", "tableSupports", "figureSupports",
]

# Type -> color mapping
TYPE_COLORS = {
    "Template": "#4A90D9",
    "InformationItem": "#E8A838",
    "Condition": "#E05252",
    "DesignParameter": "#50B86C",
    "MechanicalParameter": "#50B86C",
    "ThermalParameter": "#3DA85E",
    "FlowParameter": "#2D9850",
    "MaterialSpec": "#6BC882",
    "ChemistryParameter": "#45A864",
    "Component": "#9B59B6",
    "Valve": "#9B59B6",
    "Pressurizer": "#9B59B6",
    "SteamGenerator": "#9B59B6",
    "ReactorPressureVessel": "#9B59B6",
    "Piping": "#9B59B6",
    "HeatExchanger": "#9B59B6",
    "Instrument": "#9B59B6",
    "Tank": "#9B59B6",
    "Pump": "#9B59B6",
    "System": "#8E44AD",
    "GeneralDesignCriterion": "#F39C12",
    "FederalRegulation": "#D4A017",
    "RegulatoryGuide": "#E67E22",
    "IndustryCode": "#CA8622",
    "TableTemplate": "#1ABC9C",
    "FigureTemplate": "#16A085",
    "ReviewActivity": "#7F8C8D",
    "COLItem": "#C0392B",
}

# Type -> group for clustering
TYPE_GROUP = {
    "Template": 0,
    "InformationItem": 1,
    "Condition": 2,
    "DesignParameter": 3, "MechanicalParameter": 3, "ThermalParameter": 3,
    "FlowParameter": 3, "MaterialSpec": 3, "ChemistryParameter": 3,
    "Component": 4, "Valve": 4, "Pressurizer": 4, "SteamGenerator": 4,
    "ReactorPressureVessel": 4, "Piping": 4, "HeatExchanger": 4,
    "Instrument": 4, "Tank": 4, "Pump": 4,
    "System": 5,
    "GeneralDesignCriterion": 6, "FederalRegulation": 6,
    "RegulatoryGuide": 6, "IndustryCode": 6,
    "TableTemplate": 7,
    "FigureTemplate": 8,
    "ReviewActivity": 9,
    "COLItem": 10,
}

EDGE_COLORS = {
    "contains": "#4A90D9",
    "parent": "#4A90D9",
    "containsItem": "#E8A838",
    "containsTable": "#1ABC9C",
    "containsFigure": "#16A085",
    "crossReferences": "#95A5A6",
    "references": "#95A5A6",
    "requires": "#E05252",
    "governs": "#50B86C",
    "satisfies": "#50B86C",
    "validates": "#E05252",
    "verifiedBy": "#E05252",
    "isEvaluatedBy": "#7F8C8D",
    "compliesWith": "#F39C12",
    "partOf": "#9B59B6",
    "containsComponent": "#8E44AD",
    "connectedTo": "#9B59B6",
    "interfacesWith": "#8E44AD",
    "tableSupports": "#1ABC9C",
    "figureSupports": "#16A085",
    "containsCOLItem": "#C0392B",
    "relatedCOLItem": "#C0392B",
    "flowPath": "#8E44AD",
}

for desc in root.findall("rdf:Description", NS):
    about = desc.get(f"{{{NS['rdf']}}}about")
    if not about:
        continue
    node_id = short(about)

    # Get type
    type_el = desc.find("rdf:type", NS)
    node_type = short(type_el.get(f"{{{NS['rdf']}}}resource")) if type_el is not None else None

    # Skip property/ontology definitions for node creation
    if node_type in ("http://www.w3.org/2002/07/owl#ObjectProperty",
                     "http://www.w3.org/2002/07/owl#DatatypeProperty",
                     "http://www.w3.org/2002/07/owl#Ontology",
                     "http://www.w3.org/2002/07/owl#Class"):
        # Still register class nodes
        if node_type == "http://www.w3.org/2002/07/owl#Class":
            label_el = desc.find("rdfs:label", NS)
            label = label_el.text if label_el is not None else node_id
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": "Class",
                "color": "#34495E",
                "group": 11,
            }
        continue

    # Get label
    label_el = desc.find("rdfs:label", NS)
    label = label_el.text if label_el is not None else node_id

    # Get description
    desc_el = desc.find("dc:description", NS)
    description = desc_el.text if desc_el is not None else ""

    # Section number
    sec_el = desc.find("nr:sectionNumber", NS)
    section_number = sec_el.text if sec_el is not None else ""

    if node_type and not node_type.startswith("http"):
        color = TYPE_COLORS.get(node_type, "#BDC3C7")
        group = TYPE_GROUP.get(node_type, 11)
    else:
        color = "#BDC3C7"
        group = 11

    nodes[node_id] = {
        "id": node_id,
        "label": label,
        "type": node_type if node_type else "Unknown",
        "color": color,
        "group": group,
        "section": section_number,
        "description": description,
    }

    # Extract edges
    for child in desc:
        tag = child.tag
        # Remove namespace
        for prefix, uri in NS.items():
            if tag.startswith(f"{{{uri}}}"):
                local = tag[len(f"{{{uri}}}"):]
                if prefix == "nr" and local in OBJECT_PROPS:
                    target_uri = child.get(f"{{{NS['rdf']}}}resource")
                    if target_uri:
                        target_id = short(target_uri)
                        edges.append({
                            "source": node_id,
                            "target": target_id,
                            "type": local,
                            "color": EDGE_COLORS.get(local, "#BDC3C7"),
                        })
                break

# Ensure all edge targets exist as nodes
for edge in edges:
    for key in ["source", "target"]:
        nid = edge[key]
        if nid not in nodes:
            nodes[nid] = {
                "id": nid,
                "label": nid,
                "type": "Unknown",
                "color": "#BDC3C7",
                "group": 11,
            }

# Stats
type_counts = {}
for n in nodes.values():
    t = n.get("type", "Unknown")
    type_counts[t] = type_counts.get(t, 0) + 1

edge_type_counts = {}
for e in edges:
    t = e["type"]
    edge_type_counts[t] = edge_type_counts.get(t, 0) + 1

data = {
    "nodes": list(nodes.values()),
    "edges": edges,
    "stats": {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": type_counts,
        "edge_types": edge_type_counts,
    }
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Nodes: {len(nodes)}")
print(f"Edges: {len(edges)}")
print(f"\nNode types:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")
print(f"\nEdge types:")
for t, c in sorted(edge_type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")
print(f"\nSaved to {OUTPUT_PATH}")
