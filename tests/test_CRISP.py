"""contract.cairo test file."""
import os
from starkware.starknet.business_logic.state.state import BlockInfo
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


# The testing library uses python's asyncio. So the following
# decorator and the ``async`` keyword are needed.
@pytest.mark.asyncio
async def test_setup():
    # Create a new Starknet class that simulates the StarkNet
    # system.
    starknet = await Starknet.empty()

    # Deploy the contract.
    crisp = await starknet.deploy(
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

    # Invoke increase_balance() twice.
    # await contract.increase_balance(amount=10).invoke()
    # await contract.increase_balance(amount=20).invoke()

    # # Check the result of get_balance().
    # execution_info = await contract.get_balance().call()
    # assert execution_info.result == (30,)

    block_number = await crisp.blockNumber().call()
    price_decay_start_block = await crisp.getPriceDecayStartBlock().call()
    print("BLOCK NUMBER: " + str(block_number.result) + "\n")
    print("PRICE DECAY START BLOCK: " + str(price_decay_start_block.result))
    assert block_number.result == price_decay_start_block.result

    # test_starting_price()

    print("=========test_starting_price=============================================")
    price = await crisp.getQuote().call()
    print("test_starting_price: " + str(price.result))

    print("=========test_get_current_EMS=============================================")
    current_ems = await crisp.getCurrentEMS().call()
    print("current_ems: " + str(current_ems.result))

    return crisp


##########
# TEST 1 #
##########
# test starting price
@pytest.mark.asyncio
async def test_starting_price():
    starknet, contract = await contract_factory()
    logger.debug('test_starting_price...')
    print("=========test_starting_price============")
    price = await contract.getQuote().call()
    print("test_starting_price: " + str(price.result))
    assert (price.result == (STARTINGPRICE, ))

##########
# TEST 2 #
##########
# test price doesn't decay when above target sales rate
@pytest.mark.asyncio
async def test_price_decay_above_target_rate():
    starknet, contract = await contract_factory()
    # block_info = await block_info_mock()
    logger.debug("test_price_decay_above_target_rate")
    print("=========test_price_decay_above_target_rate============")
    contract.mint()
    initial_price = await contract.getQuote().call()
    set_block_number(starknet.state, 50)
    final_price = await contract.getQuote().call()
    assert (initial_price.result == final_price.result)

##########
# TEST 3 #
##########
# test price decays when actual sales rate below target sales rate
@pytest.mark.asyncio
async def test_price_decay_below_target_rate():
    starknet, contract = await contract_factory()
    # block_info = await block_info_mock()
    logger.debug("test_price_decay_below_target_rate")
    print("=========test_price_decay_below_target_rate============")
    # purchaseToken
    initial_price = await contract.getQuote().call()
    set_block_number(starknet.state, 200)
    final_price = await contract.getQuote().call()
    assert (initial_price.result > final_price.result)

##########
# TEST 4 #
##########
# test price decays when actual sales rate below target sales rate
@pytest.mark.asyncio
async def test_price_increase_above_target_rate():
    starknet, contract = await contract_factory()
    # block_info = await block_info_mock()
    logger.debug("test_price_increase_above_target_rate")
    print("=========test_price_increase_above_target_rate============")
    # purchaseToken
    set_block_number(starknet.state, 1)
    initial_price = await contract.getQuote().call()
    # purchaseToken
    final_price = await contract.getQuote().call()
    assert (initial_price.result < final_price.result)



# adjusting block number
def set_block_number(self, block_number):
    self.state.block_info = BlockInfo(
        block_number, self.state.block_info.block_timestamp
    )

# adjusting timestamp
def set_block_timestamp(self, block_timestamp):
    self.state.block_info = BlockInfo(
        self.block_info.block_number, block_timestamp
    )


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


    