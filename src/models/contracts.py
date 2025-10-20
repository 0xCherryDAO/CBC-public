from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar, Mapping


@dataclass
class ERC20:
    abi: str = open('./assets/abi/erc20.json', 'r').read()


@dataclass
class RelayData:
    address: str = None
    abi: str = None


@dataclass
class JumperData:
    address: str = None
    abi: str = None
