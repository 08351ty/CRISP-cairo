"""contract.cairo test file."""
from netrc import NetrcParseError
import os
from starkware.starknet.business_logic.state.state import BlockInfo
from starkware.starknet.definitions.general_config import DEFAULT_GAS_PRICE
# from starkware.starknet.public.abi import get_selector_from_name
import logging
from ast import Constant
import pytest
from enum import Enum
import asyncio
from starkware.starknet.testing.starknet import Starknet
# from utils import (
#     Signer, uint, str_to_felt, ZERO_ADDRESS, TRUE, FALSE, assert_revert, assert_event_emitted,
#     get_contract_def, cached_contract, to_uint, sub_uint, add_uint
# )
import logging
logger = logging.getLogger(__name__)

# initializing variables

NAME = 289143346000 # CRISP in int representation
SYMBOL = 289143346000 # CRISP in int representation
TARGETBLOCKSPERSALE = 100
SALEHALFLIFE = 700
PRICESPEED = 1
PRICEHALFLIFE = 100
STARTINGPRICE = 100

# The path to the contract source code.
CONTRACT_FILE = os.path.join("contracts", "CRISP.cairo")

async def contract_factory():
    starknet = await Starknet.empty()
    set_block_number(starknet.state, 0, 10)
    contract = await starknet.deploy(
        source=CONTRACT_FILE,
        constructor_calldata=[
            NAME,
            SYMBOL,
            TARGETBLOCKSPERSALE,
            SALEHALFLIFE,
            PRICESPEED,
            PRICEHALFLIFE,
            STARTINGPRICE
        ]
    )

    # account = await starknet.deploy(
    #     "contracts/Account.cairo",
    #     constructor_calldata=[signer.public_key]
    # )

    return starknet, contract

##########
# TEST 1 #
##########
#test starting price
@pytest.mark.asyncio
async def test_starting_price():
    starknet, contract = await contract_factory()
    price = await contract.getQuote().call()
    assert (price.result == (230584300921369395200, ))

##########
# TEST 2 #
##########
# test price doesn't decay when above target sales rate
@pytest.mark.asyncio
async def test_price_decay_above_target_rate():
    starknet, contract = await contract_factory()
    # print("=========TEST 1: test_price_decay_above_target_rate============\n")
    await contract.mint().invoke()
    # print("NPSP in MINT = " + str(testing.result))
    initial_price = await contract.getQuote().call()
    # pdsb = await contract.getPriceDecayStartBlock().call()
    # print("PDSB = " + str(pdsb.result) + "|||| INITIAL_PRICE: " + str(initial_price.result))
    set_block_number(starknet.state, 50, 11)
    final_price = await contract.getQuote().call()
    # pdsb = await contract.getPriceDecayStartBlock().call()
    # print("PDSB = " + str(pdsb.result) + "|||| FINAL_PRICE: " + str(final_price.result))
    
    assert (initial_price.result == final_price.result)


##########
# TEST 3 #
##########
# test price decays when actual sales rate below target sales rate
@pytest.mark.asyncio
async def test_price_decay_below_target_rate():
    starknet, contract = await contract_factory()
    await contract.mint().invoke()
    initial_price = await contract.getQuote().call()
    set_block_number(starknet.state, 200, 11)
    final_price = await contract.getQuote().call()
    assert (initial_price.result > final_price.result)

##########
# TEST 4 #
##########
# test price increases when minting above target rate
@pytest.mark.asyncio
async def test_price_increase_above_target_rate():
    starknet, contract = await contract_factory()
    await contract.mint().invoke()
    set_block_number(starknet.state, 1, 11)
    initial_price = await contract.getQuote().call()
    await contract.mint().invoke()
    final_price = await contract.getQuote().call()
    assert (initial_price.result < final_price.result)

##########
# TEST 5 #
##########
# test price does not increase when minting below target rate
@pytest.mark.asyncio
async def test_price_increase_below_target_rate():
    starknet, contract = await contract_factory()
    await contract.mint().invoke()
    set_block_number(starknet.state, 1000, 11)
    initial_price = await contract.getQuote().call()
    await contract.mint().invoke()
    final_price = await contract.getQuote().call()
    assert (initial_price.result == final_price.result)

##########
# TEST 6 #
##########
# test EMS decays over time
@pytest.mark.asyncio
async def test_ems_decay():
    starknet, contract = await contract_factory()
    starting_ems = await contract.getCurrentEMS().call()
    set_block_number(starknet.state, 100, 11)
    final_ems = await contract.getCurrentEMS().call()
    assert (starting_ems.result > final_ems.result)

###########
# TEST 7 #
##########
# test EMS increases after every purchase
@pytest.mark.asyncio
async def test_ems_increase():
    starknet, contract = await contract_factory()
    starting_ems = await contract.getCurrentEMS().call()
    await contract.mint().invoke()
    final_ems = await contract.getCurrentEMS().call()
    assert (starting_ems.result < final_ems.result)

# adjusting block number
def set_block_number(self, block_number, gas_price):
    self.state.block_info = BlockInfo(
        block_number, self.state.block_info.block_timestamp, gas_price
    )


    