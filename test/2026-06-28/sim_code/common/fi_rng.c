#include <stdint.h>
#include <stddef.h>
static uint64_t s=0x123456789abcdef0ULL;
int randombytes(uint8_t *out, size_t n){
  for(size_t i=0;i<n;i++){ s=s*6364136223846793005ULL+1442695040888963407ULL; out[i]=(uint8_t)(s>>33);} return 0; }
