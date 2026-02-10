"""DIAMOND OWL 온톨로지를 파싱하여 시각화용 JSON 데이터를 추출하는 스크립트"""
import xml.etree.ElementTree as ET
import json

OWL_PATH = r"diamond_ontology.owl"
OUTPUT_PATH = r"diamond_graph_data.json"

tree = ET.parse(OWL_PATH)
root = tree.getroot()

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "obo": "http://purl.obolibrary.org/obo/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

DIAMOND_BASE = "https://github.com/idaholab/DIAMOND/"
BFO_BASE = "http://purl.obolibrary.org/obo/"
NUCLEAR_PREFIX = "nuclear:"

def short(uri):
    if not uri:
        return uri
    if uri.startswith(DIAMOND_BASE):
        return uri[len(DIAMOND_BASE):]
    if uri.startswith(BFO_BASE):
        return uri[len(BFO_BASE):]
    if uri.startswith(NUCLEAR_PREFIX):
        return "nuclear:" + uri[len(NUCLEAR_PREFIX):]
    if uri.startswith("http://www.w3.org/"):
        parts = uri.split("#")
        if len(parts) == 2:
            return parts[1]
        return uri.split("/")[-1]
    return uri

def get_label(el):
    label_el = el.find("rdfs:label", NS)
    if label_el is not None and label_el.text:
        return label_el.text.strip()
    return None

def get_definition(el):
    defn = el.find("obo:IAO_0000115", NS)
    if defn is not None and defn.text:
        return defn.text.strip()
    return ""

nodes = {}
edges = []

# --- Parse Classes ---
for cls in root.findall(".//owl:Class[@rdf:about]", NS):
    uri = cls.get(f"{{{NS['rdf']}}}about")
    node_id = short(uri)
    label = get_label(cls) or node_id
    definition = get_definition(cls)

    # Determine source/category
    if uri.startswith(DIAMOND_BASE):
        source = "DIAMOND"
    elif uri.startswith(BFO_BASE) and "BFO" in uri:
        source = "BFO"
    elif uri.startswith(BFO_BASE) and "IAO" in uri:
        source = "IAO"
    elif "nuclear:" in uri:
        source = "Nuclear"
    else:
        source = "Other"

    nodes[node_id] = {
        "id": node_id,
        "label": label,
        "type": "Class",
        "source": source,
        "definition": definition[:200] if definition else "",
        "uri": uri,
    }

    # subClassOf edges
    for sub in cls.findall("rdfs:subClassOf", NS):
        parent_uri = sub.get(f"{{{NS['rdf']}}}resource")
        if parent_uri:
            parent_id = short(parent_uri)
            edges.append({
                "source": node_id,
                "target": parent_id,
                "type": "subClassOf",
            })

# --- Parse ObjectProperties ---
for prop in root.findall(".//owl:ObjectProperty[@rdf:about]", NS):
    uri = prop.get(f"{{{NS['rdf']}}}about")
    node_id = short(uri)
    label = get_label(prop) or node_id
    definition = get_definition(prop)

    nodes[node_id] = {
        "id": node_id,
        "label": label,
        "type": "ObjectProperty",
        "source": "Nuclear" if "nuclear:" in uri else "DIAMOND",
        "definition": definition[:200] if definition else "",
        "uri": uri,
    }

    # inverseOf
    inv = prop.find("owl:inverseOf", NS)
    if inv is not None:
        inv_uri = inv.get(f"{{{NS['rdf']}}}resource")
        if inv_uri:
            edges.append({
                "source": node_id,
                "target": short(inv_uri),
                "type": "inverseOf",
            })

    # domain / range
    domain = prop.find("rdfs:domain", NS)
    if domain is not None:
        d_uri = domain.get(f"{{{NS['rdf']}}}resource")
        if d_uri:
            edges.append({
                "source": node_id,
                "target": short(d_uri),
                "type": "domain",
            })
    rng = prop.find("rdfs:range", NS)
    if rng is not None:
        r_uri = rng.get(f"{{{NS['rdf']}}}resource")
        if r_uri:
            edges.append({
                "source": node_id,
                "target": short(r_uri),
                "type": "range",
            })

# --- Parse DatatypeProperties ---
for prop in root.findall(".//owl:DatatypeProperty[@rdf:about]", NS):
    uri = prop.get(f"{{{NS['rdf']}}}about")
    node_id = short(uri)
    label = get_label(prop) or node_id
    definition = get_definition(prop)

    nodes[node_id] = {
        "id": node_id,
        "label": label,
        "type": "DatatypeProperty",
        "source": "DIAMOND",
        "definition": definition[:200] if definition else "",
        "uri": uri,
    }

# --- Parse NamedIndividuals ---
for ind in root.findall(".//owl:NamedIndividual[@rdf:about]", NS):
    uri = ind.get(f"{{{NS['rdf']}}}about")
    node_id = short(uri)
    label = get_label(ind) or node_id
    definition = get_definition(ind)

    # Get type
    type_el = ind.find("rdf:type", NS)
    ind_type = short(type_el.get(f"{{{NS['rdf']}}}resource")) if type_el is not None else "Individual"

    nodes[node_id] = {
        "id": node_id,
        "label": label,
        "type": "Individual",
        "instance_of": ind_type,
        "source": "DIAMOND" if uri.startswith(DIAMOND_BASE) else "Nuclear",
        "definition": definition[:200] if definition else "",
        "uri": uri,
    }

    # Type edge
    if type_el is not None:
        type_uri = type_el.get(f"{{{NS['rdf']}}}resource")
        if type_uri:
            edges.append({
                "source": node_id,
                "target": short(type_uri),
                "type": "instanceOf",
            })

# Ensure all edge targets exist
for edge in edges:
    for key in ["source", "target"]:
        nid = edge[key]
        if nid not in nodes:
            nodes[nid] = {
                "id": nid,
                "label": nid,
                "type": "External",
                "source": "External",
                "definition": "",
            }

# Color mapping
SOURCE_COLORS = {
    "BFO": "#E74C3C",
    "IAO": "#E67E22",
    "DIAMOND": "#3498DB",
    "Nuclear": "#2ECC71",
    "External": "#95A5A6",
    "Other": "#BDC3C7",
}

TYPE_COLORS = {
    "ObjectProperty": "#9B59B6",
    "DatatypeProperty": "#1ABC9C",
    "Individual": "#F39C12",
}

for n in nodes.values():
    if n["type"] in TYPE_COLORS:
        n["color"] = TYPE_COLORS[n["type"]]
    else:
        n["color"] = SOURCE_COLORS.get(n.get("source", "Other"), "#BDC3C7")

EDGE_COLORS = {
    "subClassOf": "#3498DB",
    "inverseOf": "#9B59B6",
    "domain": "#E67E22",
    "range": "#E74C3C",
    "instanceOf": "#F39C12",
}

for e in edges:
    e["color"] = EDGE_COLORS.get(e["type"], "#95A5A6")

# Stats
source_counts = {}
type_counts = {}
for n in nodes.values():
    s = n.get("source", "Other")
    source_counts[s] = source_counts.get(s, 0) + 1
    t = n["type"]
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
        "source_counts": source_counts,
        "type_counts": type_counts,
        "edge_types": edge_type_counts,
    }
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Nodes: {len(nodes)}")
print(f"Edges: {len(edges)}")
print(f"\nBy source:")
for s, c in sorted(source_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"\nBy type:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")
print(f"\nEdge types:")
for t, c in sorted(edge_type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")
print(f"\nSaved to {OUTPUT_PATH}")
