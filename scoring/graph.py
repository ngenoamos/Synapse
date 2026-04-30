"""Pillar 2: Graph Clustering for Sybil Farm Detection"""

import networkx as nx
import math
from collections import Counter, defaultdict
from typing import Dict, Any, List, Set, Tuple
from datetime import datetime, timedelta
from .config import ALL_TIER_1_ADDRESSES

class GraphClusteringEngine:
    """
    Pillar 2: Graph clustering for Sybil farm detection.
    Three-layer defence: Local Clustering, Louvain Modularity, Jaccard Similarity.
    """
    
    def __init__(self):
        self.tier_1_addresses = ALL_TIER_1_ADDRESSES
        self.verification_registry = {}
    
    # ========== LAYER 1: VERIFICATION REGISTRY ==========
    
    def classify_address(self, address: str, tx_count: int = 0, age_days: int = 0, tvl: float = 0) -> int:
        """
        Classify address into Tiers 0, 2, or 1.
        
        Returns:
            0: Tier 0 (Unverified)
            2: Tier 2 (Recent - 0.3x weight)
            1: Tier 1 (Verified - full weight)
        """
        address_lower = address.lower()
        
        # Check if in hardcoded Tier-1 list
        if address_lower in self.tier_1_addresses:
            return 1
        
        # Check for CEX wallets (simplified - would query from registry)
        # Check for wallets with SRS > 60 (from Pillar 1)
        
        # Temporal decay: previously Tier 1 but old interactions
        if age_days > 365:  # Older than 12 months
            return 2  # Tier 2 (recency decay)
        
        # Default: Tier 0
        return 0
    
    def get_external_degree(self, counterparties: Set[str], tx_counts: Dict[str, int] = None) -> Tuple[int, float]:
        """
        Calculate external degree: weighted connections to verified addresses.
        
        Returns:
            (weighted_count, raw_count)
        """
        weighted_count = 0
        raw_count = 0
        
        for cp in counterparties:
            tier = self.classify_address(cp)
            if tier == 1:
                weighted_count += 1.0
                raw_count += 1
            elif tier == 2:
                weighted_count += 0.3  # Recency decay weight
                raw_count += 1
        
        return weighted_count, raw_count
    
    # ========== LAYER 2: LOCAL CLUSTERING COEFFICIENT ==========
    
    def build_transaction_graph(self, transactions: List[Dict], wallet_address: str) -> nx.Graph:
        """
        Build directed graph of wallet interactions.
        
        Nodes: wallet_address + all counterparties
        Edges: transactions between addresses
        """
        G = nx.Graph()
        G.add_node(wallet_address)
        
        for tx in transactions:
            from_addr = tx.get("from_address")
            to_addr = tx.get("to_address")
            
            if from_addr and to_addr:
                G.add_edge(from_addr, to_addr)
        
        return G
    
    def calculate_clustering_coefficient(self, G: nx.Graph, wallet_address: str) -> Dict[str, Any]:
        """
        Calculate local clustering coefficient for the wallet node.
        
        C_v = 2 * (number of triangles through v) / (deg(v) * (deg(v) - 1))
        
        Range: 0 to 1
        - High clustering (C_v > 0.5): Dense internal connections (island signal)
        - Low clustering (C_v < 0.1): Minimal internal structure
        """
        if wallet_address not in G:
            return {"clustering_coefficient": 0, "triangle_count": 0, "degree": 0}
        
        degree = G.degree(wallet_address)
        
        # Count triangles containing wallet_address
        triangles = 0
        neighbors = list(G.neighbors(wallet_address))
        
        for i, u in enumerate(neighbors):
            for v in neighbors[i+1:]:
                if G.has_edge(u, v):
                    triangles += 1
        
        # Clustering coefficient formula
        if degree >= 2:
            clustering = (2 * triangles) / (degree * (degree - 1))
        else:
            clustering = 0
        
        # Island detection: high clustering + low external degree
        is_island = clustering > 0.3 and degree < 5
        
        return {
            "clustering_coefficient": round(clustering, 4),
            "triangle_count": triangles,
            "degree": degree,
            "is_island": is_island,
            "interpretation": "High clustering with few connections -> island structure" if is_island else "Normal connectivity"
        }
    
    # ========== LAYER 3: LOUVAIN MODULARITY ==========
    
    def detect_communities(self, G: nx.Graph) -> Dict[str, Any]:
        """
        Detect communities using Louvain modularity.
        
        Modularity Q = (1/2m) * Σ [A_ij - (k_i * k_j)/(2m)] * δ(c_i, c_j)
        
        Range: -0.5 to 1
        - High modularity (Q > 0.3): Distinct, isolated communities
        - Low modularity (Q < 0.1): Well-integrated network
        """
        try:
            from networkx.algorithms.community import louvain_communities, modularity
            
            # Detect communities
            communities = list(louvain_communities(G, seed=42))
            mod = modularity(G, communities)
            
            # Check if wallet is in an isolated community
            community_sizes = [len(c) for c in communities]
            avg_community_size = sum(community_sizes) / len(communities) if communities else 0
            
            is_isolated_community = mod > 0.3 and len(communities) > 1
            
            return {
                "modularity": round(mod, 4),
                "num_communities": len(communities),
                "avg_community_size": round(avg_community_size, 2),
                "is_isolated_community": is_isolated_community,
                "interpretation": "Isolated community detected" if is_isolated_community else "Well-integrated network"
            }
        except Exception as e:
            return {"modularity": 0, "num_communities": 0, "avg_community_size": 0, "is_isolated_community": False}
    
    # ========== LAYER 4: JACCARD BEHAVIOURAL SIMILARITY ==========
    
    def calculate_jaccard_similarity(self, wallet_a: str, wallet_b: str, G: nx.Graph) -> float:
        """
        Calculate Jaccard similarity between two wallets' neighbor sets.
        
        J(A, B) = |N(A) ∩ N(B)| / |N(A) ∪ N(B)|
        
        Returns similarity between 0 and 1.
        """
        if wallet_a not in G or wallet_b not in G:
            return 0
        
        neighbors_a = set(G.neighbors(wallet_a))
        neighbors_b = set(G.neighbors(wallet_b))
        
        if not neighbors_a and not neighbors_b:
            return 0
        
        intersection = len(neighbors_a & neighbors_b)
        union = len(neighbors_a | neighbors_b)
        
        return intersection / union if union > 0 else 0
    
    def detect_clone_scripts(self, G: nx.Graph, wallet_address: str, transactions: List[Dict]) -> Dict[str, Any]:
        """
        Detect wallets executing identical automated scripts.
        
        - J > 0.85 with 3+ neighbours → 0.4× clone penalty
        - J > 0.95 with any neighbour → manual review trigger
        """
        if wallet_address not in G:
            return {"clone_detected": False, "similarity": 0, "clone_penalty": 1.0}
        
        # Find wallets with high Jaccard similarity
        high_similarity = []
        very_high_similarity = []
        
        for neighbor in G.neighbors(wallet_address):
            jaccard = self.calculate_jaccard_similarity(wallet_address, neighbor, G)
            if jaccard > 0.85:
                high_similarity.append((neighbor, jaccard))
            if jaccard > 0.95:
                very_high_similarity.append((neighbor, jaccard))
        
        # Apply clone penalties
        clone_penalty = 1.0
        
        if len(very_high_similarity) > 0:
            clone_penalty = 0.2
            trigger_manual = True
        elif len(high_similarity) >= 3:
            clone_penalty = 0.4
            trigger_manual = False
        else:
            trigger_manual = False
        
        return {
            "clone_detected": clone_penalty < 1.0,
            "similarity_count": len(high_similarity),
            "high_similarity": len(high_similarity),
            "very_high_similarity": len(very_high_similarity),
            "clone_penalty": clone_penalty,
            "trigger_manual_review": trigger_manual,
            "interpretation": f"Clone penalty {clone_penalty}x applied" if clone_penalty < 1.0 else "No clone patterns detected"
        }
    
    # ========== COMPLETE PILLAR 2 ANALYSIS ==========
    
    def analyze_pillar_2(self, wallet_address: str, transactions: List[Dict], counterparties: Set[str]) -> Dict[str, Any]:
        """
        Complete Pillar 2 analysis combining all three algorithms.
        """
        # Build graph
        G = self.build_transaction_graph(transactions, wallet_address)
        
        # Layer 1: External degree
        weighted_degree, raw_degree = self.get_external_degree(counterparties)
        
        # Layer 2: Local clustering coefficient
        clustering = self.calculate_clustering_coefficient(G, wallet_address)
        
        # Layer 3: Louvain modularity
        communities = self.detect_communities(G)
        
        # Layer 4: Jaccard clone detection
        clones = self.detect_clone_scripts(G, wallet_address, transactions)
        
        # Apply zero-trust gate
        zero_trust_active = weighted_degree == 0
        zero_trust_cap = 20  # Cap SRS at 20 if no Tier-1 connections
        
        # Combine scores
        island_score = 1.0
        if clustering["is_island"]:
            island_score = 0.5
        if communities["is_isolated_community"]:
            island_score *= 0.5
        island_score *= clones["clone_penalty"]
        
        pillar_2_score = 100 * island_score
        
        return {
            "pillar_2": {
                "external_degree": {
                    "weighted": round(weighted_degree, 2),
                    "raw": raw_degree,
                    "zero_trust_gate": zero_trust_active,
                    "srs_cap": zero_trust_cap if zero_trust_active else None
                },
                "local_clustering": clustering,
                "louvain_modularity": communities,
                "jaccard_similarity": clones,
                "pillar_2_score": round(pillar_2_score, 2),
                "island_multiplier": round(island_score, 2),
                "interpretation": self._get_interpretation(zero_trust_active, clustering, communities, clones)
            }
        }
    
    def _get_interpretation(self, zero_trust: bool, clustering: Dict, communities: Dict, clones: Dict) -> str:
        """Generate human-readable interpretation"""
        if zero_trust:
            return "CRITICAL: Wallet has zero Tier-1 connections. This is a classic island structure."
        elif clones["clone_detected"]:
            return f"WARNING: Clone script detected. {clones['interpretation']}"
        elif clustering["is_island"]:
            return "Island structure detected: dense internal clustering with few external connections"
        else:
            return "Normal graph structure: well-connected to verified protocols"
