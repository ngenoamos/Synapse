"""Configuration constants for SRS scoring system"""

# Time window
STANDARD_WINDOW_DAYS = 180
ACCELERATED_WINDOW_DAYS = 90

# Transaction thresholds
MIN_QUALIFYING_TXS = 50
MIN_PROTOCOL_BREADTH = 3
MIN_TX_PER_WEEK_DENSE = 5

# Value filters
MIN_USD_VALUE = 5  # $5 minimum for non-dust

# ETH and BNB prices (for dust filtering)
ETH_PRICE_USD = 3500.0
BNB_PRICE_USD = 300.0

# Gas entropy buckets
GAS_BUCKETS = 20
GAS_MIN_VALUE_GWEI = 1.0
GAS_MAX_VALUE_GWEI = 500.0

# Entropy buckets
HOUR_BUCKETS = 24
DAY_BUCKETS = 7
GAS_BUCKETS = 20  # For Week 3

# Density multiplier
SPARSE_DENSITY_MULTIPLIER = 0.7
FULL_DENSITY_MULTIPLIER = 1.0

# Score caps
SINGLE_PROTOCOL_CAP = 40
ZERO_TRUST_CAP = 20

# Tier-1 Protocol addresses (Ethereum mainnet)
TIER_1_PROTOCOLS = {
    "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "uniswap_v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    "aave_v2": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
    "aave_v3": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "compound": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
    "curve": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
    "ens_registry": "0x314159265dD8dbb310642f98f50C066173C1259b",
    "ens_resolver": "0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41",
    "lido": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    "rocket_pool": "0xDC035D45d973E3EC169dBe6faF81a1AbEf93Bc2F",
    "frax": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
    "maker_dao": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
}

# Protocol categories for diversity scoring
PROTOCOL_CATEGORIES = {
    # DEX / Swaps
    "uniswap": ["0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "0xE592427A0AEce92De3Edee1F18E0157C05861564"],
    "curve": ["0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"],
    
    # Lending
    "aave": ["0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9", "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"],
    "compound": ["0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"],
    
    # Staking / LSD
    "lido": ["0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"],
    "rocket_pool": ["0xDC035D45d973E3EC169dBe6faF81a1AbEf93Bc2F"],
    
    # Identity / ENS
    "ens": ["0x314159265dD8dbb310642f98f50C066173C1259b", "0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41"],
    
    # Stablecoins
    "maker": ["0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2"],
    "frax": ["0x853d955aCEf822Db058eb8505911ED77F175b99e"],
}

# Flatten to set for quick lookup
ALL_TIER_1_ADDRESSES = {addr.lower() for addrs in PROTOCOL_CATEGORIES.values() for addr in addrs}

# Diversity thresholds
MIN_DIVERSITY_PROTOCOLS = 3   # Minimum for basic score
TARGET_DIVERSITY_PROTOCOLS = 10  # Target for full score
MAX_DIVERSITY_SCORE = 100

# Diversity weights in combined score
DIVERSITY_WEIGHT = 0.35