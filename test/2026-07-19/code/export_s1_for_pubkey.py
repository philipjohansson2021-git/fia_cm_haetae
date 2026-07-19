# SPDX-License-Identifier: MIT
# export_s1_for_pubkey.py — recovered s1 (NTT domain) -> coeff-domain file for
# the public-only verifier verify_s1_pubkey (closes review item W2).
#
# The T1 2-trace recovery returns s1 in the NTT domain (sign-ambiguous). This
# writes it as 768 ternary coefficients {-1,0,1} (row-major m*256+k), which
# verify_s1_pubkey re-NTTs and checks against the PUBLIC key (both signs tried).
#
# In the notebook, right after a successful recovery:
#   from haetae_recover_t1 import recover_s1_from_two_traces
#   r = recover_s1_from_two_traces(z_clean, z_fault, c)     # r['s1ntt'] = [3][256]
#   from export_s1_for_pubkey import write_coeff_file
#   write_coeff_file(r['s1ntt'], 'recovered_s1.txt')
# Then (WSL):  ./verify_s1_pubkey recovered_s1.txt   ->  PASS (matches public key)
from haetae_recover_t1 import intt, _center

_MONT = 14321   # {-1,0,1} appear as {-14321,0,14321} in the tomont coeff domain

def _to_coeff(block):
    v = [_center(x) for x in intt(list(block))]
    return [1 if x > _MONT // 2 else (-1 if x < -_MONT // 2 else 0) for x in v]

def write_coeff_file(s1ntt, path):
    """s1ntt: list of 3 blocks x 256 (NTT domain) from recover_s1_from_two_traces."""
    assert len(s1ntt) == 3 and all(len(b) == 256 for b in s1ntt), "expect [3][256]"
    with open(path, 'w') as f:
        for b in range(3):
            for x in _to_coeff(s1ntt[b]):
                f.write('%d\n' % x)
    print('wrote', path, '(768 ternary coeffs) -> run: ./verify_s1_pubkey', path)
