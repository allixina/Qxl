import logging
import time
from decimal import Decimal, getcontext
import secrets
from web3 import Web3
import yaml
from colorama import Fore, Style, init
import requests
import random

init(autoreset=True)

class ColorFormatter(logging.Formatter):
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    datefmt = '%H:%M:%S'
    FORMATS = {
        logging.INFO: Fore.CYAN + format_str + Style.RESET_ALL,
        logging.ERROR: Fore.RED + format_str + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + format_str + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)

handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

getcontext().prec = 18

class Config:
    def __init__(self, path: str):
        with open(path, 'r') as file:
            config = yaml.safe_load(file)
        self.rpc = config['rpc']
        self.private_key = config['private_key']
        self.min_amount = Decimal(config['amount']['min'])
        self.max_amount = Decimal(config['amount']['max'])
        self.gas = Decimal(config.get('gas', 3))
        delay_config = config.get('delay', {'min': 10, 'max': 15})
        self.min_delay = delay_config['min'] if isinstance(delay_config, dict) else delay_config
        self.max_delay = delay_config['max'] if isinstance(delay_config, dict) else delay_config
        self.token_contract_address = config.get('token_contract_address')
        self.cycle_time = config.get('cycle_time', 24) * 60 * 60

class EthereumHandler:
    def __init__(self, config: Config):
        self.web3 = Web3(Web3.HTTPProvider(config.rpc))
        self.account = self.web3.eth.account.from_key(config.private_key)
        self.config = config
        self.current_nonce = self.web3.eth.get_transaction_count(self.account.address)
        self.tx_counter = 0
        self.addresses = []
        self.using_github = False
        self.token_contract = None

    def load_addresses_from_file(self):
        try:
            with open('wallet.txt', 'r') as file:
                self.addresses = [addr.strip() for addr in file.readlines() if addr.strip()]
            logger.info(f"Loaded {len(self.addresses)} addresses from wallet.txt")
        except FileNotFoundError:
            logger.error("wallet.txt not found")
            exit(1)

    def load_addresses_from_url(self, max_addresses=None):
        try:
            url = "https://raw.githubusercontent.com/clwkevin/LayerOS/refs/heads/main/addressteasepoliakyc.txt"
            response = requests.get(url)
            response.raise_for_status()
            addresses = [addr.strip() for addr in response.text.splitlines() if addr.strip()]
            random.shuffle(addresses)
            if max_addresses and max_addresses > 0:
                addresses = addresses[:max_addresses]
            self.addresses = addresses
            logger.info(f"Loaded and shuffled {len(self.addresses)} addresses from URL")
            self.using_github = True
        except Exception as e:
            logger.error(f"Failed to load addresses from URL: {str(e)}")
            exit(1)

    def load_token_contract(self, contract_address):
        try:
            abi = '[{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},' \
                  '{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},' \
                  '{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"}]'
            self.token_contract = self.web3.eth.contract(address=self.web3.to_checksum_address(contract_address), abi=abi)
            token_name = self.token_contract.functions.name().call()
            token_symbol = self.token_contract.functions.symbol().call()
            logger.info(f"Loaded token contract at address: {contract_address}")
            logger.info(f"Token Name: {Fore.GREEN}{token_name}{Style.RESET_ALL}, Symbol: {Fore.CYAN}{token_symbol}{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Failed to load token contract: {str(e)}")
            exit(1)

    def send_transaction(self, use_custom_token=False):
        try:
            if self.using_github:
                self.load_addresses_from_url()

            recipient = secrets.choice(self.addresses)
            shortened_recipient = recipient[:7] + '...' + recipient[-3:]
            gas_price = int(self.web3.eth.gas_price * self.config.gas)

            if use_custom_token and self.token_contract:
                amount = Decimal(secrets.SystemRandom().uniform(float(self.config.min_amount), float(self.config.max_amount)))
                amount_in_wei = int(amount * (10 ** 18))
                tx = self.token_contract.functions.transfer(recipient, amount_in_wei).build_transaction({
                    'from': self.account.address, 
                    'gasPrice': gas_price,
                    'nonce': self.current_nonce,
                    'chainId': self.web3.eth.chain_id
                })
                tx['gas'] = self.web3.eth.estimate_gas(tx)
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                shortened_hash = self.web3.to_hex(tx_hash)[:15] + '...'
                logger.info(f"{Fore.MAGENTA}[{Style.RESET_ALL}{Fore.RED}#{self.tx_counter}{Style.RESET_ALL}{Fore.MAGENTA}]{Style.RESET_ALL} Sent {Fore.GREEN}{amount:.4f}{Style.RESET_ALL} tokens to {Fore.YELLOW}{shortened_recipient}{Style.RESET_ALL}. "
                           f"Tx: {Fore.CYAN}{shortened_hash}{Style.RESET_ALL}")
            else:
                amount = Decimal(secrets.SystemRandom().uniform(float(self.config.min_amount), float(self.config.max_amount)))
                tx = {
                    'to': recipient,
                    'value': self.web3.to_wei(amount, 'ether'),
                    'gasPrice': gas_price,
                    'nonce': self.current_nonce,
                    'chainId': self.web3.eth.chain_id
                }
                tx['gas'] = self.web3.eth.estimate_gas(tx)
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                shortened_hash = self.web3.to_hex(tx_hash)[:10] + '...'
                logger.info(f"{Fore.MAGENTA}[{Style.RESET_ALL}{Fore.RED}#{self.tx_counter}{Style.RESET_ALL}{Fore.MAGENTA}]{Style.RESET_ALL} Sent {Fore.GREEN}{amount:.4f}{Style.RESET_ALL} ETH to {Fore.YELLOW}{shortened_recipient}{Style.RESET_ALL}. "
                           f"Tx: {Fore.CYAN}{shortened_hash}{Style.RESET_ALL}")

            self.tx_counter += 1
            self.current_nonce += 1
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            self.current_nonce = self.web3.eth.get_transaction_count(self.account.address)

    def start(self, use_custom_token=False):
        logger.info(f"Using address: {Fore.YELLOW}{self.account.address}{Style.RESET_ALL}")
        while True:
            for _ in range(len(self.addresses)):
                self.send_transaction(use_custom_token=use_custom_token)
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                time.sleep(delay)
            logger.info(f"All transactions for this cycle are done. Waiting for {self.config.cycle_time // 3600} hours before the next cycle.")
            time.sleep(self.config.cycle_time)

if __name__ == "__main__":
    config = Config('config.yml')
    handler = EthereumHandler(config)
    
    print("\nChoose address loading option:")
    print("1. Load addresses from wallet.txt")
    print("2. Load addresses from GitHub")
    
    choice = input("\nEnter your choice (1-2): ")
    
    if choice == '1':
        handler.load_addresses_from_file()
    elif choice == '2':
        max_addresses = input("\nEnter maximum number of addresses (press Enter for no limit): ").strip()
        if max_addresses:
            try:
                max_addresses = int(max_addresses)
                handler.load_addresses_from_url(max_addresses)
            except ValueError:
                logger.error("Invalid number entered")
                exit(1)
        else:
            handler.load_addresses_from_url()
    else:
        logger.error("Invalid choice")
        exit(1)

    print("\nChoose transaction type:")
    print("1. Send native token (ETH)")
    print("2. Send custom token")

    tx_choice = input("\nEnter your choice (1-2): ")

    use_custom_token = False
    if tx_choice == '2':
        if config.token_contract_address:
            handler.load_token_contract(config.token_contract_address)
            use_custom_token = True
        else:
            logger.error("Token contract address not found in config.yml")
            exit(1)

    handler.start(use_custom_token=use_custom_token)