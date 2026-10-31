#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
  float *allocated, *aligned;
  int64_t offset, sizes[2], strides[2];
} F32View2;
typedef struct {
  int32_t *allocated, *aligned;
  int64_t offset, sizes[2], strides[2];
} I32View2;
typedef struct {
  int32_t *allocated, *aligned;
  int64_t offset, sizes[1], strides[1];
} I32View1;

_Static_assert(sizeof(void *) == 8, "This driver targets a 64-bit host ABI");
_Static_assert(sizeof(F32View2) == 56 && offsetof(F32View2, sizes) == 24 &&
               offsetof(F32View2, strides) == 40, "Unexpected descriptor layout");

extern void _mlir_ciface_add_into(F32View2 *, F32View2 *, F32View2 *);
extern int32_t _mlir_ciface_read2d(I32View2 *, int64_t, int64_t);
extern int32_t _mlir_ciface_sum(I32View1 *);
extern void _mlir_ciface_make_copy(F32View2 *result, F32View2 *source);
extern int32_t sum_pair(int32_t *);
extern int32_t choose(bool, int32_t, int32_t);

static int failures;
static void observe(const char *name, double actual, double expected) {
  printf("%s\t%.9g\t%.9g\n", name, actual, expected);
  if (actual != expected) ++failures;
}

static void matrix_case(const char *name, int64_t rows, int64_t cols,
                        bool strided) {
  float a[64], b[64], out[64];
  bool written[64] = {false};
  for (int k = 0; k < 64; ++k) a[k] = b[k] = out[k] = -999;
  F32View2 av = {a, a, strided ? 5 : 0, {rows, cols}, {strided ? 7 : cols, 1}};
  F32View2 bv = {b, b, strided ? 2 : 0, {rows, cols}, {strided ? 8 : cols, strided ? 2 : 1}};
  F32View2 ov = {out, out, strided ? 3 : 0, {rows, cols}, {strided ? 9 : cols, strided ? 2 : 1}};
  for (int64_t i = 0; i < rows; ++i)
    for (int64_t j = 0; j < cols; ++j) {
      float x = (float)(3 * i + j + 1);
      a[av.offset + i * av.strides[0] + j * av.strides[1]] = x;
      b[bv.offset + i * bv.strides[0] + j * bv.strides[1]] = 10 * x;
    }
  _mlir_ciface_add_into(&av, &bv, &ov);
  for (int64_t i = 0; i < rows; ++i)
    for (int64_t j = 0; j < cols; ++j) {
      int64_t position = ov.offset + i * ov.strides[0] + j * ov.strides[1];
      written[position] = true;
      char label[96];
      snprintf(label, sizeof(label), "%s[%lld,%lld]", name, (long long)i, (long long)j);
      observe(label, out[position], 11 * (3 * i + j + 1));
    }
  int changed_outside = 0;
  for (int k = 0; k < 64; ++k)
    if (!written[k] && out[k] != -999) ++changed_outside;
  char label[96];
  snprintf(label, sizeof(label), "%s.outside-writes", name);
  observe(label, changed_outside, 0);
}

int main(void) {
  matrix_case("contiguous", 2, 3, false);
  matrix_case("strided", 2, 3, true);
  matrix_case("single", 1, 1, true);
  matrix_case("empty-rows", 0, 3, true);
  matrix_case("empty-columns", 2, 0, true);
  int32_t data[16];
  for (int k = 0; k < 16; ++k) data[k] = k;
  I32View2 window = {data, data, 5, {2, 2}, {4, 1}};
  observe("read-window", _mlir_ciface_read2d(&window, 1, 1), 10);
  // The aligned pointer and allocation pointer need not be identical.
  I32View2 shifted = {data, data + 4, 1, {2, 2}, {4, 1}};
  observe("read-aligned-base", _mlir_ciface_read2d(&shifted, 1, 1), 10);
  int32_t numbers[] = {3, -2, 5, 7};
  I32View1 vector = {numbers, numbers, 0, {4}, {1}};
  observe("loop-sum", _mlir_ciface_sum(&vector), 13);
  observe("pointer-pair", sum_pair(numbers), 1);
  observe("choose-true", choose(true, 8, 13), 8);
  observe("choose-false", choose(false, 8, 13), 13);
  float source[] = {1, 2, 3, 4, 5, 6};
  F32View2 input = {source, source, 0, {2, 3}, {3, 1}}, result;
  _mlir_ciface_make_copy(&result, &input);
  observe("returned-rows", result.sizes[0], 2);
  observe("returned-columns", result.sizes[1], 3);
  for (int i = 0; i < 2; ++i)
    for (int j = 0; j < 3; ++j) {
      char label[64];
      snprintf(label, sizeof(label), "returned-copy[%d,%d]", i, j);
      observe(label, result.aligned[result.offset + i * result.strides[0] + j * result.strides[1]], source[3*i+j]);
    }
  // make_copy uses memref.alloc + memref.copy, so its result is independently writable.
  result.aligned[result.offset] = 99;
  observe("input-after-copy-write", source[0], 1);
  free(result.allocated);
  return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
