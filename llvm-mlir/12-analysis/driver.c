#include <stdint.h>
#include <stdio.h>

typedef struct {
  int32_t *allocated;
  int32_t *aligned;
  int64_t offset;
  int64_t sizes[1];
  int64_t strides[1];
} MemRef1;

extern int32_t _mlir_ciface_pure(int32_t);
extern int32_t _mlir_ciface_load_pair(MemRef1 *);
extern int32_t _mlir_ciface_load_store(MemRef1 *, MemRef1 *, int32_t);
extern int32_t _mlir_ciface_hoist(int64_t, int32_t);
extern int32_t _mlir_ciface_do_not_hoist_div(int64_t, int32_t, int32_t);

static int failures;
static void check(const char *name, int32_t actual, int32_t expected) {
  printf("%s\t%d\t%d\n", name, actual, expected);
  failures += actual != expected;
}

int main(void) {
  _Static_assert(sizeof(void *) == 8, "This harness uses the host 64-bit ABI");
  check("pure-negative", _mlir_ciface_pure(-3), -4);
  check("pure-zero", _mlir_ciface_pure(0), 2);
  check("pure-positive", _mlir_ciface_pure(5), 12);
  int32_t p = 3, q = 5;
  MemRef1 pd = {&p, &p, 0, {1}, {1}};
  MemRef1 qd = {&q, &q, 0, {1}, {1}};
  check("pair", _mlir_ciface_load_pair(&pd), 6);
  check("store-alias", _mlir_ciface_load_store(&pd, &pd, 9), 12);
  check("alias-final-memory", p, 9);
  p = 3;
  check("store-disjoint", _mlir_ciface_load_store(&pd, &qd, 9), 6);
  check("disjoint-final-memory", q, 9);
  check("hoist-zero-trip", _mlir_ciface_hoist(0, 2), 0);
  check("hoist-one-trip", _mlir_ciface_hoist(1, 2), 3);
  check("hoist-four-trips", _mlir_ciface_hoist(4, 2), 12);
  // Zero-trip execution never evaluates the division, so d=0 is defined here.
  check("div-zero-trip-zero-divisor", _mlir_ciface_do_not_hoist_div(0, 12, 0), 0);
  check("div-one-trip", _mlir_ciface_do_not_hoist_div(1, 12, 3), 4);
  check("div-four-trips", _mlir_ciface_do_not_hoist_div(4, 12, 3), 16);
  check("div-negative", _mlir_ciface_do_not_hoist_div(3, -12, 3), -12);
  return failures != 0;
}
