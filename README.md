## Requirements

- Python 3.6+
- Required Python packages:
  - web3
  - pyyaml
  - colorama
  - decimal

## Installation

1. Clone this repository or download the script
   ```
   git clone https://github.com/allixina/Qxl
   ```
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `config.yml` file (see configuration section below)

## Configuration

Fill a `config.yml` file in the same directory as the script with the following structure:

```yaml
rpc: "https://rpc-url-for-your-ethereum-node"
private_key: "0x-your-private-key-here"
amount:
  min: 0.001  # Minimum ETH amount to send
  max: 0.01   # Maximum ETH amount to send
gas: 3        # Gas price multiplier (optional, default: 3)
delay:
  min: 10     # Minimum seconds between transactions
  max: 15     # Maximum seconds between transactions
cycle_time: 24 # delay for between cycle
token_contract_address: "0x-your-token-contact-address"
```

4. Fill a `wallet.txt` file in the same directory as the script. This file should contain a list of recipient wallet addresses, one per line. For example:

    ```
    0x1234...abcd
    0x5678...efgh
    0x9abc...ijkl
    ```

⚠️ **Security Warning**: Keep your private key secure and never share it. Only use this script with test accounts and on test networks.

## Usage

Run the script with:

```
python app.py
```

The script will continuously send transactions until manually stopped (Ctrl+C).

## Warning

This tool is intended for testing and development purposes only. Using it on mainnet can result in the loss of real funds. Always test on testnets first.