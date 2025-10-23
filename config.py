TG_BOT_TOKEN = ''  # str ('2282282282:AAZYB35L2PoziKsri6RFPOASdkal-z1Wi_s')
TG_USER_ID = None  # int (22822822) or None

SHUFFLE_WALLETS = False
PAUSE_BETWEEN_WALLETS = [0, 0]
PAUSE_BETWEEN_MODULES = [20, 40]
MAX_PARALLEL_ACCOUNTS = 50
MAX_GWEI = 200

RETRIES = 10  # Сколько раз повторять 'зафейленное' действие
PAUSE_BETWEEN_RETRIES = 5  # Пауза между повторами

CEX_WITHDRAW = False  # Вывод с CEX на кошельки, если требуется. (CEXWithdrawSettings)
CEX_DEPOSIT = False  # Перевод с кошельков на адреса из recipients.txt. (CEXDepositSettings)

RELAY_BRIDGE = False  # Настройка в RelayBridgeSettings
JUMPER_BRIDGE = False  # Настройка в JumperBridgeSettings


class RelayBridgeSettings:
    from_chain = ['BASE', 'OP', 'ARB']
    to_chain = ['ETH']

    from_token = ['USDC']
    to_token = ['ETH']

    amount = [0.0002, 0.0004]  # Кол-во ETH [от, до]
    use_percentage = True  # Использовать ли процент от баланса вместо amount
    bridge_percentage = [1, 1]  # Процент от баланса. 0.1 - это 10%, 0.27 - это 27% и т.д.

    to_token_min_balances = {
        'ARB': {
            'USDC': 0
        }
    }


class JumperBridgeSettings:
    from_chain = ['ARB']
    to_chain = ['ARB']

    from_token = ['USDT']
    to_token = ['ETH']

    amount = [0.0002, 0.0004]  # Кол-во ETH [от, до]
    use_percentage = True  # Использовать ли процент от баланса вместо amount
    bridge_percentage = [1, 1]  # Процент от баланса. 0.1 - это 10%, 0.27 - это 27% и т.д.

    to_token_min_balances = {
        'ARB': {
            'USDC': 100
        }
    }


class CEXWithdrawSettings:  # Вывод с CEX на кошельки
    cex = 'Bitget'  # Binance/OKX/Bitget
    to_chain = ['Arbitrum One']  # 'Base' / 'Optimism' / 'Arbitrum One'
    to_token = 'USDT'
    amount = [10, 10]

    to_token_min_balances = {
        'Arbitrum One': {
            'USDC': 1
        }
    }


class CEXDepositSettings:
    chains = ['OP']
    token = 'ETH'
    keep_balances = {
        'BASE': [0.00005, 0.000067],
        'ARB': [0.001, 0.002],
        'OP': [0, 0]
    }


class OKXSettings:
    API_KEY = ''
    API_SECRET = ''
    API_PASSWORD = ''

    PROXY = None  # 'http://login:pass@ip:port' (если нужно)


class BinanceSettings:
    BINANCE_KEY = ''
    BINANCE_SECRET = ''

    PROXY = None  # 'http://login:pass@ip:port' (если нужно)


class BitgetSettings:
    BITGET_KEY = ''
    BITGET_SECRET = ''
    BITGET_PASSWORD = ''

    PROXY = None  # 'http://login:pass@ip:port' (если нужно)
