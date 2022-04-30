"""contract.cairo test file."""
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
    tgtems = await contract.getTargetEMS().call()
    shl = await contract.getSaleHalfLife().call()
    ps = await contract.getPriceSpeed().call()
    phl = await contract.getPriceHalfLife().call()

    print("\nTarget EMS: " + str(tgtems.result))
    print("Sale Half Life: " + str(shl.result))
    print("Price Speed: " + str(ps.result))
    print("Price Half Life: " + str(phl.result))

    # account = await starknet.deploy(
    #     "contracts/Account.cairo",
    #     constructor_calldata=[signer.public_key]
    # )

    return starknet, contract


# The testing library uses python's asyncio. So the following
# decorator and the ``async`` keyword are needed.
# @pytest.mark.asyncio
# async def test_setup():
#     # Create a new Starknet class that simulates the StarkNet
#     # system.
#     starknet = await Starknet.empty()

#     # Deploy the contract.
#     crisp = await starknet.deploy(
#         source=CONTRACT_FILE,
#         constructor_calldata=[
#             NAME,
#             SYMBOL,
#             TARGETBLOCKSPERSALE,
#             SALEHALFLIFE,
#             PRICESPEED,
#             PRICEHALFLIFE,
#             STARTINGPRICE
#         ]
#     )

#     # Invoke increase_balance() twice.
#     # await contract.increase_balance(amount=10).invoke()
#     # await contract.increase_balance(amount=20).invoke()

#     # # Check the result of get_balance().
#     # execution_info = await contract.get_balance().call()
#     # assert execution_info.result == (30,)

#     return crisp



##########
# TEST 1 #
##########
# test starting price
@pytest.mark.asyncio
async def test_starting_price():
    starknet, contract = await contract_factory()
    logger.debug('test_starting_price...')
    print("=========test_starting_price============")
    #price = await contract.getQuote().call()
    #print("test_starting_price: " + str(price.result))
    #assert (price.result == (STARTINGPRICE, ))

# ##########
# # TEST 2 #
# ##########
# # test price doesn't decay when above target sales rate
# @pytest.mark.asyncio
# async def test_price_decay_above_target_rate():
#     starknet, contract = await contract_factory()
#     # block_info = await block_info_mock()
#     logger.debug("test_price_decay_above_target_rate")
#     print("=========TEST 1: test_price_decay_above_target_rate============\n")
#     contract.mint()
#     initial_price = await contract.getQuote().call()
#     # set_block_number(starknet.state, 50, 11)
#     final_price = await contract.getQuote().call()
#     assert (initial_price.result == final_price.result)
#     print("========TEST 1: SUCCESSFUL============\n")

##########
# TEST 3 #
##########
# test price decays when actual sales rate below target sales rate
@pytest.mark.asyncio
async def test_price_decay_below_target_rate():
    starknet, contract = await contract_factory()
    print("=========test_price_decay_below_target_rate=======================")
    pdsb = await contract.getPriceDecayStartBlock().call()
    print(">>>>>>get_price_decay_start_block: " + str(pdsb.result))
    gc_ems = await contract.getCurrentEMS().call()
    tgtems = await contract.getTargetEMS().call()
    print("\nTarget EMS: " + str(tgtems.result) + " AND Current EMS: " + str(gc_ems.result))
    contract.mint()
    print("minted")
    
    initial_price = await contract.getQuote().call()
    #print("initial_price: " + str(initial_price.result))
    #print(">>>>>>block_number_initial: " + str(starknet.state.state.block_info.block_number) + "<<<<<<<<<<<<")
    set_block_number(starknet.state, 50, 10)
    contract.mint()
    #print(">>>>>>block_number_final: " + str(starknet.state.state.block_info.block_number) + "<<<<<<<<<<<<")
    # print(">>>>>>current_ems: " + str(await contract.getCurrentEMS().call().result) + "<<<<<<<<<<<<")
    final_price = await contract.getQuote().call()
    pdsb = await contract.getPriceDecayStartBlock().call()
    print(">>>>>>get_price_decay_start_block: " + str(pdsb.result))
    #gc_ems = await contract.getCurrentEMS().call()
    #tgtems = await contract.getTargetEMS().call()
    #print("\nTarget EMS: " + str(tgtems.result) + " AND Current EMS: " + str(gc_ems.result))
    #print("final_price: " + str(final_price.result))
    assert (initial_price.result > final_price.result)

##########
# TEST 4 #
##########
# test price decays when actual sales rate below target sales rate
# @pytest.mark.asyncio
# async def test_price_increase_above_target_rate():
#     starknet, contract = await contract_factory()
#     # block_info = await block_info_mock()
#     logger.debug("test_price_increase_above_target_rate")
#     print("=========test_price_increase_above_target_rate============")
#     contract.mint()
#     set_block_number(starknet.state, 1, 10)
#     initial_price = await contract.getQuote().call()
#     contract.mint()
#     final_price = await contract.getQuote().call()
#     assert (initial_price.result < final_price.result)


# adjusting block number
def set_block_number(self, block_number, gas_price):
    self.state.block_info = BlockInfo(
        block_number, self.state.block_info.block_timestamp, gas_price
    )

# adjusting timestamp
def set_block_timestamp(self, block_timestamp, gas_price):
    self.state.block_info = BlockInfo(
        self.state.block_info.block_number, block_timestamp, gas_price
    )

async def crisp_params():
    starknet, contract = await contract_factory()
    tgtems = await contract.getTargetEMS().call()
    shl = await contract.getSaleHalfLife().call()
    ps = await contract.getPriceSpeed().call()
    phl = await contract.getPriceHalfLife().call()

    print("\nTarget EMS: " + str(tgtems.result) + "\n")
    print("Sale Half Life: " + str(shl.result) + "\n")
    print("Price Speed: " + str(ps.result) + "\n")
    print("Price Half Life: " + str(phl.result) + "\n")


# async def purchase_tokens():
#     contract = await contract_factory()
#     current_price = contract.getQuote().call().result
#     contract.mint()
#     )


    # function mineBlocks(uint256 numBlocks) private {
    #     uint256 currentBlock = block.number;
    #     vm.roll(currentBlock + numBlocks);
    # }

    # function purchaseToken() private {
    #     uint256 currentPrice = uint256(token.getQuote().toInt());
    #     token.mint{value: currentPrice}();
    # }


    