from typing import List, Dict


def rerank_by_scheme_and_source(results: List[Dict], target_scheme: str = None) -> List[Dict]:
    """Re-rank results: exact scheme match first, then by score."""
    def scheme_bonus(r):
        meta = r.get("metadata", {})
        scheme = str(meta.get("scheme", "")).lower()
        if target_scheme and target_scheme.lower() in scheme:
            return 1000.0  # huge bonus for exact match
        return 0.0
    
    def source_type_bonus(r):
        meta = r.get("metadata", {})
        source_type = str(meta.get("source_type", "")).lower()
        if "groww" in source_type:
            return 100.0
        return 0.0
    
    for r in results:
        r["rerank_score"] = r.get("score", 0) + scheme_bonus(r) + source_type_bonus(r)
    
    results_sorted = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
    for r in results_sorted:
        del r["rerank_score"]
    return results_sorted
