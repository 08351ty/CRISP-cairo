from starkware.cairo.common.hash_chain import compute_hash_chain
from starkware.cairo.lang.vm.crypto import pedersen_hash


def test_compute_hash_chain():
    data = [1, 2, 3]
    assert compute_hash_chain(data) == pedersen_hash(1, pedersen_hash(2, 3))
