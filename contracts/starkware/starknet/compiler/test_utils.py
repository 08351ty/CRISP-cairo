from starkware.cairo.lang.cairo_constants import DEFAULT_PRIME
from starkware.cairo.lang.compiler.preprocessor.preprocessor_error import PreprocessorError
from starkware.cairo.lang.compiler.preprocessor.preprocessor_test_utils import (
    CAIRO_TEST_MODULES,
    preprocess_str_ex,
)
from starkware.cairo.lang.compiler.preprocessor.preprocessor_test_utils import (
    verify_exception as generic_verify_exception,
)
from starkware.cairo.lang.compiler.test_utils import read_file_from_dict
from starkware.starknet.compiler.starknet_pass_manager import starknet_pass_manager
from starkware.starknet.compiler.starknet_preprocessor import StarknetPreprocessedProgram

STARKNET_TEST_MODULES = {
    **CAIRO_TEST_MODULES,
    "starkware.starknet.common.storage": """
struct Storage:
end

func normalize_address{range_check_ptr}(addr : felt) -> (res : felt):
    ret
end
""",
    "starkware.starknet.common.syscalls": """
func call_contract{syscall_ptr : felt*}(
        contract_address : felt, function_selector : felt, calldata_size : felt,
        calldata : felt*) -> (retdata_size : felt, retdata : felt*):
    ret
end

func delegate_call{syscall_ptr : felt*}(
        contract_address : felt, function_selector : felt, calldata_size : felt,
        calldata : felt*) -> (retdata_size : felt, retdata : felt*):
    ret
end

func storage_read{syscall_ptr : felt*}(address : felt) -> (value : felt):
    ret
end

func storage_write{syscall_ptr : felt*}(address : felt, value : felt):
    ret
end

func emit_event{syscall_ptr : felt*}(keys_len : felt, keys : felt*, data_len : felt, data : felt*):
    ret
end
""",
    "starkware.cairo.common.cairo_builtins": """
struct HashBuiltin:
end
""",
    "starkware.cairo.common.hash": """
from starkware.cairo.common.cairo_builtins import HashBuiltin

func hash2{hash_ptr : HashBuiltin*}(x, y) -> (result):
    ret
end
""",
    "starkware.cairo.common.alloc": """
func alloc() -> (result):
    ret
end
""",
    "starkware.cairo.common.memcpy": """
func memcpy(dst : felt*, src : felt*, len):
    # Manually revoke ap tracking to better simulate memcpy().
    ap += [ap]
    ret
end
""",
}


def preprocess_str(code: str) -> StarknetPreprocessedProgram:
    preprocessed = preprocess_str_ex(
        code=code,
        pass_manager=starknet_pass_manager(
            prime=DEFAULT_PRIME, read_module=read_file_from_dict(STARKNET_TEST_MODULES)
        ),
    )
    assert isinstance(preprocessed, StarknetPreprocessedProgram)
    return preprocessed


def verify_exception(code: str, error: str, exc_type=PreprocessorError):
    return generic_verify_exception(
        code=code,
        error=error,
        pass_manager=starknet_pass_manager(
            prime=DEFAULT_PRIME, read_module=read_file_from_dict(STARKNET_TEST_MODULES)
        ),
        exc_type=exc_type,
    )
