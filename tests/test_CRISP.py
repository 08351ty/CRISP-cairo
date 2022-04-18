"""contract.cairo test file."""
import os
# from starkware.starknet.business_logic.state import BlockInfo
# from starkware.starknet.public.abi import get_selector_from_name
import logging
from ast import Constant
import pytest
from enum import Enum
import asyncio
from starkware.starknet.testing.starknet import Starknet
from utils import (
    Signer, uint, str_to_felt, ZERO_ADDRESS, TRUE, FALSE, assert_revert, assert_event_emitted,
    get_contract_def, cached_contract, to_uint, sub_uint, add_uint
)
import logging
logger = logging.getLogger(__name__)

# initializing variables

NAME = 289143346000 # CRISP in int rep
SYMBOL = 289143346000 # CRISP in int rep
TARGETBLOCKSPERSALE = 100
SALEHALFLIFE = 700
PRICESPEED = 1
PRICEHALFLIFE = 100
STARTINGPRICE = 100

# The path to the contract source code.
CONTRACT_FILE = os.path.join("contracts", "CRISP.cairo")


# The testing library uses python's asyncio. So the following
# decorator and the ``async`` keyword are needed.
@pytest.mark.asyncio
async def test_increase_balance():
    # Create a new Starknet class that simulates the StarkNet
    # system.
    starknet = await Starknet.empty()

    # Deploy the contract.
    contract = await starknet.deploy(
        source=CONTRACT_FILE,
    )

    # Invoke increase_balance() twice.
    await contract.increase_balance(amount=10).invoke()
    await contract.increase_balance(amount=20).invoke()

    # Check the result of get_balance().
    execution_info = await contract.get_balance().call()
    assert execution_info.result == (30,)
