from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.hash_state import hash_finalize, hash_init, hash_update_single
from starkware.cairo.common.registers import get_fp_and_pc

const STARKNET_OS_CONFIG_VERSION = 'StarknetOsConfig1'

struct StarknetOsConfig:
    # The identifier of the chain.
    # This field can be used to prevent replay of testnet transactions on mainnet.
    member chain_id : felt
    # The (L2) address of the fee token contract.
    member fee_token_address : felt
end

# Calculates the hash of StarkNet OS config.
func get_starknet_os_config_hash{hash_ptr : HashBuiltin*}(
    starknet_os_config : StarknetOsConfig*
) -> (starknet_os_config_hash : felt):
    let (hash_state_ptr) = hash_init()
    let (hash_state_ptr) = hash_update_single(
        hash_state_ptr=hash_state_ptr, item=STARKNET_OS_CONFIG_VERSION
    )
    let (hash_state_ptr) = hash_update_single(
        hash_state_ptr=hash_state_ptr, item=starknet_os_config.chain_id
    )
    let (hash_state_ptr) = hash_update_single(
        hash_state_ptr=hash_state_ptr, item=starknet_os_config.fee_token_address
    )

    let (starknet_os_config_hash) = hash_finalize(hash_state_ptr=hash_state_ptr)

    return (starknet_os_config_hash=starknet_os_config_hash)
end

func starknet_os_config_new(chain_id : felt, fee_token_address : felt) -> (
    starknet_os_config : StarknetOsConfig*
):
    let (fp_val, pc_val) = get_fp_and_pc()
    static_assert StarknetOsConfig.SIZE == Args.SIZE
    return (starknet_os_config=cast(fp_val - 2 - StarknetOsConfig.SIZE, StarknetOsConfig*))
end
