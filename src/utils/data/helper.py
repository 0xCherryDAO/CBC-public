from colorama import Fore

with open('config.py', 'r', encoding='utf-8-sig') as file:
    module_config = file.read()

exec(module_config)

with open('data/wallets.txt', 'r', encoding='utf-8-sig') as file:
    private_keys = [line.strip() for line in file]

with open('data/proxies.txt', 'r', encoding='utf-8-sig') as file:
    proxies = [line.strip() for line in file]
    if not proxies:
        proxies = [None for _ in range(len(private_keys))]

with open('data/recipients.txt', 'r', encoding='utf-8-sig') as file:
    recipients = [line.strip() for line in file]

print(Fore.BLUE + f'Loaded {len(private_keys)} wallets:')
print('\033[39m')
