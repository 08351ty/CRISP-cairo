# Declare this file as a StarkNet contract.
%lang starknet

# Dependencies
from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.cairo.common.uint256 import (
    Uint256, uint256_add, uint256_sub, uint256_le, uint256_lt, uint256_check, uint256_eq
)
from starkware.cairo.common.math import (
    assert_le, assert_lt, assert_not_equal, assert_not_zero
)
from starkware.cairo.common.math_cmp import (
    is_not_zero, is_le
)
from starkware.starknet.common.syscalls import (
    get_contract_address, get_block_number, get_block_timestamp, get_caller_address
)
# from openzeppelin.token.erc20.ERC20 import constructor
from openzeppelin.token.erc721.interfaces.IERC721 import IERC721
from openzeppelin.utils.constants import FALSE, TRUE
from contracts.utils.Math64x61 import (
    Math64x61_mul, 
    Math64x61_fromFelt, 
    Math64x61_sub, 
    Math64x61_div, 
    Math64x61__pow_int, 
    Math64x61_pow, 
    Math64x61_exp, 
    Math64x61_add, 
    Math64x61_log2, 
    Math64x61_ceil, 
    Math64x61_toFelt
)

from openzeppelin.token.erc721.library import (
    ERC721_name,
    ERC721_symbol,
    ERC721_balanceOf,
    ERC721_ownerOf,
    ERC721_getApproved,
    ERC721_isApprovedForAll,
    ERC721_tokenURI,

    ERC721_initializer,
    ERC721_approve, 
    ERC721_setApprovalForAll, 
    ERC721_transferFrom,
    ERC721_safeTransferFrom,
    ERC721_mint,
    ERC721_burn,
    ERC721_only_token_owner,
    ERC721_setTokenURI
)

###############
# CRISP State #
###############

@storage_var
func lastPurchaseBlock() -> (i : felt):
end

@storage_var
func priceDecayStartBlock() -> (i : felt):
end

@storage_var
func curTokenId() -> (i : felt):
end

@storage_var
func nextPurchaseStartingEMS() -> (i : felt):
end

@storage_var
func nextPurchaseStartingPrice() -> (i : felt):
end

####################
# CRISP parameters #
####################

@storage_var
func targetEMS() -> (i : felt):
end

@storage_var
func saleHalfLife() -> (i : felt):
end

@storage_var
func priceSpeed() -> (i : felt):
end

@storage_var
func priceHalfLife() -> (i : felt):
end

###############
# Constructor #
###############

#
@constructor
func constructor{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
    }(_name: felt, 
    _symbol: felt, 
    _targetBlocksPerSale: felt,
    _saleHalfLife: felt,
    _priceSpeed: felt,
    _priceHalfLife: felt,
    _startingPrice: felt
    ):
    alloc_locals
    # set curTokenID = 0
    curTokenId.write(0)

    # set vars as block number
    let block_number: felt = get_block_number()
    lastPurchaseBlock.write(block_number)
    priceDecayStartBlock.write(block_number)

    # setting CRISP parameters
    let (local shl: felt) = Math64x61_fromFelt(_saleHalfLife)
    let (local ps: felt) = Math64x61_fromFelt(_priceSpeed)
    let (local phl: felt) = Math64x61_fromFelt(_priceHalfLife)
    let (local npsp: felt) = Math64x61_fromFelt(_startingPrice)
    saleHalfLife.write(shl)
    priceSpeed.write(ps)
    priceHalfLife.write(phl)

    # calculate target EMS from target blocks per sale
    # 1/(1-2^(-targetBlocksPerSale/saleHalfLife))

    #fp_integers
    let (local fp_one: felt) = Math64x61_fromFelt(1)
    let (local fp_two: felt) = Math64x61_fromFelt(2)
    let (local tbps: felt) = Math64x61_fromFelt(_targetBlocksPerSale)

    let (neg_tbps: felt) = Math64x61_sub(0, tbps)
    let (tbps_div_shl: felt) = Math64x61_div(neg_tbps, shl)
    let (two_exp: felt) = Math64x61_pow(fp_two, tbps_div_shl)
    let (denom: felt) = Math64x61_sub(fp_one, two_exp)
    
    let (_targetEMS: felt) = Math64x61_div(fp_one, denom)
    
    # CRISP parameter set
    targetEMS.write(_targetEMS)

    # CRISP state set
    nextPurchaseStartingEMS.write(_targetEMS)
    nextPurchaseStartingPrice.write(npsp)

    return ()
end



