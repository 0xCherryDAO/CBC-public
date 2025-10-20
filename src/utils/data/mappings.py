from src.utils.runner import *

module_handlers = {
    'CEX_WITHDRAW': process_cex_withdraw,
    'RELAY_BRIDGE': process_relay_bridge,
    'CEX_DEPOSIT': process_cex_deposit,
    'JUMPER_BRIDGE': process_jumper_bridge
}
