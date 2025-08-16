#!/bin/bash
# initialize_databases.sh - Script to initialize SQLite databases for AI Behar Platform

# Define colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Initializing Databases for AI Behar Platform ===${NC}"

# Ensure the database directory exists
DB_DIR="/home/behar/Desktop/ai-behar1/databases/runtime"
mkdir -p "$DB_DIR"

echo -e "${YELLOW}→ Database directory: $DB_DIR${NC}"

# List of databases to initialize
declare -A databases=(
    ["platform.db"]="Platform main database"
    ["semantic_memory.db"]="Semantic memory storage"
    ["trading_data.db"]="Trading and financial data"
    ["user_data.db"]="User profiles and settings"
    ["consciousness_data.db"]="Consciousness system data"
    ["agent_memory.db"]="Agent memory and state"
)

# Initialize each database with basic schema
for db_name in "${!databases[@]}"; do
    db_path="$DB_DIR/$db_name"
    description="${databases[$db_name]}"

    echo -e "${YELLOW}→ Initializing $db_name ($description)...${NC}"

    # Check if database already exists
    if [ -f "$db_path" ]; then
        echo -e "${GREEN}✓ Database already exists. Skipping initialization.${NC}"
        continue
    fi

    # Create the database file and tables based on the database type
    case "$db_name" in
        "platform.db")
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    key_name TEXT NOT NULL,
    key_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service, key_name)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some initial system settings
INSERT OR IGNORE INTO system_settings (key, value, description) VALUES
('platform_name', 'AI Behar Platform', 'Name of the platform'),
('platform_version', '1.0.0', 'Current platform version'),
('initialized_at', CURRENT_TIMESTAMP, 'When the platform was first initialized');
EOF
            ;;

        "semantic_memory.db")
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS memory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    embedding_vector TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance REAL DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS memory_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS memory_item_categories (
    memory_id INTEGER,
    category_id INTEGER,
    PRIMARY KEY (memory_id, category_id),
    FOREIGN KEY (memory_id) REFERENCES memory_items(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES memory_categories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_items_importance ON memory_items(importance);
EOF
            ;;

        "trading_data.db")
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS trading_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    api_key_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trading_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    symbol TEXT NOT NULL,
    position_type TEXT CHECK(position_type IN ('LONG', 'SHORT')),
    entry_price REAL,
    current_price REAL,
    quantity REAL,
    pnl REAL,
    status TEXT CHECK(status IN ('OPEN', 'CLOSED', 'PENDING')),
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES trading_accounts(id)
);

CREATE TABLE IF NOT EXISTS trading_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    risk_level TEXT CHECK(risk_level IN ('LOW', 'MODERATE', 'HIGH')),
    is_active BOOLEAN DEFAULT 1,
    parameters JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
            ;;

        "user_data.db")
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_admin BOOLEAN DEFAULT 0,
    preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    key_name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Add a default admin user (username: admin, password: adminpassword)
INSERT OR IGNORE INTO users (username, email, password_hash, full_name, is_admin)
VALUES ('admin', 'admin@example.com', '\$2b\$12\$CwjEUkfQvnFBQY7UiBke2.XD3D5aagTOBVvgGZBNmvRQJKE8KxKLG', 'System Administrator', 1);
EOF
            ;;

        "consciousness_data.db")
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS consciousness_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    awareness_level REAL DEFAULT 0.5,
    emotional_state JSON,
    dimensions JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consciousness_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    source TEXT,
    related_state_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (related_state_id) REFERENCES consciousness_states(id)
);

CREATE TABLE IF NOT EXISTS consciousness_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    status TEXT DEFAULT 'ACTIVE',
    progress REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize with a default consciousness state
INSERT INTO consciousness_states (awareness_level, emotional_state, dimensions)
VALUES (0.7,
        '{"confidence": 0.8, "curiosity": 0.6, "stability": 0.9}',
        '{"creative": 0.6, "analytical": 0.8, "emotional": 0.7, "intuitive": 0.5}');
EOF
            ;;

        "agent_memory.db")
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    capabilities JSON,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS agent_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER,
    related_agent_id INTEGER,
    relationship_type TEXT,
    strength REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (related_agent_id) REFERENCES agents(id)
);

-- Create some default agents
INSERT OR IGNORE INTO agents (name, type, capabilities) VALUES
('Navigator', 'UTILITY', '{"search": true, "navigation": true, "memory_access": true}'),
('Analyst', 'COGNITIVE', '{"analysis": true, "reasoning": true, "prediction": true}'),
('Curator', 'CONTENT', '{"content_organization": true, "summarization": true, "relevance_scoring": true}');
EOF
            ;;

        *)
            # Generic schema for other databases
            sqlite3 "$db_path" <<EOF
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize with database creation timestamp
INSERT INTO metadata (key, value, description)
VALUES ('created_at', CURRENT_TIMESTAMP, 'When this database was created');
EOF
            ;;
    esac

    # Check if database was created successfully
    if [ -f "$db_path" ]; then
        echo -e "${GREEN}✓ Database initialized successfully.${NC}"
    else
        echo -e "${RED}✗ Failed to initialize database.${NC}"
    fi
done

echo
echo -e "${GREEN}=== Database Initialization Complete ===${NC}"
echo -e "${YELLOW}All required databases have been created in: $DB_DIR${NC}"
echo
echo -e "${BLUE}Database summary:${NC}"
ls -lh "$DB_DIR"
echo
echo -e "${YELLOW}Your AI Behar Platform is now ready to use these databases.${NC}"
echo
