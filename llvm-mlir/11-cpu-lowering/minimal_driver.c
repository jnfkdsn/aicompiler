#include <stdint.h>
#include <stdio.h>

typedef struct {
  float *allocated, *aligned;
  int64_t offset, sizes[2], strides[2];
} F32View2;

extern void _mlir_ciface_add_into(F32View2 *, F32View2 *, F32View2 *);

int main(void) {
  float a[6] = {1, 2, 3, 4, 5, 6};
  float b[6] = {10, 20, 30, 40, 50, 60};
  float out[6] = {0};
  F32View2 av = {a, a, 0, {2, 3}, {3, 1}};
  F32View2 bv = {b, b, 0, {2, 3}, {3, 1}};
  F32View2 ov = {out, out, 0, {2, 3}, {3, 1}};
  _mlir_ciface_add_into(&av, &bv, &ov);
  int failed = 0;
  for (int k = 0; k < 6; ++k) {
    printf("%.0f\n", out[k]);
    if (out[k] != a[k] + b[k]) failed = 1;
  }
  return failed;
}
