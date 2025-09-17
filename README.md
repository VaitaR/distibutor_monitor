# Distributor Monitor

A Streamlit application for monitoring on-chain Claim events from distributor contracts with real-time metrics, tables, and exports.

## Features

- 📊 **Real-time Monitoring**: Track claim events as they happen on-chain
- 📈 **Live Metrics**: Total claimed amounts, unique claimers, claims count
- 📋 **Event Tables**: Sortable tables with converted token amounts and timestamps  
- 📊 **Charts**: Cumulative claims visualization over time
- 📤 **Exports**: CSV events export and JSON snapshots for distributor restarts
- 🔧 **Configurable**: Support for any ERC20 token decimals and custom ABIs
- 🌐 **Multi-network**: Ethereum Mainnet and Sepolia testnet support

## Architecture

- **UI**: Streamlit-based web interface with sidebar controls
- **Data Sources**: Blockscout API for historical logs, Ankr RPC for latest blocks
- **Event Decoding**: Support for indexed and non-indexed parameters
- **State Management**: In-memory state with session persistence
- **Export Formats**: CSV for events, JSON for distributor snapshots

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/distributor-monitor.git
cd distributor-monitor
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Configure API keys in `.env`:
```bash
ANKR_API_KEY=your_ankr_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key
```

### Running the Application

```bash
source .venv/bin/activate
python -m streamlit run src/streamlit_app/app.py
```

The application will be available at `http://localhost:8501`

## Usage

1. **Select Network**: Choose between Mainnet or Sepolia
2. **Upload ABI**: Upload your distributor contract's ABI JSON file
3. **Configure Contract**: 
   - Enter the contract address
   - Set the starting block number
   - Adjust token decimals (18 for most ERC20 tokens)
4. **Select Events**: Choose which events to monitor from the ABI
5. **Initial Sync**: Click "Initial Sync" to fetch historical events
6. **Live Monitoring**: Click "Start Live" for real-time updates

## Configuration

### Networks

- **Mainnet**: Uses Ethereum mainnet via Blockscout and Ankr
- **Sepolia**: Uses Sepolia testnet for development and testing

### Settings

- **From Block**: Starting block for historical sync
- **Page Size**: Number of events to fetch per API request (default: 1000)
- **API QPS**: Rate limiting for API requests (default: 3 requests/second)
- **Confirmations**: Number of blocks to wait for reorg protection (default: 6)
- **Token Decimals**: Decimal places for token amounts (default: 18)

## Development

### Project Structure

```
src/streamlit_app/
├── app.py                 # Main Streamlit application
├── config.py             # Network and API configuration
├── core/                 # Core business logic
│   ├── abi.py           # ABI parsing and event discovery
│   ├── app_logic.py     # High-level sync orchestration
│   ├── claims_aggregate.py # Event aggregation and metrics
│   ├── decode.py        # Event log decoding
│   ├── exports.py       # CSV and JSON export functions
│   └── sync.py          # Initial and incremental sync logic
├── datasources/         # External data source clients
│   ├── blockscout.py    # Blockscout API client
│   └── rpc.py           # JSON-RPC client (Ankr)
├── ui/                  # User interface components
│   ├── sidebar.py       # Sidebar controls and settings
│   ├── state.py         # Application state management
│   └── views.py         # Main content rendering
└── utils/
    └── secrets.py       # Environment variable loading
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_decode.py

# Run end-to-end test (requires environment variables)
RUN_E2E=1 E2E_CONTRACT=0xYourContract pytest -k e2e
```

### Code Quality

The project uses several tools for code quality:

```bash
# Type checking
mypy --strict src/

# Linting and formatting
ruff check src/
ruff format src/

# Run all quality checks
pytest && mypy --strict src/ && ruff check src/
```

## API Keys (Optional)

While the application works without API keys, adding them improves performance:

- **ANKR_API_KEY**: For faster latest block queries
- **ETHERSCAN_API_KEY**: For Etherscan-compatible APIs (Blockscout works without keys)

Create a `.env` file in the project root:
```
ANKR_API_KEY=your_ankr_api_key
ETHERSCAN_API_KEY=your_etherscan_api_key
```

## Troubleshooting

### Common Issues

1. **"No events found"**: Check contract address and starting block number
2. **"OverflowError"**: Large numbers are automatically handled in recent versions
3. **"Initial Sync hangs"**: Try a more recent starting block or check API rate limits
4. **"AttributeError: token_decimals"**: Clear browser cache/session state

### Debug Mode

Set environment variable for verbose logging:
```bash
STREAMLIT_LOGGER_LEVEL=debug streamlit run src/streamlit_app/app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/distributor-monitor/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/distributor-monitor/discussions)
- 📧 **Email**: your.email@example.com
