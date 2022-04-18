from typing import List

import pytest

from starkware.cairo.common.cairo_function_runner import CairoFunctionRunner
from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash
from starkware.starknet.core.os.os_program import get_os_program
from starkware.starknet.core.os.transaction_hash.transaction_hash import (
    TransactionHashPrefix,
    calculate_deploy_transaction_hash,
    calculate_transaction_hash_common,
    compute_hash_on_elements,
)
from starkware.starknet.definitions import constants
from starkware.starknet.services.api.contract_definition import CONSTRUCTOR_SELECTOR


def run_cairo_transaction_hash(
    tx_hash_prefix: TransactionHashPrefix,
    version: int,
    contract_address: int,
    entry_point_selector: int,
    calldata: List[int],
    max_fee: int,
    chain_id: int,
    additional_data: List[int],
) -> int:
    program = get_os_program()
    runner = CairoFunctionRunner(program, layout="all")

    runner.run(
        "starkware.starknet.core.os.transaction_hash.transaction_hash.get_transaction_hash",
        hash_ptr=runner.pedersen_builtin.base,
        tx_hash_prefix=tx_hash_prefix.value,
        version=version,
        contract_address=contract_address,
        entry_point_selector=entry_point_selector,
        calldata_size=len(calldata),
        calldata=calldata,
        max_fee=max_fee,
        chain_id=chain_id,
        additional_data_size=len(additional_data),
        additional_data=additional_data,
        use_full_name=True,
        verify_secure=False,
    )
    pedersen_ptr, contract_hash = runner.get_return_values(2)

    assert pedersen_ptr == runner.pedersen_builtin.base + (
        runner.pedersen_builtin.cells_per_instance * (9 + len(calldata) + len(additional_data))
    )
    return contract_hash


@pytest.mark.parametrize("tx_hash_prefix", set(TransactionHashPrefix))
@pytest.mark.parametrize("calldata", [[], [659], [540, 338], [73, 443, 234, 350, 841]])
@pytest.mark.parametrize("max_fee", [0, 10, 299])
@pytest.mark.parametrize("version", [0])
@pytest.mark.parametrize("additional_data", [[], [17]])
def test_transaction_hash_common_flow(
    tx_hash_prefix: TransactionHashPrefix,
    version: int,
    calldata: List[int],
    max_fee: int,
    additional_data: List[int],
):
    """
    Tests that the Python and Cairo tx_hash implementations return the same value.
    """
    contract_address = 42
    entry_point_selector = 100
    chain_id = 1

    tx_hash = calculate_transaction_hash_common(
        tx_hash_prefix=tx_hash_prefix,
        version=version,
        contract_address=contract_address,
        entry_point_selector=entry_point_selector,
        calldata=calldata,
        max_fee=max_fee,
        chain_id=chain_id,
        hash_function=pedersen_hash,
        additional_data=additional_data,
    )

    assert tx_hash == run_cairo_transaction_hash(
        tx_hash_prefix=tx_hash_prefix,
        contract_address=contract_address,
        entry_point_selector=entry_point_selector,
        calldata=calldata,
        max_fee=max_fee,
        chain_id=chain_id,
        version=version,
        additional_data=additional_data,
    )


@pytest.mark.parametrize("constructor_calldata", [[], [658], [539, 337], [72, 442, 233, 349, 840]])
def test_deploy_transaction_hash(constructor_calldata: List[int]):
    version = constants.TRANSACTION_VERSION
    contract_address = 1
    chain_id = 1
    max_fee = 0

    expected_hash = compute_hash_on_elements(
        data=[
            TransactionHashPrefix.DEPLOY.value,
            version,
            contract_address,
            CONSTRUCTOR_SELECTOR,
            compute_hash_on_elements(data=constructor_calldata, hash_func=pedersen_hash),
            max_fee,
            chain_id,
        ],
        hash_func=pedersen_hash,
    )
    assert (
        calculate_deploy_transaction_hash(
            contract_address=contract_address,
            constructor_calldata=constructor_calldata,
            chain_id=chain_id,
        )
        == expected_hash
    )
