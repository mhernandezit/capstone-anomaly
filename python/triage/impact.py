from typing import Dict
from python.utils.schema import FeatureBin


class ImpactScorer:
    def __init__(self, cfg_roles: Dict):
        self.roles = cfg_roles.get("roles", {})
        th = cfg_roles.get("thresholds", {})
        self.edge_local_prefix_max = th.get("edge_local_prefix_max", 100)
        self.edge_local_pct_table_max = th.get("edge_local_pct_table_max", 0.01)
        self.corr_secs = th.get("correlation_window_secs", 60)
        # TODO: maintain short history of role activity for correlation

    def classify(self, fb: FeatureBin, mp_score: float) -> Dict:
        # Role involvement proxy = peers seen in bin
        roles_hit = set()
        for peer in fb.peers.keys():
            role = self.roles.get(peer, "unknown")
            roles_hit.add(role)
        # Prefix spread proxy = announcements + withdrawals (you can wire exact table deltas)
        prefix_spread = fb.totals.get("ann_total", 0) + fb.totals.get("wdr_total", 0)
        edge_local = (
            roles_hit == {"tor"} or roles_hit == {"server", "tor"}
        ) and prefix_spread <= self.edge_local_prefix_max
        impact = "EDGE_LOCAL" if edge_local else "NETWORK_IMPACTING"
        return {
            "impact": impact,
            "roles": list(roles_hit),
            "prefix_spread": prefix_spread,
            "mp": mp_score,
        }
