module {
  func.func @window(%a: tensor<?x?xf32>, %row: index, %col: index,
                    %height: index, %width: index) -> tensor<?x?xf32> {
    %r = tensor.extract_slice %a[%row, %col][%height, %width][1, 1]
      : tensor<?x?xf32> to tensor<?x?xf32>
    return %r : tensor<?x?xf32>
  }
}
