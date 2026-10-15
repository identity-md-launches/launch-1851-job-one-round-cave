#!/usr/bin/env python3
"""Small offline Ethereum ABI function calldata encoder and return decoder."""
import argparse
import json
import re
import sys

MASK = (1 << 64) - 1
ROT = [0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43, 25, 39, 41, 45, 15, 21, 8, 18, 2, 61, 56, 14]
RC = [0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]

def rol(x, n):
    return x if n == 0 else ((x << n) | (x >> (64 - n))) & MASK

def keccak256(data):
    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    padded.extend(b'\0' * ((rate - len(padded) % rate - 1) % rate))
    padded.append(0x80)
    a = [0] * 25
    for off in range(0, len(padded), rate):
        block = padded[off:off + rate]
        for i in range(rate // 8):
            a[i] ^= int.from_bytes(block[i*8:i*8+8], 'little')
        for rc in RC:
            c = [a[x] ^ a[x+5] ^ a[x+10] ^ a[x+15] ^ a[x+20] for x in range(5)]
            d = [c[(x-1)%5] ^ rol(c[(x+1)%5], 1) for x in range(5)]
            for y in range(5):
                for x in range(5): a[x+5*y] ^= d[x]
            b = [0] * 25
            for y in range(5):
                for x in range(5): b[y + 5*((2*x+3*y)%5)] = rol(a[x+5*y], ROT[x+5*y])
            for y in range(5):
                for x in range(5): a[x+5*y] = b[x+5*y] ^ ((~b[(x+1)%5+5*y]) & b[(x+2)%5+5*y])
            a[0] ^= rc
    return b''.join(v.to_bytes(8, 'little') for v in a)[:32]

def canonical(param):
    t = param.get('type', '')
    if t.startswith('tuple'):
        raise ValueError('tuple types are not supported in this compact tool')
    if not re.fullmatch(r'(address|bool|string|bytes|bytes(?:[1-9]|[12][0-9]|3[0-2])|u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)?)', t):
        raise ValueError(f'unsupported ABI type: {t!r}')
    return t

def dynamic(t): return t in ('string', 'bytes')

def word(n):
    if n < 0 or n >= 1 << 256: raise ValueError('ABI word is outside uint256 range')
    return n.to_bytes(32, 'big')

def encode_value(t, value):
    if t == 'address':
        if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{40}', value): raise ValueError('address must be 0x followed by 40 hex digits')
        return bytes.fromhex(value[2:]).rjust(32, b'\0')
    if t == 'bool':
        if not isinstance(value, bool): raise ValueError('bool argument must be true or false')
        return word(int(value))
    if t == 'string': raw = value.encode('utf-8') if isinstance(value, str) else (_ for _ in ()).throw(ValueError('string argument must be text'))
    elif t == 'bytes':
        if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value): raise ValueError('bytes argument must be even-length 0x hex')
        raw = bytes.fromhex(value[2:])
    else:
        m = re.fullmatch(r'bytes([0-9]+)', t)
        if m:
            size = int(m.group(1))
            if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value): raise ValueError(f'{t} argument must be 0x hex')
            raw = bytes.fromhex(value[2:])
            if len(raw) != size: raise ValueError(f'{t} requires exactly {size} bytes')
            return raw.ljust(32, b'\0')
        m = re.fullmatch(r'(u?int)([0-9]*)', t)
        if m:
            bits = int(m.group(2) or '256')
            try: n = int(value)
            except Exception: raise ValueError(f'{t} argument must be an integer')
            signed = m.group(1) == 'int'
            lo, hi = (-(1 << (bits-1)), (1 << (bits-1))-1) if signed else (0, (1 << bits)-1)
            if not lo <= n <= hi: raise ValueError(f'{t} value is out of range')
            return word(n % (1 << 256))
        raise ValueError(f'unsupported ABI type: {t}')
    return word(len(raw)) + raw + b'\0' * ((-len(raw)) % 32)

