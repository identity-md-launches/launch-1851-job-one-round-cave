# ABI Workbench

A Python standard-library command line tool that computes Ethereum function selectors with Keccak-256, encodes function arguments into unsigned calldata, and decodes return values from a supplied ABI. It performs no RPC, wallet, signing, or transaction submission.

It supports scalar `address`, `bool`, `int`/`uint` widths from 8 through 256 bits, `bytes1` through `bytes32`, and dynamic `string` and `bytes`. Tuples and arrays are outside this compact first version. ABI files should be JSON arrays of function entries.

## Try it

From the repository root, run:

```sh
python3 line-4/tools/abi-workbench/abi_workbench.py --demo
```

This prints the canonical `transfer(address,uint256)` selector and complete calldata for the real ZTO contract address and an illustrative amount; it does not send anything. For a supplied ABI, use `encode --abi ABI.json --function transfer --args '["0xd782bdea4ef02a0bd391eb9089470c8080f0a68e",12]'`, or `decode --abi ABI.json --function balanceOf --data 0x...`.

## Result and limits

The offline demo ran successfully and produced selector `0xa9059cbb`, matching the known ERC-20 transfer selector. The implementation follows standard 32-byte ABI head/tail layout for the supported types. It does not handle overloaded names (choose a unique function name in the ABI), tuples, arrays, event logs, or validate all canonical sign-extension rules for unusual malformed return words. A decoded value is a local interpretation of supplied bytes, not evidence of an on-chain call result.