# get current EMS based on current block number. Returns 64x61 fixed-point number
@view
func getCurrentEMS{syscall_ptr : felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (result : felt):
    alloc_locals
    let (lpb: felt) = lastPurchaseBlock.read()
    let (block_number: felt) = get_block_number()
    let (local fp_two: felt) = Math64x61_fromFelt(2)

    local blockInterval: felt = block_number - lpb

    let bi: felt = Math64x61_fromFelt(blockInterval)
    let (_saleHalfLife: felt) = saleHalfLife.read()
    let (local neg_bi: felt) = Math64x61_sub(0, bi)
    let (local two_exp: felt) = Math64x61_div(neg_bi, _saleHalfLife)
    let (weightonPrev: felt) = Math64x61_pow(fp_two, two_exp)
    let (_nextPurchaseStartingEMS: felt) = nextPurchaseStartingEMS.read()

    let (res: felt) = Math64x61_mul(_nextPurchaseStartingEMS, weightonPrev)
    
    return (res)
end

# Get quote for purchasing in current block, decaying price as needed. Returns fixed-point number
@view
func getQuote{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}() -> (result: felt):
    alloc_locals
    local result: felt
    let (local block_number: felt) = get_block_number()
    let (local price_decay_start_block: felt) = priceDecayStartBlock.read()
    local before_or_after: felt = (block_number - price_decay_start_block)
    let (local is_before: felt) = is_le(block_number, price_decay_start_block)
    let (local price_half_life: felt) = priceHalfLife.read()
    let (local next_purchase_starting_price: felt) = nextPurchaseStartingPrice.read()

    if is_before == 1:
        
        # block number is BEFORE block that the decay is supposed to occur
        # simply returns same starting price
        tempvar range_check_ptr = range_check_ptr
        result = next_purchase_starting_price
    else:
        # decay price if current block is AFTER block that the decay is supposed to start
        
        let (decay_interval: felt) = Math64x61_fromFelt(before_or_after)
        let (neg_di: felt) = Math64x61_sub(0, decay_interval)
        let (decay: felt) = Math64x61_div(neg_di, price_half_life)
        let (exp_decay: felt) = Math64x61_exp(decay)
        let (res: felt) = Math64x61_mul(next_purchase_starting_price, exp_decay)

        tempvar range_check_ptr = range_check_ptr
        result = res
    end
    return (result)

end

# Get starting price for the next purchase before time decay. Returns fixed-point number
@view
func getNextStartingPrice{syscall_ptr : felt*, pedersen_ptr : HashBuiltin*, range_check_ptr}(lastPurchasePrice: felt) -> (result: felt):

    alloc_locals
    local result: felt
    let (local next_purchase_starting_ems: felt) = nextPurchaseStartingEMS.read()
    let (local target_ems: felt) = targetEMS.read()
    let (local mismatchRatio: felt) = Math64x61_div(next_purchase_starting_ems, target_ems)
    let (local fp_one: felt) = Math64x61_fromFelt(1)
    let (local price_speed: felt) = priceSpeed.read() #price_speed = 1
    let (local is_before: felt) = is_le(mismatchRatio, fp_one)

    if is_before == 0:
        let (ratio: felt) = Math64x61_mul(mismatchRatio, price_speed)
        let (multiplier: felt) = Math64x61_add(fp_one, ratio)
        let (res: felt) = Math64x61_mul(lastPurchasePrice, multiplier)
        result = res
    else:
        result = lastPurchasePrice
    end

    return (result)
end

@view
func getPriceDecayStartBlock{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (result: felt):
    alloc_locals
    local result: felt
    let (local next_purchase_starting_ems: felt) = nextPurchaseStartingEMS.read()
    let (local target_ems: felt) = targetEMS.read()

    let (local mismatchRatio: felt) = Math64x61_div(next_purchase_starting_ems, target_ems)
    let (local fp_one: felt) = Math64x61_fromFelt(1)
    let (local mmr_over_one: felt) = is_le(mismatchRatio, fp_one)
    let (block_number: felt) = get_block_number()
    let (sale_half_life: felt) = saleHalfLife.read()

    if mmr_over_one == 0:
        # if mismatch ratio > 1, decay should start in the future
        let (log_two: felt) = Math64x61_log2(mismatchRatio)
        # let (ceiling: felt) = Math64x61_ceil(log_two)
        let (di: felt) = Math64x61_mul(sale_half_life, log_two)
        let (decayInterval: felt) = Math64x61_toFelt(di) #di)
        let res: felt = (block_number + decayInterval)
        tempvar range_check_ptr = range_check_ptr
        result = res

    else:
        # else, decay should start at the current block
        tempvar range_check_ptr = range_check_ptr
        result = block_number
    end
    return (result)
end

@external
func mint{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> ():
    alloc_locals
    let (local price: felt) = getQuote()
    let (local fp_one: felt) = Math64x61_fromFelt(1)

    let (last_purchase_block: felt) = get_block_number()
    
    # no such thing as msg.value on starknet yet
    let (cti: felt) = curTokenId.read()
    let incr_cti: felt = cti + 1
    curTokenId.write(incr_cti)

    # update state
    let (get_current_ems: felt) = getCurrentEMS()
    let (next_purchase_starting_ems: felt) = Math64x61_add(get_current_ems, fp_one)
    nextPurchaseStartingEMS.write(next_purchase_starting_ems)
    


    # updating CRISP state
    let (next_purchase_starting_price: felt) = getNextStartingPrice(price)
    nextPurchaseStartingPrice.write(next_purchase_starting_price)
    

    lastPurchaseBlock.write(last_purchase_block)

    let (price_decay_start_block: felt) = getPriceDecayStartBlock()
    priceDecayStartBlock.write(price_decay_start_block)

    # hook for caller to do sth with ETH based on price paid
    afterMint(price)

    # issue refund
    # no such thing as msg.value/msg.sender.call on starknet yet

    return ()
end

func afterMint{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(priceScaled: felt) -> ():
    return ()
end

@view
func blockNumber{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (number: felt):
    let (number: felt) = get_block_number()
    return (number)
end

# Getters for CRISP parameters
@view
func getTargetEMS{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    let (x: felt) = targetEMS.read()
    return (x)
end

@view
func getSaleHalfLife{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    let (x: felt) = saleHalfLife.read()
    return (x)
end

@view
func getPriceSpeed{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    let (x: felt) = priceSpeed.read()
    return (x)
end

@view
func getPriceHalfLife{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    let (x: felt) = priceHalfLife.read()
    return (x)
end

# Getters for CRISP state
@view
func getLastPurchaseBlock{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    return lastPurchaseBlock.read()
end

@view
func getCurTokenId{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    return curTokenId.read()
end

@view
func getNextPurchaseStartingEMS{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    let (x: felt) = nextPurchaseStartingEMS.read()
    return (x)
end

@view
func getNextPurchaseStartingPrice{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}() -> (i : felt):
    let (x: felt) = nextPurchaseStartingPrice.read()
    return (x)
end