def encode_tuple(params, values):
    if len(params) != len(values): raise ValueError(f'expected {len(params)} arguments, received {len(values)}')
    head_size = 32 * len(params)
    head, tail = bytearray(), bytearray()
    for p, v in zip(params, values):
        t = canonical(p)
        if dynamic(t):
            encoded = encode_value(t, v)
            head.extend(word(head_size + len(tail))); tail.extend(encoded)
        else: head.extend(encode_value(t, v))
    return bytes(head + tail)

def decode_tuple(params, data):
    if len(data) % 32: raise ValueError('return data must be whole 32-byte words')
    out=[]
    for i,p in enumerate(params):
        t=canonical(p); pos=i*32
        if pos+32 > len(data): raise ValueError('return data is shorter than the ABI output head')
        w=data[pos:pos+32]
        if dynamic(t):
            off=int.from_bytes(w,'big')
            if off%32 or off+32>len(data): raise ValueError('invalid dynamic return offset')
            n=int.from_bytes(data[off:off+32],'big'); raw=data[off+32:off+32+n]
            if len(raw)!=n: raise ValueError('truncated dynamic return value')
            val=raw.decode('utf-8') if t=='string' else '0x'+raw.hex()
        elif t=='address': val='0x'+w[-20:].hex()
        elif t=='bool':
            n=int.from_bytes(w,'big')
            if n not in (0,1): raise ValueError('invalid encoded bool')
            val=bool(n)
        elif t.startswith('bytes') and t!='bytes':
            n=int(t[5:]); val='0x'+w[:n].hex()
        else:
            signed=t.startswith('int'); bits=int(re.search(r'[0-9]+$',t).group(0)) if re.search(r'[0-9]+$',t) else 256
            n=int.from_bytes(w,'big')
            if signed and n & (1 << 255): n-=1 << 256
            if not signed and n >= 1 << bits: raise ValueError(f'invalid high bits for {t}')
            val=n
        out.append({'name':p.get('name') or f'arg{i}', 'type':t, 'value':val})
    return out

def load_function(path, name):
    with open(path, encoding='utf-8') as f: abi=json.load(f)
    matches=[x for x in abi if x.get('type')=='function' and x.get('name')==name]
    if len(matches)!=1: raise ValueError(f'expected exactly one ABI function named {name!r}; found {len(matches)}')
    fn=matches[0]
    sig=fn['name']+'('+','.join(canonical(p) for p in fn.get('inputs',[]))+')'
    return fn,sig

def demo():
    sig='transfer(address,uint256)'; args=['0xd782bdea4ef02a0bd391eb9089470c8080f0a68e',123]
    calldata='0x'+keccak256(sig.encode())[:4].hex()+encode_tuple([{'type':'address'},{'type':'uint256'}],args).hex()
    print(json.dumps({'signature':sig,'selector':'0x'+keccak256(sig.encode())[:4].hex(),'arguments':args,'calldata':calldata},indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--demo',action='store_true',help='encode a built-in offline transfer example')
    sub=ap.add_subparsers(dest='command')
    enc=sub.add_parser('encode'); enc.add_argument('--abi',required=True); enc.add_argument('--function',required=True); enc.add_argument('--args',required=True,help='JSON array of arguments')
    dec=sub.add_parser('decode'); dec.add_argument('--abi',required=True); dec.add_argument('--function',required=True); dec.add_argument('--data',required=True,help='0x-prefixed return bytes')
    a=ap.parse_args()
    try:
        if a.demo: demo(); return 0
        if a.command=='encode':
            fn,sig=load_function(a.abi,a.function); vals=json.loads(a.args)
            if not isinstance(vals,list): raise ValueError('--args must be a JSON array')
            selector=keccak256(sig.encode())[:4]
            payload=encode_tuple(fn.get('inputs',[]),vals)
            print(json.dumps({'signature':sig,'selector':'0x'+selector.hex(),'calldata':'0x'+(selector+payload).hex()},indent=2)); return 0
        if a.command=='decode':
            fn,sig=load_function(a.abi,a.function)
            if not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',a.data): raise ValueError('--data must be even-length 0x hex')
            print(json.dumps({'signature':sig,'outputs':decode_tuple(fn.get('outputs',[]),bytes.fromhex(a.data[2:]))},indent=2)); return 0
        ap.print_help(); return 2
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f'error: {e}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
