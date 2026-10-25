#include <iostream>

struct AddTag {
  static const char *name() { return "add"; }
};

template <typename T>
void announce(int count) {
  std::cout << T::name() << ": " << count << '\n';
}

int main() {
  announce<AddTag>(2);
  announce<AddTag>(3);
}
